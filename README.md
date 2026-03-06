# Ad Agency Swarm

A flat multi-agent system that generates campaign briefs. No coordinator. Five specialist agents run in parallel, build on each other's work across rounds, and converge on a strategy.

## Architecture

```
POST /campaign  →  GET /stream/{id}  →  GET /result/{id}
                        │
              asyncio.gather (all agents, each round)
                        │
         ┌──────────────┼──────────────┐
   brand_strategist  audience_researcher  competitive_analyst
         │              media_planner       copywriter
         └──────────────┼──────────────┘
                        │
                  Memorystore (Redis)
                  (shared campaign state)
                        │
              Live data: Reddit · Meta Ad Library · Google Trends
```

## Stack

| Layer | Service |
|---|---|
| LLM | Vertex AI — Gemini 2.0 Flash |
| Backend | FastAPI + SSE |
| Shared state | Redis (Memorystore on GCP, local Redis for dev) |
| Hosting | Google Cloud Run |

## Local Setup

**Prerequisites:** Python 3.12+, Redis running on localhost:6379

```bash
cd backend
cp .env.example .env        # fill in your keys
pip install -r requirements.txt
python -m textblob.download_corpora
uvicorn main:app --reload
```

API available at `http://localhost:8000`

## API

### Start a campaign
```bash
curl -X POST http://localhost:8000/campaign \
  -H "Content-Type: application/json" \
  -d '{
    "product": "Notion",
    "description": "All-in-one productivity workspace",
    "budget": 15000,
    "goal": "User acquisition",
    "competitor": "Obsidian"
  }'
# → { "campaign_id": "abc-123" }
```

### Stream agent activity
```bash
curl -N http://localhost:8000/stream/abc-123
```

### Get final brief
```bash
curl http://localhost:8000/result/abc-123
```

## Environment Variables

See [backend/.env.example](backend/.env.example) for all required variables.

- `GCP_PROJECT_ID` — your GCP project
- `REDIS_HOST` — Memorystore IP (or `localhost` for dev)
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` — from reddit.com/prefs/apps
- `META_ACCESS_TOKEN` — from Meta Ad Library API

Reddit and Meta tokens are optional — the system falls back gracefully if they are missing.

## Deploy to Cloud Run

```bash
gcloud run deploy swarm-backend \
  --source ./backend \
  --region us-central1 \
  --set-env-vars GCP_PROJECT_ID=your-project,REDIS_HOST=your-memorystore-ip \
  --vpc-connector swarm-connector \
  --allow-unauthenticated
```
