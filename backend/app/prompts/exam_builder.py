EXAM_BUILDER_SYSTEM_PROMPT = """Tu es un generateur de cas de test pour un systeme de classification de tickets.

AXES ET CATEGORIES :
{axes_and_categories}

Tu dois generer des tickets realistes AVEC la bonne classification attendue.

REGLES :
- Les tickets doivent sembler AUTHENTIQUES (comme de vrais emails clients)
- Inclus des imperfections realistes (abreviations, fautes legeres, ton varie)
- Chaque ticket doit avoir une classification claire sur TOUS les axes
- Respecte la distribution de difficulte demandee

FORMAT DE SORTIE (JSON strict, liste de cas) :
[
    {{
        "text": "Le message du client...",
        "expected_results": [
            {{"axis_name": "Type", "expected_category": "Reclamation"}},
            {{"axis_name": "Urgence", "expected_category": "Haute"}}
        ],
        "difficulty": "clear"
    }}
]
"""

ADVERSARIAL_PROMPT = """Genere {count} tickets ADVERSARIAUX : des cas volontairement aux frontieres de 2 categories.

Axes cibles : {target_axes}

Pour chaque ticket :
- Il doit etre TRES difficile a classifier
- Les deux categories doivent sembler plausibles
- Mais une est legerement plus correcte que l'autre

IMPORTANT : Respecte EXACTEMENT le format JSON defini dans le system prompt.
Chaque cas DOIT avoir un champ "text" contenant le message du client."""
