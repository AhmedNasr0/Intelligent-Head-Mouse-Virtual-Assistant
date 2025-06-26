import spacy
from pathlib import Path

model_path = Path(__file__).resolve().parent.parent.parent / "models" / "new_NLP_model" / "model-best"
print(model_path)

class NERUsernameService:
    def __init__(self):
        self.nlp = spacy.load(model_path)

    def extract_username(self, sentence: str) -> str:
        doc = self.nlp(sentence)
        return doc.ents[0].text if doc.ents else None
