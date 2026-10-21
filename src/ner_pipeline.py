import os
from typing import Any, Dict, List
import spacy

MODEL_DIR = "models/trained_ner"

class NERPipeline:
    def __init__(self, model_path: str = MODEL_DIR):
        if os.path.exists(model_path):
            self.model_name = model_path
            self.nlp = spacy.load(model_path)
        else:
            self.model_name = "en_core_web_sm"
            self.nlp = spacy.load("en_core_web_sm")

    def combine_text(self, title: str, body: str) -> str:
        clean_title = title.strip()
        clean_body = body.strip()
        if not clean_title.endswith((".", "!", "?")):
            return f"{clean_title}. {clean_body}"
        return f"{clean_title} {clean_body}"

    def extract(self, title: str, body: str) -> Dict[str, Any]:
        combined_text = self.combine_text(title, body)
        doc = self.nlp(combined_text)

        entities: List[Dict[str, Any]] = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })

        return {
            "entities": entities,
            "meta": {
                "entity_count": len(entities),
                "model": self.model_name,
                "combined_length": len(combined_text)
            }
        }
