TICKET_QUERY_PROMPT = """Tu es un traducteur de requetes en langage naturel vers des filtres structures.

L'utilisateur cherche des tickets dans une base de donnees de classification.

AXES ET CATEGORIES DISPONIBLES :
{axes_and_categories}

FILTRES SUPPORTES :
- axes : filtre par axe et categorie (ex: Type=Reclamation)
- date_range : "today", "last_week", "last_month", "all", ou format "YYYY-MM-DD:YYYY-MM-DD"
- confidence_min / confidence_max : filtre par score de confiance (0.0 a 1.0)
- was_challenged : true/false
- has_feedback : true/false
- text_search : recherche dans le contenu du ticket

Retourne un JSON strict :
{{
    "filters": {{
        "axes": {{"Type": ["Reclamation"], "Urgence": ["Haute", "Critique"]}},
        "date_range": "last_week",
        "confidence_min": null,
        "confidence_max": null,
        "was_challenged": null,
        "has_feedback": null,
        "text_search": null
    }},
    "sort": "created_at_desc",
    "limit": 20,
    "aggregation": null
}}

Si l'utilisateur demande un COMPTE ("combien"), set aggregation = "count".
Si l'utilisateur demande une LISTE, set aggregation = null.

REQUETE DE L'UTILISATEUR :
\"\"\"{message}\"\"\"

FILTRE JSON :"""

TICKET_QUERY_SEMANTIC_PROMPT = """La requete de l'utilisateur ne correspond pas a un filtre structure.
Elle semble demander une recherche semantique (par similarite de contenu).

Extrais le CONCEPT cle a rechercher par similarite vectorielle.

REQUETE : \"\"\"{message}\"\"\"

Retourne un JSON strict :
{{
    "search_text": "le concept a chercher par embedding",
    "limit": 20
}}"""
