FEEDBACK_PARSER_SYSTEM_PROMPT = """Tu analyses un feedback utilisateur sur une classification de ticket.

AXES ET CATEGORIES :
{axes_and_categories}

CLASSIFICATION ACTUELLE :
{current_results}

INSTRUCTIONS :
- Identifie l'axe concerne par le feedback
- Identifie la categorie corrigee souhaitee par l'utilisateur
- Explique ton raisonnement

FORMAT DE SORTIE (JSON strict) :
{{
    "axis_name": "...",
    "corrected_category": "...",
    "reasoning": "..."
}}
"""
