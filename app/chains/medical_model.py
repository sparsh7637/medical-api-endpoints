from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.chains.prompts import SYSTEM_MEDICAL, PRESCRIPTION_EXTRACTION_INSTRUCTIONS, QUERY_ASSISTANT_INSTRUCTIONS
from app.models.ii_medical_loader import build_ii_medical_runnable

summarize_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_MEDICAL),
    ("user", "{instructions}\n\nOCR_TEXT:\n{ocr}")
])
summarize_chain = summarize_prompt | build_ii_medical_runnable() | StrOutputParser()

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_MEDICAL),
    ("user", "{instructions}\n\nQUESTION:\n{query}\n\nOPTIONAL_CONTEXT:\n{context}")
])
qa_chain = qa_prompt | build_ii_medical_runnable() | StrOutputParser()

def run_summarize(ocr_text: str) -> str:
    return summarize_chain.invoke({
        "instructions": PRESCRIPTION_EXTRACTION_INSTRUCTIONS,
        "ocr": ocr_text,
    })

def run_qa(query: str, context: str = "") -> str:
    return qa_chain.invoke({
        "instructions": QUERY_ASSISTANT_INSTRUCTIONS,
        "query": query,
        "context": context or "",
    })
