AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "classify_ticket",
            "description": (
                "Classifie un ticket texte sur tous les axes de la config active. "
                "Utilise cet outil quand l'utilisateur colle un texte a classifier "
                "ou demande explicitement une classification."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Le texte du ticket a classifier",
                    }
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_tickets",
            "description": (
                "Recherche des tickets classifies par criteres (categorie, confiance, texte libre). "
                "Utilise cet outil quand l'utilisateur demande de chercher, lister, "
                "filtrer ou compter des tickets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La requete en langage naturel de l'utilisateur",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "correct_classification",
            "description": (
                "Corrige une classification en enregistrant un feedback. "
                "Utilise cet outil quand l'utilisateur dit 'non c'est X', "
                "'plutot Y', 'corrige vers Z', ou conteste un resultat."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "feedback_message": {
                        "type": "string",
                        "description": "Le message de correction de l'utilisateur en langage naturel",
                    }
                },
                "required": ["feedback_message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_review_queue",
            "description": (
                "Recupere les prochains tickets a revoir dans la file de priorite "
                "(tickets ambigus, faible confiance). Utilise cet outil quand l'utilisateur "
                "dit 'ticket suivant', 'prochain a revoir', 'montre les ambigus'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Nombre de tickets a recuperer (defaut: 1)",
                        "default": 1,
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stats",
            "description": (
                "Recupere les statistiques et KPIs de classification : total, "
                "confiance moyenne, taux challenger, feedbacks, taux de correction. "
                "Utilise cet outil quand l'utilisateur demande des stats, performances, "
                "ou comment ca progresse."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_improvement_suggestions",
            "description": (
                "Analyse les patterns d'erreur et propose des suggestions "
                "d'amelioration du systeme de classification. "
                "Utilise cet outil quand l'utilisateur demande comment ameliorer "
                "le systeme ou veut des recommandations."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_config_info",
            "description": (
                "Recupere les informations sur la configuration active : "
                "nom, description, axes de classification et categories disponibles. "
                "Utilise cet outil quand l'utilisateur demande des infos sur la config, "
                "les axes, les categories, ou comment le systeme est configure."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "classify_batch",
            "description": (
                "Classifie plusieurs tickets en une seule operation. "
                "Utilise cet outil quand l'utilisateur colle plusieurs textes "
                "ou demande de classifier un lot de tickets d'un coup."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "texts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Liste des textes de tickets a classifier",
                    }
                },
                "required": ["texts"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learned_rules",
            "description": (
                "Recupere les regles apprises par le systeme a partir des feedbacks utilisateur. "
                "Utilise cet outil quand l'utilisateur demande ce que le systeme a appris, "
                "quelles regles sont actives, ou comment les feedbacks ont influence le classifieur."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_version_history",
            "description": (
                "Recupere l'historique des versions du systeme de prompts : "
                "quand et pourquoi les prompts ont change. "
                "Utilise cet outil quand l'utilisateur demande l'historique, "
                "les changements recents, ou l'evolution du systeme."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]
