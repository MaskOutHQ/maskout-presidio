from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

app = FastAPI(title="Presidio PII Detection Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.lovable.app",
        "https://*.lovableproject.com",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ],
    allow_origin_regex=r"https://.*\.lovable\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Presidio engines once at startup
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

SUPPORTED_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_SSN",
    "CREDIT_CARD",
    "US_DRIVER_LICENSE",
    "STREET_ADDRESS",
    "DATE_TIME",
    "IP_ADDRESS",
    "MEDICAL_LICENSE",
    "US_PASSPORT",
    "IBAN_CODE",
]

CONFIDENCE_THRESHOLD = 0.4


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeBatchRequest(BaseModel):
    texts: List[str]


class DetectedEntity(BaseModel):
    type: str
    text: str
    start: int
    end: int
    confidence_score: float


class AnalyzeResponse(BaseModel):
    entities: List[DetectedEntity]
    redacted_text: str


class AnalyzeBatchResponse(BaseModel):
    results: List[AnalyzeResponse]


def analyze_text(text: str) -> AnalyzeResponse:
    """Run PII detection on a single text block."""
    if not text or not text.strip():
        return AnalyzeResponse(entities=[], redacted_text=text)

    # Detect PII
    results = analyzer.analyze(
        text=text,
        entities=SUPPORTED_ENTITIES,
        language="en",
    )

    # Filter by confidence threshold
    filtered = [r for r in results if r.score >= CONFIDENCE_THRESHOLD]

    # Build entity list with original text spans
    entities = [
        DetectedEntity(
            type=r.entity_type,
            text=text[r.start:r.end],
            start=r.start,
            end=r.end,
            confidence_score=round(r.score, 4),
        )
        for r in filtered
    ]

    # Redact text — replace every detected PII span with [REDACTED]
    if filtered:
        anonymized = anonymizer.anonymize(
            text=text,
            analyzer_results=filtered,
            operators={
                entity: OperatorConfig("replace", {"new_value": "[REDACTED]"})
                for entity in SUPPORTED_ENTITIES
            },
        )
        redacted_text = anonymized.text
    else:
        redacted_text = text

    return AnalyzeResponse(entities=entities, redacted_text=redacted_text)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    try:
        return analyze_text(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-batch", response_model=AnalyzeBatchResponse)
def analyze_batch(request: AnalyzeBatchRequest):
    if not request.texts:
        raise HTTPException(status_code=400, detail="texts array must not be empty")
    if len(request.texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per batch")

    try:
        results = [analyze_text(text) for text in request.texts]
        return AnalyzeBatchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
