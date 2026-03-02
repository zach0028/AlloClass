import json
import uuid
from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import agent_llm
from app.models.chat_message import ChatMessage
from app.models.config import Config

from .history import load_conversation_history
from .system_prompt import build_system_prompt
from .tools_def import create_agent_tools

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
        return f"Echec : {result['error']}"

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

    tools = create_agent_tools(config, db)
    react_agent = create_react_agent(
        model=agent_llm,
        tools=tools,
        prompt=system_prompt,
    )

    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    final_text = ""
    tool_results_for_frontend: list[dict] = []
    learning_card_data: dict | None = None
    has_emitted_deltas = False
    tool_depth = 0

    try:
        async for event in react_agent.astream_events(
            {"messages": messages},
            version="v2",
            config={"recursion_limit": MAX_TOOL_ITERATIONS * 2 + 1},
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content and not chunk.tool_call_chunks and tool_depth == 0:
                    has_emitted_deltas = True
                    final_text += chunk.content
                    yield {"type": "delta", "data": {"content": chunk.content}}

            elif kind == "on_tool_start":
                tool_depth += 1
                tool_name = event["name"]

                if has_emitted_deltas:
                    yield {"type": "thinking", "data": {"message": final_text}}
                    final_text = ""
                    has_emitted_deltas = False

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

            elif kind == "on_tool_end":
                tool_depth -= 1
                tool_name = event["name"]
                raw_output = event["data"]["output"]

                if hasattr(raw_output, "content"):
                    raw_output = raw_output.content

                if isinstance(raw_output, dict):
                    result = raw_output
                elif isinstance(raw_output, str):
                    try:
                        result = json.loads(raw_output)
                    except (json.JSONDecodeError, TypeError):
                        result = {"raw": raw_output}
                else:
                    result = {"raw": str(raw_output)}

                if not isinstance(result, dict):
                    result = {"raw": str(result)}

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
                    yield {"type": "learning", "data": learning_card_data}

                if tool_name == "classify_batch" and "results" in result:
                    for item in result["results"]:
                        yield {
                            "type": "tool_data",
                            "data": {"tool": "classify_ticket", "result": item},
                        }
                        tool_results_for_frontend.append(item)

        yield {"type": "done", "data": {}}

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
