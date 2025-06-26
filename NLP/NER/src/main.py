import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans
import os
from pathlib import Path
from data.train_data import TRAIN_DATA


def create_training_data(data, output_path="train.spacy"):
    nlp = spacy.blank("en")
    doc_bin = DocBin()

    for text, annot in data:
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in annot["entities"]:
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span:
                ents.append(span)
        doc.ents = filter_spans(ents)
        doc_bin.add(doc)

    doc_bin.to_disk(output_path)
    print(f"✅ Training data saved to {output_path}")

def init_config():
    print("📄 Creating spaCy config file...")
    os.system("python -m spacy init config config.cfg --lang en --pipeline ner --optimize efficiency")
    print("✅ Config file created")

def train_model():
    print("🚀 Starting training...")
    # Create models directory if it doesn't exist
    models_dir = Path("new_NLP_model")
    models_dir.mkdir(exist_ok=True)
    
    
    os.system("python -m spacy train config.cfg --output ./new_NLP_model --paths.train ./train.spacy --paths.dev ./train.spacy --nlp.batch_size 100 --training.max_epochs 100")
    print("✅ Model saved to new_NLPmodel")

if __name__ == "__main__":
    create_training_data(TRAIN_DATA)
    # init_config()
    train_model()
