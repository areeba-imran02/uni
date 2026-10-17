"""Transparent baseline classifier; intentionally not advertised as a trained model."""
KEYWORDS={"computer_science":["python","code","software","debug","program","api","algorithm"],"engineering":["voltage","current","resistance","circuit","load","unit","engineering"],"medical_education":["patient case","symptom","clinical","diagnosis practice","medical simulation"]}
def classify_task(text: str) -> dict:
    low=text.lower(); scores={k:sum(term in low for term in terms) for k,terms in KEYWORDS.items()}
    winner=max(scores,key=scores.get); score=scores[winner]
    return {"label":winner if score else "general_academic", "scores":scores, "method":"transparent keyword baseline", "confidence":"rule match" if score else "no strong keyword match"}
