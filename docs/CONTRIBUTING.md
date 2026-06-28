# Contributing to Stano Reader

Thank you for your interest in contributing.

---

## Development setup

**Prerequisites:** Python 3.11+, Node 20+, Git.

```bash
git clone https://github.com/vishnu97770/Stano_Reader.git
cd Stano_Reader

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

Frontend runs on [http://localhost:5173](http://localhost:5173).

---

## Running tests

All tests live in `backend/tests/`. Run the full suite from the repo root:

```bash
cd backend
.venv/bin/python -m pytest tests/ -v
```

All 292+ tests must pass before a PR is merged. New code requires new tests.

TypeScript check:

```bash
cd frontend
npx tsc --noEmit
```

---

## Adding a new detector

1. **Recognizer logic** — add `backend/recognizer/my_detector.py`:
   - Pure functions only. No I/O, no side effects.
   - Return a Pydantic model defined in `recognizer/schemas.py`.
   - Follow the `detected: bool`, `confidence: float`, `reasoning: str` pattern.

2. **API endpoint** — add `backend/app/api/my_detector.py`:
   - One `APIRouter` with a single `POST /api/my-detector` route.
   - Validate minimum point count; raise `HTTPException(422, ...)` if violated.

3. **Request schema** — add `backend/app/schemas/my_detector.py`:
   - Extend `PointRequest` or write a new Pydantic model for the request body.

4. **Register the router** — add import + `api_router.include_router(...)` in `backend/app/api/router.py`.

5. **Frontend hook** — add `frontend/src/hooks/useMyDetector.ts`:
   - Mirrors the pattern of `useStrokeCircle.ts` or `useStrokeHook.ts`.
   - Calls `api.myDetector.classify(...)`.

6. **Frontend types** — add result type in `frontend/src/types/`.

7. **Tests** — add `backend/tests/test_my_detector.py` with at least 10 tests covering:
   - Normal detection
   - Edge: empty / single point input
   - Edge: boundary confidence values
   - API endpoint (422 for < 2 points, 200 for valid input)

8. **API docs** — add endpoint description in `docs/API.md`.

---

## Code conventions

**Backend:**
- One file per detector in `recognizer/`. Never import cross-detectors.
- All public detector functions named `detect_*` or `classify_*`.
- Type-annotate every function (Pydantic v2, Python 3.11+ union syntax `X | Y`).
- No ML, no paid APIs, no network calls (except Ollama in `ai_context_engine.py`).

**Frontend:**
- Strict TypeScript — no `any`, no `// @ts-ignore`.
- One component per file in `components/<Name>/<Name>.tsx`.
- Props interfaces defined inline above the component.
- Tailwind only — no inline styles unless driven by dynamic values.

---

## Pull request process

1. Fork the repository and create a branch: `feature/my-feature` or `fix/my-bug`.
2. Write tests first (or alongside) — all existing tests must still pass.
3. Run `tsc --noEmit` before pushing.
4. Open a PR against `main` and fill out the PR template.
5. One reviewer approval required to merge.

---

## What we do not accept

- ML models or training pipelines — the recognizer must remain deterministic.
- Paid API integrations (OpenAI, Google, AWS, etc.).
- Dependencies that require a network connection at runtime.
- Code without tests.
