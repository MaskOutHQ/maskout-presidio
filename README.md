# presidio-service

A FastAPI microservice that detects and redacts PII (Personally Identifiable Information) using [Microsoft Presidio](https://github.com/microsoft/presidio).

## Detected Entity Types

| Entity | Example |
|---|---|
| PERSON | John Smith |
| EMAIL_ADDRESS | john@example.com |
| PHONE_NUMBER | (555) 867-5309 |
| US_SSN | 123-45-6789 |
| CREDIT_CARD | 4111 1111 1111 1111 |
| US_DRIVER_LICENSE | A1234567 |
| STREET_ADDRESS | 123 Main St, Seattle WA |
| DATE_TIME | January 1, 1990 |
| IP_ADDRESS | 192.168.1.1 |
| MEDICAL_LICENSE | MD123456 |
| US_PASSPORT | 123456789 |
| IBAN_CODE | GB29NWBK60161331926819 |

Only entities with a confidence score ≥ 0.4 are returned.

## Endpoints

### `GET /health`
Returns `{"status": "healthy"}`.

### `POST /analyze`
Analyze a single text block.

**Request**
```json
{ "text": "My name is John Smith and my email is john@example.com" }
```

**Response**
```json
{
  "entities": [
    { "type": "PERSON", "text": "John Smith", "start": 11, "end": 21, "confidence_score": 0.85 },
    { "type": "EMAIL_ADDRESS", "text": "john@example.com", "start": 38, "end": 54, "confidence_score": 1.0 }
  ],
  "redacted_text": "My name is [REDACTED] and my email is [REDACTED]"
}
```

### `POST /analyze-batch`
Analyze up to 100 text blocks in one call.

**Request**
```json
{ "texts": ["Text one...", "Text two..."] }
```

**Response**
```json
{ "results": [ { "entities": [...], "redacted_text": "..." }, ... ] }
```

## Local Development

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_lg
uvicorn main:app --reload --port 8080
```

## Docker

```bash
docker build -t presidio-service .
docker run -p 8080:8080 presidio-service
```

## Railway Deployment

Point Railway to the `presidio-service/Dockerfile` via `railway.json` at the repo root, or configure the build path in the Railway dashboard.
