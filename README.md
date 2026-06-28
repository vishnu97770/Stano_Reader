# Stano Reader

Offline, AI-free, deterministic Pitman shorthand recognition platform.

Draw shorthand strokes in a browser — receive word candidates in real time. No cloud, no API keys, no ML models. Everything runs locally.

---

## Quickstart (Docker)

```bash
git clone https://github.com/vishnu97770/Stano_Reader.git
cd Stano_Reader
cp .env.example .env
docker compose up
```

Open [http://localhost](http://localhost) in your browser.

**Optional — AI re-ranking (M17):** install [Ollama](https://ollama.ai), pull a model, and set `OLLAMA_URL` in `.env`. The app falls back silently when Ollama is unavailable.

```bash
ollama pull llama3.2:1b
```

---

## Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Frontend: [http://localhost:5173](http://localhost:5173) · Backend: [http://localhost:8000](http://localhost:8000)

---

## Recognition pipeline

```
Draw stroke on canvas
      │
      ▼
Vowel detector  ──────────────────────────────────────┐
      │ (consonant path only)                         │ (vowel mark)
      ▼                                               │
Symbol classifier (HORIZONTAL / VERTICAL / CURVE …)  │
      │                                               │
      ▼                                               │
Outline builder (stroke sequence → phoneme outline)  │
      │                                               │
      ▼                                               │
Phoneme mapper (outline → IPA sequence)              │
      │                                               │
      ▼                                               │
Candidate engine (IPA → word list with confidence)   │
      │                                               │
      ▼                                               │
Context engine (transcript history → re-rank)        │◄──┘
      │
      ▼ (optional — M17)
AI re-ranker (Ollama local LLM — non-blocking)
      │
      ▼
Word Candidates panel
```

Auxiliary detectors run in parallel for each stroke:

| Detector | Endpoint | Purpose |
|---|---|---|
| Weight | `/api/classify-weight` | Light / normal / heavy |
| Circle | `/api/classify-circle` | S / SES / circle-S detection |
| Hook | `/api/classify-hook` | Initial / final hook type |
| Length | `/api/classify-length` | Short / normal / long |
| Position | `/api/classify-position` | Line of writing position |
| Phrase | `/api/detect-phrase` | Phraseography match |

---

## Project structure

```
Stano_Reader/
├── backend/
│   ├── app/
│   │   ├── api/          REST endpoints (one file per detector)
│   │   ├── schemas/      Pydantic request schemas
│   │   ├── socket/       Socket.IO server + events
│   │   ├── cache.py      LRU response cache (thread-safe, TTL 5min)
│   │   ├── config.py     Environment settings
│   │   ├── database.py   SQLAlchemy + SQLite
│   │   └── main.py       FastAPI app + health endpoints
│   ├── recognizer/       All detection / classification logic
│   └── tests/            pytest suite (292+ tests)
├── frontend/
│   ├── src/
│   │   ├── components/   Pure UI components
│   │   ├── hooks/        State and side-effect hooks
│   │   ├── pages/        WritingPage, UploadPage
│   │   ├── services/     API + Socket.IO clients
│   │   └── types/        TypeScript contracts
│   └── package.json
├── docker/
│   └── nginx.conf        Nginx reverse-proxy config
├── docs/
│   ├── API.md            All endpoints M1–M17
│   ├── ARCHITECTURE.md   Pipeline diagrams + module docs
│   └── CONTRIBUTING.md   Dev setup, adding detectors, PR process
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml     Production
└── docker-compose.dev.yml Hot-reload development
```

---

## Health endpoints

| Endpoint | Response | Use |
|---|---|---|
| `GET /health` | `{status, version, uptime_seconds}` | Always 200 |
| `GET /ready` | `{ready, database, details}` | 200 ok / 503 unavailable |

---

## Milestone history

| Milestone | Description |
|---|---|
| M1 | Browser canvas, stroke capture, Socket.IO |
| M2 | Session persistence (SQLite) |
| M3 | Symbol classification (HORIZONTAL, VERTICAL, CURVE, DOT, CIRCLE) |
| M4 | Stroke weight classifier |
| M5 | Circle / S-circle detector |
| M6 | Hook detector |
| M7 | Length classifier |
| M8 | Outline builder |
| M9 | Phoneme mapper |
| M10 | Candidate engine |
| M11 | Context engine (transcript re-ranking) |
| M12 | Position classifier |
| M13 | Vowel sign detector |
| M14 | Schema audit + API hardening |
| M15 | Vowel attachment + vowel-boosted candidates |
| M16 | Image upload and stroke extraction |
| M17 | Local LLM re-ranking (Ollama, non-blocking) |
| M18 | Production release — Docker, CI/CD, caching, docs |

---

## License

[MIT](LICENSE)
