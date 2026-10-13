# 🌍 Build with Gemini: Travel Agent Project Summary & Lab Documentation

## 1. Project Overview
**Travel Agent** is a full-featured conversational AI travel companion built with the **Google Agent Development Kit (ADK)**, powered by **Gemini (gemini-3.6-flash)**, and deployed on **Google Cloud Vertex AI Agent Runtime**.

The agent assists travelers in discovering destinations, checking live weather, finding nearby points of interest via Google Places, generating photorealistic destination postcards, remembering user preferences and dietary constraints across sessions, and executing sandbox code for budget and itinerary calculations.

---

## 2. Key Architecture & Features Completed

| Capability | Component / Service | Implementation Details |
|---|---|---|
| **Agent Core & Reasoning** | Google ADK + `gemini-3.6-flash` | Defined in `app/agent.py` with structured system instructions and retry options. |
| **Long-Term Memory** | Vertex AI Memory Bank | Automatic cross-session memory preload (`PreloadMemoryTool`) and post-turn memory extraction callback (`generate_memories_callback`) to retain traveler preferences, budget tiers, and dietary restrictions. |
| **Destination Catalog** | Google Cloud Firestore | `search_destinations` tool querying curated documents in Firestore (Kyoto, Cape Town, Banff, Florence, etc.). Initialized via `seed_firestore.py`. |
| **Real-Time Weather** | Open-Meteo REST API | `get_weather` tool querying live temperatures, weather conditions, humidity, and wind speeds without API key overhead. |
| **Geocoding & Places** | Google Maps & Places API (New) | `geocode_address` and `find_nearby_places` to look up exact latitude/longitude and discover attractions, restaurants, and hotels. |
| **Postcard Image Generation** | Gemini Image Gen + Cloud Storage | `generate_travel_image` tool generating photorealistic destination postcards using `gemini-3.1-flash-lite-image`, saving artifacts, and uploading to public Cloud Storage buckets. |
| **Code Execution Sandbox** | Agent Engine Sandbox Code Executor | `AgentEngineSandboxCodeExecutor` allowing the agent to securely run Python code to convert currencies and calculate trip budgets accurately. |
| **Rich User Interface** | A2UI (Agent-to-User Interface) | Native display cards, rows, columns, and embedded images rendered via `a2ui_callback` and client-side renderer. |
| **Web Frontend Proxy** | FastAPI + A2A Protocol | Decoupled web client (`frontend/main.py`) serving an interactive chat UI, communicating directly with Vertex AI Agent Runtime over A2A protocol. |
| **Cloud Deployment** | Vertex AI Agent Runtime | Packaged as containerized Reasoning Engine in GCP region `us-central1`. |

---

## 3. Repository File Structure

```
BuildWithGemini/
├── project_brief.md                 # Original project design brief & capability matrix
├── README.md                        # Workshop root documentation
├── LAB_SUMMARY.md                   # Complete lab documentation and feature breakdown
└── travel-agent/
    ├── Dockerfile                   # Container build definition for Agent Runtime
    ├── pyproject.toml               # Python project dependencies (ADK, genai, etc.)
    ├── agents-cli-manifest.yaml     # Agents CLI project configuration
    ├── deployment_metadata.json     # Remote Vertex AI Reasoning Engine resource details
    ├── seed_firestore.py            # Seed script for the destination database
    ├── app/
    │   ├── agent.py                 # Root ADK agent configuration & callbacks
    │   ├── tools.py                 # Destination search, geocoding, places, image gen
    │   ├── a2ui_utils.py            # A2UI callback and data transform utilities
    │   └── a2ui_instruction.py      # System prompts and schema specifications
    └── frontend/
        ├── Dockerfile               # Container spec for the frontend web proxy
        ├── requirements.txt         # FastAPI, httpx, a2a-sdk dependencies
        ├── main.py                  # FastAPI A2A proxy server
        └── static/
            └── index.html           # Modern responsive chat interface + A2UI renderer
```

---

## 4. How to Run Locally

### Prerequisites
- Python 3.11+
- `uv` (recommended) or standard `pip` / `venv`
- Google Cloud Application Default Credentials (or Google AI Studio `GEMINI_API_KEY`)

### Running the Agent Backend
```bash
cd travel-agent
uv run adk web app
```
The ADK developer UI will be available at `http://localhost:8000`.

### Running the Web Frontend (Chat UI)
```bash
cd travel-agent/frontend
uv run python main.py
```
Open `http://localhost:8081` in your browser.

---

## 5. Deployed Cloud Resource Details
- **Google Cloud Project**: `qwiklabs-gcp-03-d9aebf9c9790`
- **Region**: `us-central1`
- **Agent Runtime Resource**:
  `projects/289235292550/locations/us-central1/reasoningEngines/4540411551546343424`
- **Agent Card URL**:
  `https://us-central1-aiplatform.googleapis.com/reasoningEngines/v1/projects/289235292550/locations/us-central1/reasoningEngines/4540411551546343424/api/a2a/app/.well-known/agent-card.json`
