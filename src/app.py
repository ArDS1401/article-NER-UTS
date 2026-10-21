import os
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from src.ner_pipeline import NERPipeline

app = FastAPI(title="Article NER Service", version="1.0.0")

pipeline = NERPipeline()

MAX_CHAR_LIMIT = 10000

class ArticleRequest(BaseModel):
    title: str = Field(..., max_length=MAX_CHAR_LIMIT)
    body: str = Field(..., max_length=MAX_CHAR_LIMIT)

    @field_validator("title", "body")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Field must be a string")
        stripped = value.strip()
        if len(stripped) == 0:
            raise ValueError("Field cannot be empty or blank")
        return stripped

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Invalid input format or validation error", "errors": exc.errors()}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "NER API running. Visit /docs for OpenAPI specs."}

@app.post("/extract-entities")
async def extract_entities(payload: ArticleRequest):
    try:
        results = pipeline.extract(payload.title, payload.body)
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(exc)}"
        )
