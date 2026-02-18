import json
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.openai_client import client as openai_client
from app.models.chat_message import ChatMessage
from app.models.config import Config

from .history import load_conversation_history
from .system_prompt import build_system_prompt
from .tool_executor import execute_tool
from .tools import AGENT_TOOLS

TOOL_STEP_LABELS = {
    "classify_ticket": "Classification en cours...",
    "classify_batch": "Classification du lot en cours...",
    "search_tickets": "Recherche en cours...",
    "correct_classification": "Enregistrement de la correction...",
    "get_review_queue": "Chargement de la file de revision...",
    "get_stats": "Calcul des statistiques...",
    "get_improvement_suggestions": "Analyse des patterns d'erreur...",
    "get_config_info": "Chargement de la configuration...",
    "get_learned_rules": "Chargement des regles apprises...",
    "get_version_history": "Chargement de l'historique...",
}


def summarize_tool_result(tool_name: str, result: dict) -> str:
    if "error" in result:
        return result["error"]

    match tool_name:
        case "classify_ticket":
            conf = result.get("overall_confidence", 0)
            axes = result.get("results", [])
            labels = ", ".join(r.get("category_name", "?") for r in axes[:3])
            return f"Confiance {round(conf * 100)}% — {labels}"
        case "classify_batch":
            count = result.get("count", 0)
            return f"{count} ticket(s) classifie(s)"
        case "search_tickets":
            total = result.get("total_count", len(result.get("results", [])))
            return f"{total} ticket(s) trouve(s)"
        case "correct_classification":
            return result.get("message", "Correction enregistree")
        case "get_review_queue":
            count = result.get("count", 0)
            return f"{count} ticket(s) a revoir" if count else "File vide"
        case "get_stats":
            total = result.get("total_classifications", 0)
            conf = result.get("average_confidence", 0)
            return f"{total} classifications, confiance moyenne {round(conf * 100)}%"
        case "get_improvement_suggestions":
            suggestions = result.get("suggestions", [])
            return f"{len(suggestions)} suggestion(s) generee(s)"
        case "get_config_info":
            name = result.get("config_name", "?")
            axes = result.get("axes_count", 0)
            return f"Config \"{name}\" — {axes} axe(s)"
        case "get_learned_rules":
            count = result.get("count", 0)
            return f"{count} regle(s) active(s)" if count else "Aucune regle"
        case "get_version_history":
            count = result.get("count", 0)
            return f"{count} version(s)" if count else "Aucun historique"
        case _:
            return "Termine"

MAX_TOOL_ITERATIONS = 5


async def run_agent(
    user_message: str,
    config: Config,
    db: AsyncSession,
    conversation_id: "uuid.UUID | None" = None,
) -> AsyncGenerator[dict, None]:
    user_msg = ChatMessage(
        config_id=config.id,
        conversation_id=conversation_id,
        role="user",
        content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    system_prompt = build_system_prompt(config)
    history = await load_conversation_history(
        config.id, db, limit=20, conversation_id=conversation_id
    )

    messages = [
        {"role": "system", "content": system_prompt},
        *history,
    ]

    final_text = ""
    tool_results_for_frontend: list[dict] = []
    learning_card_data: dict | None = None

    try:
        for _ in range(MAX_TOOL_ITERATIONS):
            stream = await openai_client.chat.completions.create(
                model=settings.agent_model,
                messages=messages,
                tools=AGENT_TOOLS,
                reasoning_effort="medium",
                stream=True,
            )

            content_parts: list[str] = []
            tool_calls_acc: dict[int, dict] = {}

            async for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta

                if delta.content:
                    content_parts.append(delta.content)
                    yield {"type": "delta", "data": {"content": delta.content}}

                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {
                                "id": "",
                                "name": "",
                                "arguments": "",
                            }
                        if tc_delta.id:
                            tool_calls_acc[idx]["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tool_calls_acc[idx]["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                tool_calls_acc[idx]["arguments"] += tc_delta.function.arguments

            content_text = "".join(content_parts)

            if not tool_calls_acc:
                final_text = content_text
                yield {"type": "done", "data": {}}
                break

            if content_text:
                yield {
                    "type": "thinking",
                    "data": {"message": content_text},
                }

            messages.append({
                "role": "assistant",
                "content": content_text or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"],
                        },
                    }
                    for _, tc in sorted(tool_calls_acc.items())
                ],
            })

            for tc_data in (tool_calls_acc[i] for i in sorted(tool_calls_acc)):
                tool_name = tc_data["name"]
                tool_args = json.loads(tc_data["arguments"])

                yield {
                    "type": "step",
                    "data": {
                        "step": "tool_call",
                        "tool": tool_name,
                        "message": TOOL_STEP_LABELS.get(
                            tool_name, f"Execution de {tool_name}..."
                        ),
                    },
                }

                try:
                    result = await execute_tool(tool_name, tool_args, config, db)
                except Exception as tool_exc:
                    await db.rollback()
                    result = {"error": f"Echec de {tool_name}: {tool_exc}"}

                yield {
                    "type": "step_result",
                    "data": {
                        "tool": tool_name,
                        "summary": summarize_tool_result(tool_name, result),
                    },
                }

                if tool_name == "classify_ticket" and "results" in result:
                    yield {
                        "type": "tool_data",
                        "data": {"tool": tool_name, "result": result},
                    }
                    tool_results_for_frontend.append(result)

                if tool_name == "correct_classification" and "learning_card" in result:
                    learning_card_data = result["learning_card"]
                    yield {
                        "type": "learning",
                        "data": learning_card_data,
                    }

                if tool_name == "classify_batch" and "results" in result:
                    for item in result["results"]:
                        yield {
                            "type": "tool_data",
                            "data": {"tool": "classify_ticket", "result": item},
                        }
                        tool_results_for_frontend.append(item)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_data["id"],
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

    except Exception as exc:
        final_text = f"Erreur : {exc}"
        yield {"type": "error", "data": {"message": final_text}}

    finally:
        metadata = None
        if tool_results_for_frontend or learning_card_data:
            metadata = {}
            if tool_results_for_frontend:
                metadata["tool_results"] = tool_results_for_frontend
            if learning_card_data:
                metadata["learning_card"] = learning_card_data

        assistant_msg = ChatMessage(
            config_id=config.id,
            conversation_id=conversation_id,
            role="assistant",
            content=final_text,
            metadata_=metadata,
        )
        db.add(assistant_msg)

        if conversation_id:
            from datetime import datetime, timezone
            from app.models.conversation import Conversation

            conv = await db.get(Conversation, conversation_id)
            if conv:
                conv.updated_at = datetime.now(timezone.utc)
                if not conv.title:
                    conv.title = user_message[:80]

        await db.commit()
