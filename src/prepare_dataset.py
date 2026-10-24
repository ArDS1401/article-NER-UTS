import json
import os
import random
import spacy
from spacy.tokens import DocBin

RAW_ARTICLES = [
    {
        "id": "art_001",
        "title": "UOB Malaysia and Maybank complete landmark transaction",
        "body": "UOB Malaysia, RHB Banking Group and Maybank completed a financial transaction in Kuala Lumpur on Monday. Chief Executive Officer Khairussaleh Ramli stated that Maybank remains committed to digital transformation in Malaysia.",
        "mentions": [
            ("UOB Malaysia", "ORG"),
            ("RHB Banking Group", "ORG"),
            ("Maybank", "ORG"),
            ("Kuala Lumpur", "GPE"),
            ("Monday", "DATE"),
            ("Khairussaleh Ramli", "PERSON"),
            ("Malaysia", "GPE")
        ]
    },
    {
        "id": "art_002",
        "title": "CIMB Group launches sustainability initiative",
        "body": "CIMB Group Holdings Berhad announced a regional initiative across Southeast Asia. Group CEO Novan Amirudin presented the framework at Menara CIMB in Petaling Jaya.",
        "mentions": [
            ("CIMB Group Holdings Berhad", "ORG"),
            ("CIMB Group", "ORG"),
            ("Southeast Asia", "LOC"),
            ("Novan Amirudin", "PERSON"),
            ("Menara CIMB", "LOC"),
            ("Petaling Jaya", "GPE")
        ]
    },
    {
        "id": "art_003",
        "title": "Public Bank partners with fintech start-up",
        "body": "Public Bank Berhad partnered with local firms to modernize online payments in Selangor. The banking group will expand services by December 2026.",
        "mentions": [
            ("Public Bank Berhad", "ORG"),
            ("Public Bank", "ORG"),
            ("Selangor", "GPE"),
            ("December 2026", "DATE")
        ]
    },
    {
        "id": "art_004",
        "title": "Bank Negara Malaysia issues updated regulatory guidelines",
        "body": "Bank Negara Malaysia released fresh guidelines for commercial banks in Putrajaya yesterday. Governor Abdul Rasheed Ghaffour emphasized consumer protection.",
        "mentions": [
            ("Bank Negara Malaysia", "ORG"),
            ("Putrajaya", "GPE"),
            ("yesterday", "DATE"),
            ("Abdul Rasheed Ghaffour", "PERSON")
        ]
    },
    {
        "id": "art_005",
        "title": "Bursa Malaysia closes higher amid positive sentiment",
        "body": "Bursa Malaysia closed higher on Friday driven by strong banking stocks including Hong Leong Bank and Maybank.",
        "mentions": [
            ("Bursa Malaysia", "ORG"),
            ("Friday", "DATE"),
            ("Hong Leong Bank", "ORG"),
            ("Maybank", "ORG")
        ]
    },
    {
        "id": "art_006",
        "title": "Tech startup MDV secures government grant in Cyberjaya",
        "body": "Malaysia Debt Ventures or MDV obtained new capital in Cyberjaya to back renewable technology ventures.",
        "mentions": [
            ("Malaysia Debt Ventures", "ORG"),
            ("MDV", "ORG"),
            ("Cyberjaya", "GPE")
        ]
    },
    {
        "id": "art_007",
        "title": "Maybank Foundation supports local community development",
        "body": "Maybank Foundation launched an educational workshop in Penang led by Shahril Azuar Jimin. The project will continue until November 2026.",
        "mentions": [
            ("Maybank Foundation", "ORG"),
            ("Penang", "GPE"),
            ("Shahril Azuar Jimin", "PERSON"),
            ("November 2026", "DATE")
        ]
    },
    {
        "id": "art_008",
        "title": "Hong Leong Bank expands digital wealth solutions",
        "body": "Hong Leong Bank revealed its new automated investment portal for young retail investors across Malaysia.",
        "mentions": [
            ("Hong Leong Bank", "ORG"),
            ("Malaysia", "GPE")
        ]
    },
    {
        "id": "art_009",
        "title": "Quarterly financial review highlights resilience in banking sector",
        "body": "Operating margins showed stable recovery across institutional lenders during third quarter evaluations.",
        "mentions": []
    },
    {
        "id": "art_010",
        "title": "General market overview and liquidity conditions",
        "body": "Interbank lending rates remained within normal ranges with strong participation in overnight deposits.",
        "mentions": []
    },
    {
        "id": "art_011",
        "title": "S&P Global upgrades credit outlook for Malaysian financial sector",
        "body": "S&P Global Ratings revised its rating outlook for major lenders in Kuala Lumpur including RHB Bank Berhad.",
        "mentions": [
            ("S&P Global Ratings", "ORG"),
            ("S&P Global", "ORG"),
            ("Malaysian", "LOC"),
            ("Kuala Lumpur", "GPE"),
            ("RHB Bank Berhad", "ORG")
        ]
    },
    {
        "id": "art_012",
        "title": "Finance Minister Anwar Ibrahim addresses regional summit",
        "body": "Prime Minister and Finance Minister Anwar Ibrahim delivered keynote remarks in Jakarta, Indonesia regarding bilateral trade agreements.",
        "mentions": [
            ("Anwar Ibrahim", "PERSON"),
            ("Jakarta", "GPE"),
            ("Indonesia", "GPE")
        ]
    },
    {
        "id": "art_013",
        "title": "Maybank Islamic issues new sukuk framework",
        "body": "Maybank Islamic Berhad completed a Shariah-compliant issuance supported by institutional investors in Johor Bahru.",
        "mentions": [
            ("Maybank Islamic Berhad", "ORG"),
            ("Maybank Islamic", "ORG"),
            ("Johor Bahru", "GPE")
        ]
    },
    {
        "id": "art_014",
        "title": "Securities Commission Malaysia publishes fintech roadmap",
        "body": "Securities Commission Malaysia announced updated tokenization standards for capital markets in Mont Kiara.",
        "mentions": [
            ("Securities Commission Malaysia", "ORG"),
            ("Mont Kiara", "LOC")
        ]
    },
    {
        "id": "art_015",
        "title": "Axiata and Digi finalize digital infrastructure consolidation",
        "body": "CelcomDigi Berhad confirmed network expansion milestones in Subang Jaya following integration meetings.",
        "mentions": [
            ("CelcomDigi Berhad", "ORG"),
            ("Axiata", "ORG"),
            ("Digi", "ORG"),
            ("Subang Jaya", "GPE")
        ]
    }
]

def auto_align_spans(title: str, body: str, mentions):
    full_text = f"{title}. {body}" if not title.strip().endswith((".", "!", "?")) else f"{title.strip()} {body.strip()}"
    found_spans = []

    for text_span, label in mentions:
        start_idx = 0
        while True:
            idx = full_text.find(text_span, start_idx)
            if idx == -1:
                break
            found_spans.append({
                "text": text_span,
                "label": label,
                "start": idx,
                "end": idx + len(text_span)
            })
            start_idx = idx + len(text_span)

    # Sort and remove overlapping spans
    found_spans = sorted(found_spans, key=lambda x: (x["start"], -(x["end"] - x["start"])))
    non_overlapping = []
    last_end = -1
    for span in found_spans:
        if span["start"] >= last_end:
            non_overlapping.append(span)
            last_end = span["end"]

    return full_text, non_overlapping

def make_doc_bin(nlp, dataset):
    doc_bin = DocBin()
    total_added = 0
    total_dropped = 0
    for item in dataset:
        doc = nlp.make_doc(item["combined_text"])
        ents = []
        for ent in item["entities"]:
            span = doc.char_span(ent["start"], ent["end"], label=ent["label"])
            if span is not None:
                ents.append(span)
                total_added += 1
            else:
                total_dropped += 1
        doc.ents = ents
        doc_bin.add(doc)
    print(f"Entities added: {total_added}, dropped: {total_dropped}")
    return doc_bin

def main():
    random.seed(42)
    processed_articles = []
    for item in RAW_ARTICLES:
        combined_text, entities = auto_align_spans(item["title"], item["body"], item["mentions"])
        processed_articles.append({
            "id": item["id"],
            "title": item["title"],
            "body": item["body"],
            "combined_text": combined_text,
            "entities": entities
        })

    shuffled = list(processed_articles)
    random.shuffle(shuffled)

    n_total = len(shuffled)
    n_train = int(n_total * 0.70)
    n_val = int(n_total * 0.15)

    train_data = shuffled[:n_train]
    val_data = shuffled[n_train:n_train + n_val]
    test_data = shuffled[n_train + n_val:]

    nlp = spacy.blank("en")
    os.makedirs("data/processed", exist_ok=True)

    print("Building train.spacy:")
    train_bin = make_doc_bin(nlp, train_data)
    train_bin.to_disk("data/processed/train.spacy")

    print("Building dev.spacy:")
    val_bin = make_doc_bin(nlp, val_data)
    val_bin.to_disk("data/processed/dev.spacy")

    print("Building test.spacy:")
    test_bin = make_doc_bin(nlp, test_data)
    test_bin.to_disk("data/processed/test.spacy")

    with open("evaluation_examples.json", "w", encoding="utf-8") as f:
        json.dump(processed_articles[:10], f, indent=2)

    print(f"\nCompleted: {n_total} articles split into {len(train_data)} train, {len(val_data)} dev, {len(test_data)} test.")

if __name__ == "__main__":
    main()
