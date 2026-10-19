import os
import random
import spacy
from spacy.scorer import Scorer
from spacy.tokens import DocBin
from spacy.training import Example

def load_docbin_examples(nlp_model, docbin_path):
    doc_bin = DocBin().from_disk(docbin_path)
    docs = list(doc_bin.get_docs(nlp_model.vocab))
    examples = []
    for doc in docs:
        entities = [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]
        pred_doc = nlp_model.make_doc(doc.text)
        example = Example.from_dict(pred_doc, {"entities": entities})
        examples.append(example)
    return examples

def evaluate_pipeline(nlp_model, examples):
    scorer = Scorer()
    evaluated_examples = []
    for eg in examples:
        pred_doc = nlp_model(eg.predicted.text)
        evaluated_examples.append(Example(pred_doc, eg.reference))
    scores = scorer.score(evaluated_examples)
    return {
        "p": scores.get("ents_p", 0.0),
        "r": scores.get("ents_r", 0.0),
        "f": scores.get("ents_f", 0.0),
        "per_type": scores.get("ents_per_type", {})
    }

def print_scores(name, metrics):
    print(f"\n--- {name} ---")
    print(f"Overall Precision : {metrics['p']:.4f}")
    print(f"Overall Recall    : {metrics['r']:.4f}")
    print(f"Overall F1 Score  : {metrics['f']:.4f}")
    print("Per-entity breakdown:")
    for label, val in metrics["per_type"].items():
        print(f"  [{label}] P: {val['p']:.2f} | R: {val['r']:.2f} | F1: {val['f']:.2f}")

def main():
    random.seed(42)
    os.makedirs("models", exist_ok=True)

    print("Loading pretrained baseline: en_core_web_sm...")
    nlp = spacy.load("en_core_web_sm")

    test_examples = load_docbin_examples(nlp, "data/processed/test.spacy")
    train_examples = load_docbin_examples(nlp, "data/processed/train.spacy")

    print("\n[1/3] Evaluating Pretrained Baseline on Test Split...")
    baseline_metrics = evaluate_pipeline(nlp, test_examples)
    print_scores("BASELINE (en_core_web_sm)", baseline_metrics)

    print("\n[2/3] Fine-tuning NER component on Malaysian financial news...")
    ner = nlp.get_pipe("ner")
    for eg in train_examples:
        for ent in eg.reference.ents:
            ner.add_label(ent.label_)

    pipe_exceptions = ["ner", "tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]

    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.resume_training()
        epochs = 20
        for epoch in range(epochs):
            random.shuffle(train_examples)
            losses = {}
            for eg in train_examples:
                nlp.update([eg], drop=0.2, sgd=optimizer, losses=losses)
            if (epoch + 1) % 5 == 0 or epoch == epochs - 1:
                print(f"Epoch {epoch + 1:02d}/{epochs:02d} - Loss: {losses.get('ner', 0.0):.4f}")

    print("\n[3/3] Evaluating Fine-tuned Model on Test Split...")
    adapted_metrics = evaluate_pipeline(nlp, test_examples)
    print_scores("ADAPTED MODEL (models/trained_ner)", adapted_metrics)

    output_dir = "models/trained_ner"
    nlp.to_disk(output_dir)
    print(f"\nTrained model successfully saved to: {output_dir}")

if __name__ == "__main__":
    main()
