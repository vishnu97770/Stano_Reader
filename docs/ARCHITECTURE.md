# Stano Reader — Architecture

## Overview

Stano Reader is a deterministic, offline Pitman shorthand recognition platform. There is no machine learning. All recognition is done by pure geometric rule-based detectors operating on raw stroke point arrays.

The pipeline has two phases:

1. **Per-stroke analysis** — runs immediately when the user lifts the pen.
2. **Sequence analysis** — runs on the accumulated outline (all strokes so far in the current word).

---

## Full pipeline (data flow)

```
User draws stroke on <canvas>
          │
          ▼
  [DrawingCanvas hook]
  onStrokeComplete(stroke: Stroke)
          │
          ├──▶ detectVowel(stroke)  ──────────────────────────────┐
          │         │                                              │
          │         │ is_vowel=false                              │ is_vowel=true
          │         │                                             │ → setVowelAttachments
          │         ▼                                             │ → return (skip consonant path)
          │
          ├──▶ analyzeStroke       → StrokeFeatures (bounding box, angles)
          ├──▶ classifySymbol      → symbol (P, B, T …)  ──▶ addStroke(outline)
          ├──▶ classifyWeight      → LIGHT / NORMAL / HEAVY
          ├──▶ classifyCircle      → SMALL_S / LARGE_S / SES / NONE
          ├──▶ classifyHook        → INITIAL_N / FINAL_N / NONE …
          ├──▶ classifyLength      → SHORT / NORMAL / LONG
          ├──▶ classifyPosition    → ABOVE_LINE / ON_LINE / BELOW_LINE
          └──▶ detectPhrase        → phraseography match or null
                    │
                    ▼
          [outline.recognizedStrokes changes]
                    │
                    ▼
          usePhoneme(outline) → IPA sequence  [/p/, /b/ …]
                    │
                    ▼
          useCandidates(phonemes, transcript) → word candidates
                    │
                    ▼ (optional)
          useAIRefinement → POST /api/refine-candidates
                                  │
                                  ▼ (non-blocking Socket.IO push)
                          candidates_refined event
                                  │
                                  ▼
                          displayCandidates (re-ranked)
```

---

## Backend layers

```
backend/
├── app/
│   ├── main.py            FastAPI + Socket.IO ASGI app, health endpoints,
│   │                      ResponseCacheMiddleware
│   ├── config.py          pydantic-settings (reads .env)
│   ├── cache.py           Thread-safe LRU cache, TTL=5min, max=1000 entries
│   ├── database.py        SQLAlchemy + SQLite engine, session factory
│   ├── models.py          ORM models (Session, Stroke)
│   ├── api/               One FastAPI router per detector/feature:
│   │   ├── classify.py    /classify-family
│   │   ├── symbol.py      /classify-symbol
│   │   ├── weight.py      /classify-weight
│   │   ├── circle.py      /classify-circle
│   │   ├── hook.py        /classify-hook
│   │   ├── length.py      /classify-length
│   │   ├── position.py    /classify-position
│   │   ├── vowel.py       /detect-vowel
│   │   ├── phrase.py      /detect-phrase
│   │   ├── analysis.py    /analyze-stroke
│   │   ├── phoneme.py     /map-phonemes
│   │   ├── candidate.py   /get-candidates
│   │   ├── sessions.py    /sessions CRUD
│   │   ├── image.py       /upload-image, /process-image
│   │   └── ai.py          /refine-candidates
│   ├── schemas/           Pydantic request schemas (one per API file)
│   └── socket/
│       └── events.py      Socket.IO server + set_sio/get_sio singleton
└── recognizer/
    ├── analyzer.py         Geometric feature extraction
    ├── family_classifier.py Broad family (HORIZONTAL / VERTICAL / …)
    ├── symbol_classifier.py Precise Pitman symbol (P, B, T, D …)
    ├── weight_classifier.py Stroke weight
    ├── circle_detector.py   S / SES / circle detection
    ├── hook_detector.py     Hook type
    ├── length_detector.py   Stroke length
    ├── position_detector.py Line-of-writing position
    ├── vowel_detector.py    Vowel sign detection + IPA
    ├── outline_builder.py   Stroke sequence → phoneme outline
    ├── phoneme_mapper.py    Outline → IPA sequence
    ├── candidate_engine.py  IPA → word candidates
    ├── context_engine.py    Transcript history → candidate re-ranking
    ├── phrase_detector.py   Phraseography matching
    ├── image_processor.py   Image upload validation + preprocessing
    ├── stroke_extractor.py  Contour → stroke point extraction
    ├── page_analyzer.py     Full page analysis
    ├── prompt_builder.py    LLM prompt construction
    ├── ai_rules.py          Skip / invoke gates for AI refinement
    ├── ai_context_engine.py Ollama call + response parsing
    └── schemas.py           All Pydantic result models
```

---

## Frontend layers

```
frontend/src/
├── main.tsx             ReactDOM.createRoot — wraps <App> in <ErrorBoundary>
├── App.tsx              State-based router: 'write' | 'upload'
├── pages/
│   ├── WritingPage.tsx  Main drawing page — owns all state, composes panels
│   └── UploadPage.tsx   Image upload page — drag-drop, preview, results
├── components/
│   ├── Canvas/          DrawingCanvas (pointer events → stroke points)
│   ├── Header/          Nav tabs (Write / Upload), connection status
│   ├── OfflineBanner/   Shown when navigator.onLine is false
│   ├── ErrorBoundary/   Catches render errors, shows recovery UI
│   ├── CandidatePanel/  Word candidate list with confidence bars + skeletons
│   ├── AIPanel/         AI toggle, domain selector, before/after ranking
│   ├── PhrasePanel/     Phraseography match display
│   ├── VowelPanel/      Vowel IPA + attachment info
│   ├── TranscriptPanel/ Accepted word list + undo
│   └── ...              One component per detector result
├── hooks/
│   ├── useSocket.ts     Socket.IO lifecycle, socketId exposure
│   ├── useSession.ts    Session CRUD
│   ├── useOutline.ts    Stroke → outline state
│   ├── usePhoneme.ts    Outline → IPA (calls /map-phonemes)
│   ├── useCandidates.ts IPA → candidates (calls /get-candidates)
│   ├── useAIRefinement.ts POST /refine-candidates + listen candidates_refined
│   ├── useOnlineStatus.ts navigator.onLine + online/offline events
│   └── use{Detector}.ts One hook per detector endpoint
├── services/
│   ├── apiService.ts    All REST calls
│   └── socketService.ts Socket.IO singleton + getSocketId()
└── types/               TypeScript interfaces matching backend schemas
```

---

## Caching layer

Six deterministic classifier endpoints have their POST responses cached in memory:

| Endpoint | Cache key |
|---|---|
| `/api/classify-family` | `path:sha256(body)` |
| `/api/classify-symbol` | same |
| `/api/classify-circle` | same |
| `/api/classify-hook` | same |
| `/api/classify-length` | same |
| `/api/classify-position` | same |

Cache is an `OrderedDict`-based LRU store (`backend/app/cache.py`):
- Max 1000 entries
- TTL 5 minutes per entry
- Thread-safe via `threading.Lock`
- Cache hit adds `X-Cache: HIT` header; miss adds `X-Cache: MISS`

---

## AI refinement (M17)

```
POST /api/refine-candidates
        │
        ├── should_invoke_ai()? → no → return fallback_used=True immediately
        │
        ├── return HTTP 200 immediately (fallback placeholder)
        │
        └── BackgroundTasks: run_ai_refinement_task()
                  │
                  └── asyncio.to_thread(_call_ollama_sync)
                            │
                            ├── build_prompt()
                            ├── urllib.request.urlopen(ollama_url, timeout=3s)
                            ├── _parse_llm_response()
                            └── sio.emit("candidates_refined", result, to=socket_id)
```

AI is skipped when:
- Top candidate confidence > 0.95
- A phrase was detected
- No transcript context AND only one candidate
- No candidates at all

AI is invoked when:
- Top-2 candidates within 0.10 confidence gap (ambiguous)
- Transcript context available
- Vowel signals detected

---

## Socket.IO events

| Direction | Event | Payload |
|---|---|---|
| Client → Server | `stroke` | `{ sessionId, stroke, penColor, penWidth }` |
| Server → Client | `stroke` | same (broadcast to other clients in session) |
| Server → Client | `candidates_refined` | `AIRefinementResult` |

---

## Docker architecture

```
docker-compose.yml
│
├── frontend (Nginx alpine, port 80)
│   ├── /          → /usr/share/nginx/html (React build)
│   ├── /api/*     → proxy http://backend:8000
│   └── /socket.io/* → proxy http://backend:8000 (WebSocket upgrade)
│
└── backend (Python 3.11-slim, port 8000, non-root appuser)
    └── volume: sqlite_data → /app/data/stano_reader.db
```

Health check: Docker polls `GET /ready` every 30s. Frontend depends on backend being healthy before starting.
