from jd_fit_evaluator.models.llm import get_llm

def generate_rationale(role: str, signals_json: str, evidence: str) -> str:
    llm = get_llm()
    resp = llm.chat_json(
        "Hiring screener rationale",
        f"Role: {role}\nSignals: {signals_json}\nEvidence: {evidence}\nWrite 3–6 sentences citing evidence.",
    )
    return resp.text.strip()