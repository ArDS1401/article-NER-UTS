import json
import os
import random
import spacy
from spacy.tokens import DocBin

RAW_ANNOTATIONS = [
    {
        "id": "art_001",
        "title": "UOB Malaysia and Maybank complete landmark transaction",
        "body": "UOB Malaysia, RHB Banking Group and Maybank completed a financial transaction in Kuala Lumpur on Monday. Chief Executive Officer Khairussaleh Ramli stated that Maybank remains committed to digital transformation in Malaysia.",
        "entities": [
            {"text": "UOB Malaysia", "label": "ORG", "start": 0, "end": 12},
            {"text": "Maybank", "label": "ORG", "start": 17, "end": 24},
            {"text": "UOB Malaysia", "label": "ORG", "start": 57, "end": 69},
            {"text": "RHB Banking Group", "label": "ORG", "start": 71, "end": 88},
            {"text": "Maybank", "label": "ORG", "start": 93, "end": 100},
            {"text": "Kuala Lumpur", "label": "GPE", "start": 139, "end": 151},
            {"text": "Monday", "label": "DATE", "start": 155, "end": 161},
            {"text": "Khairussaleh Ramli", "label": "PERSON", "start": 188, "end": 206},
            {"text": "Maybank", "label": "ORG", "start": 220, "end": 227},
            {"text": "Malaysia", "label": "GPE", "start": 264, "end": 272}
        ]
    },
    {
        "id": "art_002",
        "title": "CIMB Group launches sustainability initiative",
        "body": "CIMB Group Holdings Berhad announced a regional initiative across Southeast Asia. Group CEO Novan Amirudin presented the framework at Menara CIMB in Petaling Jaya.",
        "entities": [
            {"text": "CIMB Group", "label": "ORG", "start": 0, "end": 10},
            {"text": "CIMB Group Holdings Berhad", "label": "ORG", "start": 47, "end": 73},
            {"text": "Southeast Asia", "label": "LOC", "start": 113, "end": 127},
            {"text": "Novan Amirudin", "label": "PERSON", "start": 139, "end": 153},
            {"text": "Menara CIMB", "label": "LOC", "start": 181, "end": 192},
            {"text": "Petaling Jaya", "label": "GPE", "start": 196, "end": 209}
        ]
    },
    {
        "id": "art_003",
        "title": "Public Bank partners with fintech start-up",
        "body": "Public Bank Berhad partnered with local firms to modernize online payments in Selangor. The banking group will expand services by December 2026.",
        "entities": [
            {"text": "Public Bank", "label": "ORG", "start": 0, "end": 11},
            {"text": "Public Bank Berhad", "label": "ORG", "start": 44, "end": 62},
            {"text": "Selangor", "label": "GPE", "start": 119, "end": 127},
            {"text": "December 2026", "label": "DATE", "start": 171, "end": 184}
        ]
    },
    {
        "id": "art_004",
        "title": "Bank Negara Malaysia issues updated regulatory guidelines",
        "body": "Bank Negara Malaysia released fresh guidelines for commercial banks in Putrajaya yesterday. Governor Abdul Rasheed Ghaffour emphasized consumer protection.",
        "entities": [
            {"text": "Bank Negara Malaysia", "label": "ORG", "start": 0, "end": 20},
            {"text": "Bank Negara Malaysia", "label": "ORG", "start": 58, "end": 78},
            {"text": "Putrajaya", "label": "GPE", "start": 127, "end": 136},
            {"text": "Abdul Rasheed Ghaffour", "label": "PERSON", "start": 157, "end": 179}
        ]
    },
    {
        "id": "art_005",
        "title": "Bursa Malaysia closes higher amid positive sentiment",
        "body": "Bursa Malaysia closed higher on Friday driven by strong banking stocks including Hong Leong Bank and Maybank.",
        "entities": [
            {"text": "Bursa Malaysia", "label": "ORG", "start": 0, "end": 14},
            {"text": "Bursa Malaysia", "label": "ORG", "start": 52, "end": 66},
            {"text": "Friday", "label": "DATE", "start": 84, "end": 90},
            {"text": "Hong Leong Bank", "label": "ORG", "start": 132, "end": 147},
            {"text": "Maybank", "label": "ORG", "start": 152, "end": 159}
        ]
    },
    {
        "id": "art_006",
        "title": "Tech startup MDV secures government grant in Cyberjaya",
        "body": "Malaysia Debt Ventures or MDV obtained new capital in Cyberjaya to back renewable technology ventures.",
        "entities": [
            {"text": "MDV", "label": "ORG", "start": 13, "end": 16},
            {"text": "Cyberjaya", "label": "GPE", "start": 44, "end": 53},
            {"text": "Malaysia Debt Ventures", "label": "ORG", "start": 55, "end": 77},
            {"text": "MDV", "label": "ORG", "start": 81, "end": 84},
            {"text": "Cyberjaya", "label": "GPE", "start": 107, "end": 116}
        ]
    },
    {
        "id": "art_007",
        "title": "Maybank Foundation supports local community development",
        "body": "Maybank Foundation launched an educational workshop in Penang led by Shahril Azuar Jimin. The project will continue until November 2026.",
        "entities": [
            {"text": "Maybank Foundation", "label": "ORG", "start": 0, "end": 18},
            {"text": "Maybank Foundation", "label": "ORG", "start": 56, "end": 74},
            {"text": "Penang", "label": "GPE", "start": 110, "end": 116},
            {"text": "Shahril Azuar Jimin", "label": "PERSON", "start": 124, "end": 143},
            {"text": "November 2026", "label": "DATE", "start": 178, "end": 191}
        ]
    },
    {
        "id": "art_008",
        "title": "Hong Leong Bank expands digital wealth solutions",
        "body": "Hong Leong Bank revealed its new automated investment portal for young retail investors across Malaysia.",
        "entities": [
            {"text": "Hong Leong Bank", "label": "ORG", "start": 0, "end": 15},
            {"text": "Hong Leong Bank", "label": "ORG", "start": 50, "end": 65},
            {"text": "Malaysia", "label": "GPE", "start": 144, "end": 152}
        ]
    },
    {
        "id": "art_009",
        "title": "Quarterly financial review highlights resilience in banking sector",
        "body": "Operating margins showed stable recovery across institutional lenders during third quarter evaluations.",
        "entities": []
    },
    {
        "id": "art_010",
        "title": "General market overview and liquidity conditions",
        "body": "Interbank lending rates remained within normal ranges with strong participation in overnight deposits.",
        "entities": []
    },
    {
        "id": "art_011",
        "title": "S&P Global upgrades credit outlook for Malaysian financial sector",
        "body": "S&P Global Ratings revised its rating outlook for major lenders in Kuala Lumpur including RHB Bank Berhad.",
        "entities": [
            {"text": "S&P Global", "label": "ORG", "start": 0, "end": 10},
            {"text": "Malaysian", "label": "LOC", "start": 39, "end": 48},
            {"text": "S&P Global Ratings", "label": "ORG", "start": 67, "end": 85},
            {"text": "Kuala Lumpur", "label": "GPE", "start": 133, "end": 145},
            {"text": "RHB Bank Berhad", "label": "ORG", "start": 156, "end": 171}
        ]
    },
    {
        "id": "art_012",
        "title": "Finance Minister Anwar Ibrahim addresses regional summit",
        "body": "Prime Minister and Finance Minister Anwar Ibrahim delivered keynote remarks in Jakarta, Indonesia regarding bilateral trade agreements.",
        "entities": [
            {"text": "Anwar Ibrahim", "label": "PERSON", "start": 17, "end": 30},
            {"text": "Anwar Ibrahim", "label": "PERSON", "start": 92, "end": 105},
            {"text": "Jakarta", "label": "GPE", "start": 135, "end": 142},
            {"text": "Indonesia", "label": "GPE", "start": 144, "end": 153}
        ]
    },
    {
        "id": "art_013",
        "title": "Maybank Islamic issues new sukuk framework",
        "body": "Maybank Islamic Berhad completed a Shariah-compliant issuance supported by institutional investors in Johor Bahru.",
        "entities": [
            {"text": "Maybank Islamic", "label": "ORG", "start": 0, "end": 15},
            {"text": "Maybank Islamic Berhad", "label": "ORG", "start": 44, "end": 66},
            {"text": "Johor Bahru", "label": "GPE", "start": 144, "end": 155}
        ]
    },
    {
        "id": "art_014",
        "title": "Securities Commission Malaysia publishes fintech roadmap",
        "body": "Securities Commission Malaysia announced updated tokenization standards for capital markets in Mont Kiara.",
        "entities": [
            {"text": "Securities Commission Malaysia", "label": "ORG", "start": 0, "end": 30},
            {"text": "Securities Commission Malaysia", "label": "ORG", "start": 57, "end": 87},
            {"text": "Mont Kiara", "label": "LOC", "start": 150, "end": 160}
        ]
    },
    {
        "id": "art_015",
        "title": "Axiata and Digi finalize digital infrastructure consolidation",
        "body": "CelcomDigi Berhad confirmed network expansion milestones in Subang Jaya following integration meetings.",
        "entities": [
            {"text": "Axiata", "label": "ORG", "start": 0, "end": 6},
            {"text": "Digi", "label": "ORG", "start": 11, "end": 15},
            {"text": "CelcomDigi Berhad", "label": "ORG", "start": 62, "end": 79},
            {"text": "Subang Jaya", "label": "GPE", "start": 120, "end": 131}
        ]
    }
]

def make_doc_bin(nlp, dataset):
    doc_bin = DocBin()
    for item in dataset:
        full_text = f"{item['title']}. {item['body']}"
        doc = nlp.make_doc(full_text)
        ents = []
        for ent in item["entities"]:
            span = doc.char_span(ent["start"], ent["end"], label=ent["label"])
            if span is not None:
                ents.append(span)
        doc.ents = ents
        doc_bin.add(doc)
    return doc_bin

def main():
    random.seed(42)
    shuffled = list(RAW_ANNOTATIONS)
    random.shuffle(shuffled)

    n_total = len(shuffled)
    n_train = int(n_total * 0.70)
    n_val = int(n_total * 0.15)

    train_data = shuffled[:n_train]
    val_data = shuffled[n_train:n_train + n_val]
    test_data = shuffled[n_train + n_val:]

    nlp = spacy.blank("en")

    os.makedirs("data/processed", exist_ok=True)

    train_bin = make_doc_bin(nlp, train_data)
    train_bin.to_disk("data/processed/train.spacy")

    val_bin = make_doc_bin(nlp, val_data)
    val_bin.to_disk("data/processed/dev.spacy")

    test_bin = make_doc_bin(nlp, test_data)
    test_bin.to_disk("data/processed/test.spacy")

    eval_examples = []
    for item in RAW_ANNOTATIONS[:10]:
        combined_text = f"{item['title']}. {item['body']}"
        eval_examples.append({
            "id": item["id"],
            "title": item["title"],
            "body": item["body"],
            "combined_text": combined_text,
            "entities": item["entities"]
        })

    with open("evaluation_examples.json", "w", encoding="utf-8") as f:
        json.dump(eval_examples, f, indent=2)

    print(f"Total annotated articles: {n_total}")
    print(f"Train split: {len(train_data)}")
    print(f"Validation split: {len(val_data)}")
    print(f"Test split: {len(test_data)}")
    print("Files created: train.spacy, dev.spacy, test.spacy, evaluation_examples.json")

if __name__ == "__main__":
    main()
