from pydantic import BaseModel

class ScoreRequest(BaseModel):
    jd_text: str
    candidate_text: str
    role: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "jd_text": "We are hiring a Senior Product Designer with Figma expertise.",
                    "candidate_text": "Alice Smith, 5 years in UX/UI, expert in Figma and prototyping.",
                    "role": "product-designer"
                }
            ]
        }
    }

class ScoreResponse(BaseModel):
    candidate_id: str
    fit_score: float
    rationale: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "candidate_id": "alice-smith",
                    "fit_score": 82.5,
                    "rationale": "Candidate has 5 years in UX/UI and strong Figma skills."
                }
            ]
        }
    }