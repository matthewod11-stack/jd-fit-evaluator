from jd_fit_evaluator.models.llm import get_llm

def normalize_titles_and_skills(titles: list[str], skills: list[str]) -> dict[str, list[str]]:
    llm = get_llm()
    resp = llm.chat_json(
        "Normalize titles and consolidate skills",
        f"Titles: {titles}\nSkills: {skills}\nReturn JSON: {{'normalized_titles': [...], 'skills': [...]}}",
        schema_hint="norm"
    )
    return resp.parsed_json or {"normalized_titles": titles, "skills": skills}