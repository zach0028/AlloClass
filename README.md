# AlloClass c'est quoi ?

AlloClass est un moteur de classification de tickets clients par LLM, contenant entre autre une boucle d'amélioration itérative et une interface conversationnelle.

<img width="1712" height="992" alt="Capture d'écran 2026-02-18 à 22 48 14" src="https://github.com/user-attachments/assets/03de3b49-5fd8-465f-a997-a74a4e405941" />

## Démarrage en 2 minutes :

Prérequis : Docker & une clé API OpenAI

```bash
git clone git@github.com:zach0028/AlloClass.git
cd AlloClass
cp .env.exemple .env        # puis coller votre clé OPENAI_API_KEY
docker compose up
```

Frontend : http://localhost:3000 | API : http://localhost:8000

## En savoir un peu plus sur le projet :

AlloClass permet de classifier automatiquement des tickets clients sur plusieurs axes simultanément (type, urgence, action attendue...). Un agent conversationnel guide l'utilisateur, et une boucle d'évaluation itérative (générateur-juge) affine les résultats en temps réel jusqu'à atteindre un seuil de confiance cible sur les tickets générés.

## La Stack :

| Couche | Techno |
|---|---|
| Frontend | Next.js, React, Tailwind, shadcn/ui |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Base de données | PostgreSQL + pgvector |
| LLM | OpenAI (gpt-5.1, gpt-5-nano, gpt-4o) |
| Infra | Docker Compose |

## L'Architecture :

```
AlloClass/
  backend/
    app/
      api/            Routes FastAPI
      models/         Modèles SQLAlchemy
      services/       Logique métier (classification, évaluation, agent)
      prompts/        Templates de prompts LLM
      schemas/        Schémas Pydantic
  frontend/
    src/
      app/            Pages Next.js
      components/     Composants React
      hooks/          Hooks custom (SSE, chat, config)
      lib/            Utilitaires (API client)
      types/          Types TypeScript
  docker-compose.yml
```
