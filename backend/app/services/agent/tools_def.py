from functools import wraps

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import Config


def create_agent_tools(config: Config, db: AsyncSession) -> list:

    def with_rollback(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                await db.rollback()
                return {"error": str(exc)}
        return wrapper

    @tool
    @with_rollback
    async def classify_ticket(text: str) -> dict:
        """Classifie un ticket texte sur tous les axes de la config active.
        Utilise cet outil quand l'utilisateur colle un texte a classifier
        ou demande explicitement une classification."""
        from app.services.classification.classification_pipeline import (
            classify_ticket as do_classify,
        )
        classification = await do_classify(text, config, db)
        return {
            "classification_id": str(classification.id),
            "input_text": text[:100],
            "results": classification.results,
            "overall_confidence": classification.overall_confidence,
            "was_challenged": classification.was_challenged,
            "challenger_response": classification.challenger_response,
            "processing_time_ms": classification.processing_time_ms,
        }

    @tool
    @with_rollback
    async def search_tickets(query: str) -> dict:
        """Recherche des tickets classifies par criteres (categorie, confiance, texte libre).
        Utilise cet outil quand l'utilisateur demande de chercher, lister,
        filtrer ou compter des tickets."""
        from app.services.analytics.ticket_query import (
            query_tickets_natural_language,
            query_tickets_semantic,
        )
        result = await query_tickets_natural_language(query, config.id, db)
        if result.get("total_count", 0) == 0 and not result.get("results"):
            result = await query_tickets_semantic(query, config.id, db)
        return result

    @tool
    @with_rollback
    async def correct_classification(feedback_message: str) -> dict:
        """Corrige une classification en enregistrant un feedback.
        Utilise cet outil quand l'utilisateur dit 'non c'est X',
        'plutot Y', 'corrige vers Z', ou conteste un resultat."""
        from app.services.learning.feedback_learning import process_natural_feedback
        return await process_natural_feedback(feedback_message, config.id, db)

    @tool
    @with_rollback
    async def get_review_queue(count: int = 1) -> dict:
        """Recupere les prochains tickets a revoir dans la file de priorite
        (tickets ambigus, faible confiance). Utilise cet outil quand l'utilisateur
        dit 'ticket suivant', 'prochain a revoir', 'montre les ambigus'."""
        from app.services.learning.feedback_learning import get_priority_queue
        queue = await get_priority_queue(config.id, db, limit=count)
        if queue:
            return {"tickets": queue, "count": len(queue)}
        return {"tickets": [], "count": 0, "message": "Aucun ticket en attente de revision."}

    @tool
    @with_rollback
    async def get_stats() -> dict:
        """Recupere les statistiques et KPIs de classification : total,
        confiance moyenne, taux challenger, feedbacks, taux de correction.
        Utilise cet outil quand l'utilisateur demande des stats, performances,
        ou comment ca progresse."""
        from app.services.analytics.analytics_computation import compute_kpis
        return await compute_kpis(config.id, db)

    @tool
    @with_rollback
    async def get_improvement_suggestions() -> dict:
        """Analyse les patterns d'erreur et propose des suggestions
        d'amelioration du systeme de classification.
        Utilise cet outil quand l'utilisateur demande comment ameliorer
        le systeme ou veut des recommandations."""
        from app.services.learning.error_pattern_detector import generate_suggestions
        raw_suggestions = await generate_suggestions(config.id, db)
        return {"suggestions": raw_suggestions}

    @tool
    @with_rollback
    async def get_config_info() -> dict:
        """Recupere les informations sur la configuration active :
        nom, description, axes de classification et categories disponibles.
        Utilise cet outil quand l'utilisateur demande des infos sur la config,
        les axes, les categories, ou comment le systeme est configure."""
        axes_info = []
        for axis in sorted(config.axes, key=lambda a: a.position):
            categories = [
                {"name": cat.name, "description": cat.description}
                for cat in sorted(axis.categories, key=lambda c: c.position)
            ]
            axes_info.append({
                "name": axis.name,
                "description": axis.description,
                "categories": categories,
            })
        return {
            "config_name": config.name,
            "config_description": config.description,
            "axes_count": len(axes_info),
            "axes": axes_info,
        }

    @tool
    @with_rollback
    async def classify_batch(texts: list[str]) -> dict:
        """Classifie plusieurs tickets en une seule operation.
        Utilise cet outil quand l'utilisateur colle plusieurs textes
        ou demande de classifier un lot de tickets d'un coup."""
        from app.services.classification.classification_pipeline import (
            classify_batch as do_classify_batch,
        )
        results = await do_classify_batch(texts, config, db)
        return {
            "count": len(results),
            "results": [
                {
                    "classification_id": str(r.id),
                    "input_text": r.input_text[:100],
                    "results": r.results,
                    "overall_confidence": r.overall_confidence,
                }
                for r in results
            ],
        }

    @tool
    @with_rollback
    async def get_learned_rules() -> dict:
        """Recupere les regles apprises par le systeme a partir des feedbacks utilisateur.
        Utilise cet outil quand l'utilisateur demande ce que le systeme a appris,
        quelles regles sont actives, ou comment les feedbacks ont influence le classifieur."""
        from sqlalchemy.orm import selectinload
        from app.models.learned_rule import LearnedRule

        result = await db.execute(
            select(LearnedRule)
            .options(selectinload(LearnedRule.axis))
            .where(
                LearnedRule.config_id == config.id,
                LearnedRule.active == True,
                LearnedRule.validated_by_user == True,
            )
            .order_by(LearnedRule.created_at)
        )
        rules = list(result.scalars().all())

        if not rules:
            return {"rules": [], "message": "Aucune regle apprise pour le moment."}
        return {
            "count": len(rules),
            "rules": [
                {
                    "axis": r.axis.name if r.axis else "general",
                    "rule_text": r.rule_text,
                    "source_feedback_count": r.source_feedback_count,
                    "validated_by_user": r.validated_by_user,
                }
                for r in rules
            ],
        }

    @tool
    @with_rollback
    async def get_version_history() -> dict:
        """Recupere l'historique des versions du systeme de prompts :
        quand et pourquoi les prompts ont change.
        Utilise cet outil quand l'utilisateur demande l'historique,
        les changements recents, ou l'evolution du systeme."""
        from app.services.config.prompt_versioning import get_version_history as do_get_history
        versions = await do_get_history(config.id, db)
        if not versions:
            return {"versions": [], "message": "Aucun historique de version."}
        return {
            "count": len(versions),
            "versions": [
                {
                    "version": v.version_number,
                    "created_at": str(v.created_at),
                    "change_type": v.change_type,
                    "change_description": v.change_description,
                    "accuracy_at_creation": v.accuracy_at_creation,
                }
                for v in versions
            ],
        }

    return [
        classify_ticket,
        search_tickets,
        correct_classification,
        get_review_queue,
        get_stats,
        get_improvement_suggestions,
        get_config_info,
        classify_batch,
        get_learned_rules,
        get_version_history,
    ]
