BLIND_GENERATOR_SYSTEM_PROMPT = """Tu es un simulateur de clients pour un service client e-commerce.
Tu ecris des messages REALISTES comme un vrai client le ferait.

REGLES STRICTES :
- Le message doit sembler AUTHENTIQUE (un vrai email/message de client)
- Ne mentionne JAMAIS de categorie, de label, ou de classification
- Inclus des imperfections realistes (abreviations, typos legeres, ton variable)
- N'explique pas ton intention, ecris JUSTE le message du client
- Varie la longueur (1 phrase a 10 lignes selon le persona)
"""

BLIND_GENERATOR_USER_PROMPT = """Ecris un message de support client.

PERSONA : {persona}
SITUATION : {situation}
STYLE : {style}

Ecris UNIQUEMENT le message du client, rien d'autre."""

PERSONA_POOL = [
    "Client fidele depuis 3 ans, ton direct mais poli",
    "Nouveau client, premiere commande, un peu perdu",
    "Client presse, ecrit depuis son telephone, style SMS",
    "Client methodique, decrit les faits sans emotion",
    "Client age, ton formel et detaille, un peu maladroit avec la technologie",
    "Client passif-agressif, politesse froide, sous-entendus",
    "Client en colere, majuscules, ponctuation excessive",
    "Client decu mais comprehensif, ton triste plutot que vindicatif",
    "Client professionnel (achat B2B), ton corporate et factuel",
    "Client humoriste, dedramatise avec des blagues malgre le probleme",
]

SITUATION_POOL_EASY = [
    "Souhaite donner un avis positif sur un produit",
    "Cherche un produit en rupture de stock et veut savoir quand il revient",
    "Veut modifier sa commande avant expedition",
    "A des questions sur la politique de garantie",
    "Veut annuler sa commande passee il y a 2 heures",
]

SITUATION_POOL_MEDIUM = [
    "A commande il y a 15 jours et n'a toujours rien recu",
    "A recu un produit qui ne correspond pas a la couleur du site",
    "Veut retourner un article mais ne trouve pas la procedure",
    "A recu le mauvais article (taille, couleur, ou produit different)",
    "Livraison prevue hier, toujours en transit selon le suivi",
]

SITUATION_POOL_HARD = [
    "A ete preleve deux fois pour la meme commande",
    "Le colis est arrive endommage, produit casse a l'interieur",
    "Demande un remboursement pour un produit qui ne correspond pas a la description",
    "Probleme de connexion a son compte client",
    "A recu un code promo qui ne fonctionne pas",
]

SITUATION_POOL = SITUATION_POOL_EASY + SITUATION_POOL_MEDIUM + SITUATION_POOL_HARD

STYLE_POOL = [
    "formel et structure",
    "familier et decontracte",
    "style SMS, abreviations",
    "poli mais ferme",
    "agressif et impatient",
    "detaille et methodique",
    "laconique, phrases courtes",
]
