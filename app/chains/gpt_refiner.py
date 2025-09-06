from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.models.gpt_ss_loader import build_gpt_ss_runnable
from app.chains.prompts import REFINER_SYSTEM

refine_prompt = ChatPromptTemplate.from_messages([
    ("system", REFINER_SYSTEM),
    ("user", "Please refine the following for a patient in India. Keep medical facts intact, simplify language, and include a short disclaimer.\n\nINPUT:\n{draft}")
])
refine_chain = refine_prompt | build_gpt_ss_runnable() | StrOutputParser()

def refine_text(draft: str) -> str:
    return refine_chain.invoke({"draft": draft})
