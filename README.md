

# 🏥 Medical Assistant API (LangChain + FastAPI + Hugging Face)

This project implements a **microservice-based medical assistant API** that leverages **LangChain** and **Hugging Face-hosted models** to provide two key services:

1. **Summarize medical prescriptions** into structured JSON.
2. **Answer patient queries** in natural, patient-friendly language tailored to the **Indian healthcare context**.

---

## 🚀 Architecture Overview

```mermaid
flowchart TD
    A[User Input] -->|OCR text or query| B[FastAPI Server]
    B -->|/summarize-prescription| C[LangChain Prompt Builder]
    B -->|/answer-query| D[LangChain Prompt Builder]
    
    C --> E[II-Medical-8B Model (HF repo_id)]
    D --> E
    
    E -->|Draft output| F[GPT-SS Refiner (HF repo_id)]
    
    F -->|Refined text| G[Post-processing: Safety + Validation]
    
    G --> H[API Response JSON]
```

### Key Layers

* **FastAPI**: lightweight web microservice, serving endpoints.
* **LangChain**: orchestrates prompt templates, model calls, and output parsing.
* **Models**:

  * [`Intelligent-Internet/II-Medical-8B`](https://huggingface.co/Intelligent-Internet/II-Medical-8B) → medical reasoning.
  * `gpt-ss` (any open-source GPT refiner) → makes responses more natural and patient-friendly.
* **Utilities**:

  * JSON extractor to handle noisy model outputs.
  * Safety filter to block harmful queries.
  * In-code Indian medicine mini-knowledge base.

---

## 📂 Project Structure

```
app/
 ├─ chains/
 │   ├─ prompts.py         # All system + user prompt templates
 │   ├─ schemas.py         # Pydantic models for request/response validation
 │   ├─ safety.py          # Prefilter for unsafe queries, safety footer
 │   ├─ retrieval.py       # In-memory hints for Indian medicines
 │   ├─ medical_model.py   # Chains for summarization and Q&A
 │   └─ gpt_refiner.py     # Refiner chain for patient-friendly answers
 │
 ├─ models/
 │   ├─ ii_medical_loader.py  # II-Medical-8B loader (HF repo_id)
 │   └─ gpt_ss_loader.py      # GPT-SS loader (HF repo_id)
 │
 ├─ utils/
 │   └─ json_extract.py    # Robust JSON extraction utility
 │
 ├─ config.py              # Environment & settings
 ├─ logging_conf.py        # Loguru logger setup
 └─ main.py                # FastAPI entrypoint with endpoints
```

---

## ⚡ Endpoints

### 1. `/health`

**Method:** `GET`
**Purpose:** Simple liveness probe.
**Response:**

```json
{"status":"ok"}
```

---

### 2. `/summarize-prescription`

**Method:** `POST`
**Input:**

```json
{
  "text": "Patient: R Gupta. Dx: URTI. Rx: Azithral 500 OD x 3 days; Dolo 650 SOS fever; Omez 20 OD before breakfast 5d."
}
```

**Process:**

1. Prefilter for unsafe content.
2. Send OCR text + instructions to II-Medical-8B.
3. Parse strict JSON (robust extractor handles noisy wrappers).
4. Validate against `PrescriptionSummary` schema.
5. Add disclaimer if missing.

**Output (sample):**

```json
{
  "summary": {
    "patient_name": "R Gupta",
    "diagnosis_or_complaints": "URTI",
    "medicines": [
      {"name": "Azithral", "dosage": "500 mg", "frequency": "OD", "duration": "3 days", "instructions": null},
      {"name": "Dolo 650", "dosage": "650 mg", "frequency": "SOS", "duration": null, "instructions": "fever"},
      {"name": "Omez", "dosage": "20 mg", "frequency": "OD", "duration": "5 days", "instructions": "before breakfast"}
    ],
    "tests_or_followup": null,
    "red_flags": null,
    "generic_advice": "Complete antibiotic course, follow up if symptoms persist.",
    "disclaimer": "Informational only; not a substitute for professional medical advice."
  }
}
```

---

### 3. `/answer-query`

**Method:** `POST`
**Input:**

```json
{
  "query": "Can I take Dolo 650 with milk?"
}
```

**Process:**

1. Prefilter unsafe text.
2. Retrieve relevant hints from in-code Indian meds DB.
3. Send query + context to II-Medical-8B.
4. Refine draft with GPT-SS into friendly patient-facing language.
5. Attach safety block + sources.

**Output (sample):**

```json
{
  "answer": "You can take Dolo 650 with milk; it does not reduce its effect. It is usually well tolerated. If you have persistent fever or severe symptoms, consult a doctor. For information only; not a substitute for professional medical advice.",
  "safety": {
    "disclaimer": "Informational only; not a substitute for professional medical advice.",
    "emergency": "If this is an emergency in India, call 112 or visit the nearest emergency department.",
    "version": "v1"
  },
  "sources": [
    "Dolo 650 (Paracetamol) – Fever/Pain; typical: 650 mg every 6–8 hours (max 3 g/day)"
  ]
}
```

---

## 🔒 Safety Features

* **Prefilter** blocks dangerous requests (e.g., overdose instructions, self-harm queries).
* **Refiner** simplifies language and ensures disclaimers.
* **Safety footer** adds:

  * Disclaimer
  * India-specific emergency contact (112)
  * Versioning info

---

## 💊 Indian Medicines Knowledge Base

A tiny in-memory dictionary is used to give context for common Indian drugs:

* **Dolo 650 (Paracetamol)** → Fever, pain relief
* **Azithral 500 (Azithromycin)** → Bacterial infections
* **Allegra 120 (Fexofenadine)** → Allergic rhinitis
* **Omez 20 (Omeprazole)** → Acidity/GERD
* **ORS Powder** → Rehydration

This list is not exhaustive but helps ground the model.

---

## ⚙️ Environment Setup

`.env` file:

```ini
HF_TOKEN=hf_xxx_your_token
CORS_ORIGINS=*
APP_HOST=127.0.0.1
APP_PORT=8080
```

Install and run:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Swagger UI: [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)

---

## 📌 Key Notes

* **Independence of Endpoints**:

  * `/summarize-prescription` does *not* automatically feed into `/answer-query`.
  * Q\&A only uses query text + small medicine DB.
  * If needed, you can extend it to use the last summary as context.

* **Hugging Face Integration**:

  * Uses `repo_id` with `HuggingFaceEndpoint` + `ChatHuggingFace`.
  * No local model downloads, only API calls.

* **Robustness**:

  * JSON-extractor utility ensures summaries don’t break when model adds `<think>`/markdown.
  * Stop sequences and strict prompts reduce formatting drift.

---

