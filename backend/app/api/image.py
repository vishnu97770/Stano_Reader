"""
Image upload and processing endpoints.

POST /api/upload-image
    - Accepts multipart image upload (JPEG / PNG / WEBP, max 10 MB)
    - Preprocesses, extracts strokes, analyses page layout
    - Returns ImageUploadResult

POST /api/process-image
    - Accepts extracted strokes + canvas dimensions (from upload result)
    - Runs the full recognition pipeline (same detectors as canvas strokes)
    - Returns ImageProcessResult
"""

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.schemas.image import ImageProcessRequest
from recognizer.analyzer import analyze_stroke
from recognizer.candidate_engine import get_candidates
from recognizer.circle_detector import detect_circle
from recognizer.family_classifier import classify_stroke
from recognizer.hook_detector import detect_hook
from recognizer.image_processor import preprocess_image, validate_upload
from recognizer.length_detector import detect_length
from recognizer.page_analyzer import analyze_page
from recognizer.phoneme_mapper import map_symbols_to_phonemes
from recognizer.phrase_detector import detect_phrase
from recognizer.position_detector import detect_position
from recognizer.schemas import (
    ExtractedStroke,
    ImageProcessResult,
    ImageStrokeResult,
    ImageUploadResult,
    PageMetadata,
    WritingZone,
    ExtractedStrokePoint,
)
from recognizer.stroke_extractor import extract_strokes
from recognizer.symbol_classifier import classify_symbol
from recognizer.vowel_detector import detect_vowel
from recognizer.weight_classifier import classify_weight

router = APIRouter(prefix="/api", tags=["image"])


@router.post("/upload-image", response_model=ImageUploadResult)
async def upload_image(file: UploadFile = File(...)) -> ImageUploadResult:
    """
    Accept a JPEG / PNG / WEBP file, preprocess it, extract strokes, and
    return the strokes in canvas point format alongside page metadata.
    """
    content_type = file.content_type or ""
    data = await file.read()

    try:
        validate_upload(data, content_type)
    except ValueError as exc:
        status = 413 if "MB" in str(exc) else 422
        raise HTTPException(status_code=status, detail=str(exc))

    binary = preprocess_image(data)
    raw_strokes = extract_strokes(binary)
    page = analyze_page(binary)

    strokes = [
        ExtractedStroke(
            id=s.id,
            points=[
                ExtractedStrokePoint(x=p.x, y=p.y, pressure=p.pressure, timestamp=p.timestamp)
                for p in s.points
            ],
        )
        for s in raw_strokes
    ]

    page_meta = PageMetadata(
        canvas_width=page.canvas_width,
        canvas_height=page.canvas_height,
        writing_zones=[
            WritingZone(top=z.top, bottom=z.bottom, baseline=z.baseline)
            for z in page.writing_zones
        ],
        line_count=page.line_count,
        image_width=page.image_width,
        image_height=page.image_height,
    )

    return ImageUploadResult(
        strokes=strokes,
        stroke_count=len(strokes),
        page_metadata=page_meta,
    )


@router.post("/process-image", response_model=ImageProcessResult)
def process_image(body: ImageProcessRequest) -> ImageProcessResult:
    """
    Run the full Pitman recognition pipeline on image-extracted strokes.

    Calls the same detector functions as the canvas pipeline so that results
    are directly comparable with live-drawn strokes.
    """
    stroke_results: list[ImageStrokeResult] = []
    all_symbols: list[str] = []
    all_families: list[str] = []
    last_stroke_id = "img-none"

    for stroke_data in body.strokes:
        stroke_id = stroke_data.id
        last_stroke_id = stroke_id
        points = [
            {"x": p.x, "y": p.y, "pressure": p.pressure, "timestamp": p.timestamp}
            for p in stroke_data.points
        ]

        if len(points) < 2:
            continue

        # Core analysis — same call chain as the canvas pipeline
        features = analyze_stroke(stroke_id, points)
        family_result = classify_stroke(features)
        sym_result = classify_symbol(features, family_result)

        if sym_result.symbol != "UNKNOWN":
            all_symbols.append(sym_result.symbol)
            all_families.append(sym_result.family)

        circle_result = detect_circle(stroke_id, features, points)
        hook_result = detect_hook(stroke_id, features, points)
        length_result = detect_length(stroke_id, features, sym_result.family if sym_result.symbol != "UNKNOWN" else None)
        pos_result = detect_position(stroke_id, points, body.canvas_height)
        weight_result = classify_weight(stroke_id, points)
        # Vowel detection with no nearby strokes (image pipeline does not yet
        # resolve cross-stroke vowel attachment — treated like standalone marks)
        detect_vowel(stroke_id, points, [])

        stroke_results.append(ImageStrokeResult(
            stroke_id=stroke_id,
            symbol=sym_result.symbol,
            family=sym_result.family,
            confidence=sym_result.confidence,
            circle_is_circle=circle_result.is_circle,
            hook_is_hook=hook_result.is_hook,
            length_is_modified=length_result.is_modified,
            position=pos_result.position,
            weight=weight_result.weight,
        ))

    # Phoneme + candidate + phrase pipeline
    phonemes = map_symbols_to_phonemes(all_symbols)
    raw_candidates = get_candidates(phonemes, max_results=10)
    candidates = [{"word": c.word, "confidence": c.confidence} for c in raw_candidates]

    phrase_result = detect_phrase(last_stroke_id, all_families, [c["word"] for c in candidates])

    return ImageProcessResult(
        stroke_results=stroke_results,
        phonemes=phonemes,
        candidates=candidates,
        phrase_text=phrase_result.phrase_text if phrase_result.is_phrase else None,
        phrase_confidence=phrase_result.confidence if phrase_result.is_phrase else 0.0,
        transcript=[candidates[0]["word"]] if candidates else [],
    )
