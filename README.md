# Vespyr — Pheromone Intelligence Swarm

> **An AI swarm just read your market, found your competitor's exposed flank, and wrote your campaign brief. Before your team finished the intro slide.**

A multi-agent system that hunts live market signals and evolves campaign strategy through **stigmergy** — the same coordination mechanism used by ant colonies. No orchestrator. No prompt chain. Agents leave typed, intensity-weighted traces on a shared Firestore blackboard. Strong signals attract more agents. Weak signals decay. The swarm converges without anyone telling it to.

---

## Architecture

```
POST /campaign
      │
      ▼
Firestore: campaigns/{id}/scents/   ← pheromone blackboard
      │
      ├── scavenger_market   BigQuery Trends + Serper  → Price-War / Viral-Heat / Market-Void
      ├── scavenger_social   Serper + Google NLP        → Sentiment-Bleed / Feature-Gap
      ├── forager            Serper                     → Market-Void
      ├── skeptic  ¹         Serper (counter-evidence)  → Doubt
      └── strategist  ¹      Serper                     → Strategy
            │
            └── Firestore on_snapshot (real-time pub/sub, zero polling)
                  each agent wakes only on typed scents above its intensity threshold
                  up to 5 stigmergic rounds · REACTION_TIMEOUT 60s · SAFETY_TIMEOUT 360s
                      │
                  mutator          blackboard only  → Mutation (5 hooks)
                  audience_sniper  trail-derived    → Audience (3 micro-segments)
                      │
                  GET /stream/{id}  →  SSE real-time UI
```

**Stigmergic execution**: Each foraging agent loops — run → commit → wait for peer scent → react. Repeats until `done: true`, `REACTION_TIMEOUT` (60s no stimulus), or `MAX_AGENT_ROUNDS = 5`. `SAFETY_TIMEOUT = 360s` bounds the full run.

**Intensity & decay**: On every commit — all scents ×0.85 (decay), cited scents +0.15 (reinforcement, capped at 1.0). Signals multiple agents build on stay strong. Signals nobody cites fade.

**Typed wake conditions**: Agents wake only on scent types they care about, above a minimum intensity threshold. A `Price-War` at 0.4 does not wake `ScavengerSocial`. Only real signal triggers reaction.

**Observation sort**: Prior observations sorted by `intensity × 0.6 + (1/round) × 0.4` — early high-quality signals stay in context as the swarm runs.

¹ `react_only` — skips independent first pass, only fires after real peer signal exists on the blackboard.

---

## Scent Types

| Type | Agent | Signal |
|---|---|---|
| `Prompt` | user | Initial campaign target — the first pheromone |
| `Followup` | user | Directed follow-up — re-enters Strategist + Mutator on existing trail |
| `Performance` | user | Real campaign metrics — intensity 0.92, highest natural authority |
| `Price-War` | scavenger_market | Competitor pricing moves |
| `Viral-Heat` | scavenger_market | Keyword spikes, trending moments |
| `Market-Void` | scavenger_market, forager | Uncontested segments, competitor pullback |
| `Sentiment-Bleed` | scavenger_social | High-volume negative sentiment toward a named competitor weakness |
| `Feature-Gap` | scavenger_social | Users demanding something no competitor provides |
| `Doubt` | skeptic | Counter-evidence against the highest-intensity claim — includes `challenge_strength` and `verdict` |
| `Strategy` | strategist | Campaign hook grounded in the strongest live signals |
| `Mutation` | mutator | 5 evolved campaign-ready hook variations (bold / empathetic / provocative / data-driven / cultural) |
| `Audience` | audience_sniper | 3 DSP-ready micro-segments with trigger events and targeting layers |

---

## Agents

| Agent | Data | Scent | Role |
|---|---|---|---|
| scavenger_market | BigQuery `google_trends.top_rising_terms` + Serper | Price-War / Viral-Heat / Market-Void | Detects highest-velocity market events with real rising-term momentum metrics |
| scavenger_social | Serper + Google NLP | Sentiment-Bleed / Feature-Gap | NLP pre-scores snippets for emotional charge before the agent sees them |
| forager | Serper | Market-Void | Looks where others don't — underserved segments, abandoned keywords, unaddressed objections |
| skeptic ¹ | Serper (counter-evidence) | Doubt | Challenges the highest-intensity claim — rates `challenge_strength` and `verdict` |
| strategist ¹ | Serper | Strategy | Exploiter — reads top scents, converts to campaign hook with 3 distinct options |
| mutator | Blackboard only | Mutation | Waits for Strategy — picks best of 3 hook options from the trail, evolves into 5 distinct variants |
| audience_sniper | Serper (trail-derived) | Audience | Waits for Mutation — builds queries from live trail terms, names micro-segments with DSP targeting layers |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| LLM | Vertex AI — Gemini 2.0 Flash | GCP-native, structured JSON output mode, temperature 1.2 |
| Blackboard | Cloud Firestore | `on_snapshot` fires instantly on write — stigmergy requires zero-latency signal propagation |
| Market data | BigQuery public dataset | `google_trends.top_rising_terms` — percent_gain, national rank, real search momentum |
| Sentiment | Google Natural Language API | Sentence-level sentiment pre-loaded as agent context |
| Web search | Serper.dev | Structured Google results, 10 results/query |
| Backend | FastAPI + sse-starlette | Async-first; SSE for real-time agent output streaming |
| Frontend | Vanilla JS + Tailwind | Zero build step, SSE-native |

Firestore over Redis: `on_snapshot` bridges into asyncio via `call_soon_threadsafe` — each agent's reaction loop wakes the instant a peer scent lands. No polling.

---

## Queries

Works best with a product, competitive tension, or market context:

```
HubSpot vs Salesforce — campaign for mid-market SaaS
Figma vs Adobe for independent designers
Linear vs Jira for fast-moving engineering teams
Launch campaign for an AI legal assistant
Campaign to move developers from AWS to GCP
```

The `vs` keyword activates competitor-split search queries across all agents. Without it, agents run broader market intelligence queries.

Less suited for: abstract brand exercises with no product, pure copywriting with no market context.

---

## Setup

**Prerequisites**: Python 3.9+, GCP project, ADC configured

```bash
gcloud auth application-default login
gcloud services enable firestore.googleapis.com bigquery.googleapis.com \
  naturallanguage.googleapis.com aiplatform.googleapis.com

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# backend/.env
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
SERPER_API_KEY=your-serper-key

uvicorn main:app --reload
```

Open `frontend/index.html`. No build step.

## API

```bash
curl -X POST http://localhost:8000/campaign \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Figma vs Adobe for independent designers"}'
# → { "campaign_id": "abc-123" }

curl -N http://localhost:8000/stream/abc-123                          # SSE stream
curl -N "http://localhost:8000/stream/abc-123?demo_kill=forager"     # kill an agent live
curl http://localhost:8000/result/abc-123                            # final brief

curl -X POST http://localhost:8000/followup/abc-123 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Focus on enterprise buyers. More aggressive."}'    # re-run on existing trail

curl -X POST http://localhost:8000/feedback/abc-123 \
  -H "Content-Type: application/json" \
  -d '{"hook_angle": "bold", "metric_name": "ctr", "metric_value": 4.2}'  # record real results
```

SSE events: `observation` · `scent_reinforced` · `status` · `agent_offline` · `complete` · `error`

---

## Project Structure

```
backend/
├── main.py                  FastAPI — /campaign, /stream, /result, /followup, /feedback
├── swarm.py                 Swarm runner, _FirestoreBus, run_followup, decay/reinforce
├── state.py                 Firestore read/write
├── agents/
│   ├── base.py              Gemini call, fetch_context, wake_on, react_only, prompt helpers
│   ├── scavenger_market.py
│   ├── scavenger_social.py
│   ├── strategist.py
│   ├── forager.py
│   ├── skeptic.py
│   ├── mutator.py
│   ├── audience_sniper.py
│   └── __init__.py
└── data/
    ├── websearch.py         Serper.dev
    ├── trends_bq.py         BigQuery Trends
    └── nlp.py               Google NLP sentiment
frontend/
└── index.html               SSE stream, scent cards, Intelligence Report, follow-up chat bar
```

---

*Theoretical basis: Stigmergy (Grassé, 1959) · Ant Colony Optimization (Dorigo, 1992) · Digital Pheromone Architecture (Parunak et al.)*
