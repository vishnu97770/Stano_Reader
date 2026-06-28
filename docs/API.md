# Stano Reader — API Reference

All endpoints are under `/api/`. The server runs on port 8000 by default.

Socket.IO events are documented in the [Architecture guide](ARCHITECTURE.md).

---

## Health

### `GET /health`

Always returns 200. Used by monitoring tools.

```json
{ "status": "ok", "version": "0.1.0", "uptime_seconds": 42.1 }
```

### `GET /ready`

Returns 200 when the database is reachable, 503 otherwise. Used by Docker health checks.

```json
{ "ready": true, "database": "ok", "details": { "sqlite": true } }
```

---

## Sessions

### `POST /api/sessions`

Create a new session with an initial set of strokes.

**Request**
```json
{
  "name": "My Session",
  "strokes": [
    {
      "id": "uuid",
      "points": [{ "x": 10, "y": 20, "timestamp": 1718000000 }],
      "pen_color": "#1a1a1a",
      "pen_width": 2.5
    }
  ]
}
```

**Response** `201`
```json
{ "id": "uuid", "name": "My Session", "created_at": "2024-01-01T00:00:00" }
```

### `GET /api/sessions`

List all sessions.

**Response** `200` — array of `{ id, name, created_at }`

### `GET /api/sessions/{session_id}`

Load a session with its strokes and transcript.

**Response** `200`
```json
{
  "id": "uuid",
  "name": "My Session",
  "strokes": [...],
  "transcript": ["the", "quick", "brown"]
}
```

### `POST /api/sessions/{session_id}/strokes`

Append strokes to an existing session.

**Request** — array of stroke objects (same shape as above)

**Response** `200` `{ "appended": 3 }`

### `POST /api/sessions/{session_id}/transcript`

Save a transcript array to a session.

**Request** `{ "words": ["the", "quick"] }`

**Response** `200` `{ "saved": true }`

---

## Stroke analysis (M3)

### `POST /api/analyze-stroke`

Extract geometric features from a stroke.

**Request**
```json
{ "stroke_id": "uuid", "points": [{ "x": 10, "y": 20 }] }
```

**Response** `200` — `StrokeFeatures` object with bounding box, length, angles, aspect ratio, etc.

---

## Classification (M3 — cached)

> Responses for these endpoints are cached for 5 minutes. Cache key = path + request body hash.

### `POST /api/classify-family`

Classify the broad stroke family.

**Request** `{ "stroke_id": "uuid", "points": [...] }`

**Response** `200`
```json
{ "stroke_id": "uuid", "family": "HORIZONTAL", "confidence": 0.92 }
```

Possible families: `HORIZONTAL`, `VERTICAL`, `CURVE`, `DOT`, `CIRCLE`, `UNKNOWN`

### `POST /api/classify-symbol`

Classify the precise Pitman symbol.

**Request** `{ "stroke_id": "uuid", "points": [...] }`

**Response** `200`
```json
{
  "stroke_id": "uuid",
  "symbol": "P",
  "family": "HORIZONTAL",
  "confidence": 0.88,
  "alternatives": [{ "symbol": "B", "confidence": 0.72 }]
}
```

---

## Weight classifier (M4 — cached)

### `POST /api/classify-weight`

Detect stroke pressure / weight.

**Request** `{ "stroke_id": "uuid", "points": [...] }`

**Response** `200`
```json
{ "stroke_id": "uuid", "weight": "NORMAL", "confidence": 0.85, "detected": true }
```

Weight values: `LIGHT`, `NORMAL`, `HEAVY`, `AMBIGUOUS`

---

## Circle detector (M5 — cached)

### `POST /api/classify-circle`

Detect S / SES / large-circle shapes.

**Request** `{ "stroke_id": "uuid", "points": [...] }`

**Response** `200`
```json
{ "stroke_id": "uuid", "circle_type": "SMALL_S", "confidence": 0.9, "detected": true }
```

---

## Hook detector (M6 — cached)

### `POST /api/classify-hook`

Detect initial or final hook.

**Request** `{ "stroke_id": "uuid", "points": [...] }`

**Response** `200`
```json
{
  "stroke_id": "uuid",
  "hook_type": "INITIAL_N",
  "attachment_position": "initial",
  "confidence": 0.87,
  "detected": true
}
```

---

## Length classifier (M7 — cached)

### `POST /api/classify-length`

Classify stroke length relative to average.

**Request** `{ "stroke_id": "uuid", "points": [...] }`

**Response** `200`
```json
{ "stroke_id": "uuid", "length_class": "NORMAL", "relative_length": 1.02, "detected": true }
```

Length classes: `SHORT`, `NORMAL`, `LONG`

---

## Phoneme mapper (M9)

### `POST /api/map-phonemes`

Map an outline (stroke sequence) to an IPA phoneme sequence.

**Request**
```json
{
  "stroke_id": "uuid",
  "recognized_strokes": [
    { "stroke_id": "s1", "symbol": "P", "family": "HORIZONTAL" }
  ]
}
```

**Response** `200`
```json
{ "phonemes": ["/p/", "/b/"], "confidence": 0.91 }
```

---

## Candidate engine (M10)

### `POST /api/get-candidates`

Look up word candidates from a phoneme sequence + transcript context.

**Request**
```json
{
  "phonemes": ["/p/", "/b/"],
  "transcript_context": ["the", "best"],
  "max_candidates": 5
}
```

**Response** `200`
```json
{
  "candidates": [
    { "word": "pub", "confidence": 0.88 },
    { "word": "pave", "confidence": 0.71 }
  ]
}
```

---

## Position classifier (M12 — cached)

### `POST /api/classify-position`

Determine stroke position relative to the writing line.

**Request**
```json
{ "stroke_id": "uuid", "points": [...], "canvas_height": 600 }
```

**Response** `200`
```json
{
  "stroke_id": "uuid",
  "word_position": "ON_LINE",
  "confidence": 0.95,
  "detected": true
}
```

Position values: `ABOVE_LINE`, `ON_LINE`, `BELOW_LINE`

---

## Vowel detector (M13)

### `POST /api/detect-vowel`

Determine whether a stroke is a vowel sign and which vowel it represents.

**Request**
```json
{
  "stroke_id": "uuid",
  "points": [...],
  "nearby_strokes": [
    { "stroke_id": "s1", "family": "HORIZONTAL", "centroid_x": 100, "centroid_y": 200,
      "start_x": 80, "start_y": 200, "end_x": 120, "end_y": 200 }
  ]
}
```

**Response** `200`
```json
{
  "stroke_id": "uuid",
  "is_vowel": true,
  "ipa": "/æ/",
  "degree": 1,
  "position": "before",
  "attached_to_stroke_id": "s1",
  "confidence": 0.82
}
```

---

## Phrase detector (M15)

### `POST /api/detect-phrase`

Check whether a stroke sequence matches a known phraseography.

**Request**
```json
{
  "stroke_id": "uuid",
  "families": ["HORIZONTAL", "CURVE"],
  "candidate_words": ["give", "get"]
}
```

**Response** `200`
```json
{
  "stroke_id": "uuid",
  "is_phrase": true,
  "phrase_text": "I am",
  "confidence": 0.95,
  "alternatives": [],
  "reasoning": "Matched phraseography rule P001"
}
```

---

## Image processing (M16)

### `POST /api/upload-image`

Upload a shorthand image for processing.

**Request** — `multipart/form-data` with field `file` (JPEG / PNG / WebP / BMP)

**Response** `200`
```json
{
  "image_id": "uuid",
  "width": 800,
  "height": 600,
  "format": "jpeg",
  "size_bytes": 45321
}
```

### `POST /api/process-image`

Extract strokes from image-derived stroke data.

**Request**
```json
{
  "strokes": [...],
  "canvas_height": 600,
  "canvas_width": 800
}
```

**Response** `200` — array of extracted stroke objects.

---

## AI refinement (M17)

### `POST /api/refine-candidates`

Trigger local LLM re-ranking of candidates. Returns immediately; result is pushed via Socket.IO `candidates_refined` event.

**Request**
```json
{
  "stroke_id": "uuid",
  "candidates": [{ "word": "give", "confidence": 0.75 }],
  "transcript_context": ["I"],
  "outline": "G, V",
  "ipa_sequence": ["/g/", "/v/"],
  "domain": "general",
  "vowel_signals": [],
  "phrase_detected": false,
  "socket_id": "socket-id-string"
}
```

Domain values: `general`, `legal`, `diplomatic`, `parliamentary`

**Response** `200` — `AIRefinementResult` (preliminary, `fallback_used=true` until Socket.IO pushes the real result)

```json
{
  "stroke_id": "uuid",
  "was_invoked": true,
  "promoted_candidate": null,
  "confidence_boost": 0.0,
  "reasoning": "",
  "original_ranking": ["give"],
  "refined_ranking": ["give"],
  "fallback_used": true,
  "detected": false,
  "confidence": 0.0,
  "alternatives": []
}
```

**Socket.IO event** `candidates_refined` — same `AIRefinementResult` shape with real re-ranking.
