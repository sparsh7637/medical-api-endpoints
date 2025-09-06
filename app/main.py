from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.logging_conf import logger
from app.chains.schemas import (
    SummarizeRequest, SummarizeResponse, PrescriptionSummary,
    AnswerQueryRequest, AnswerQueryResponse
)
from app.chains.safety import prefilter, safety_footer
from app.chains.medical_model import run_summarize, run_qa
from app.chains.gpt_refiner import refine_text
from app.chains import retrieval as med_retrieval
from app.utils.json_extract import extract_first_json  # <-- NEW: robust JSON extractor
import json

app = FastAPI(title="Medical Assistant API (LangChain via HF Endpoints)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/summarize-prescription", response_model=SummarizeResponse)
async def summarize_prescription(payload: SummarizeRequest):
    ok, msg = prefilter(payload.text)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    try:
        llm_json = run_summarize(payload.text)

        # --- Hardened parsing: accept pure JSON or salvage from fenced/wrapped output ---
        try:
            data = extract_first_json(llm_json)
        except Exception as e:
            logger.error(f"JSON parse failed: {e}; raw=\n{llm_json}")
            raise HTTPException(status_code=502, detail="Model returned invalid JSON")

        # Ensure disclaimer is always present
        data.setdefault("disclaimer", safety_footer()["disclaimer"])

        # Pydantic validation of the final structure
        validated = PrescriptionSummary(**data)
        return SummarizeResponse(summary=validated)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal error during summarization")

@app.post("/answer-query", response_model=AnswerQueryResponse)
async def answer_query(payload: AnswerQueryRequest):
    ok, msg = prefilter(payload.query)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    try:
        context_snippets = med_retrieval.search(payload.query)
        context = "\n".join(context_snippets)
        draft = run_qa(payload.query, context=context)
        refined = refine_text(draft)
        safety = safety_footer()
        return AnswerQueryResponse(answer=refined.strip(), safety=safety, sources=context_snippets)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal error during Q&A")
