import json
from minsearch import Index

data_path = "data/m2_docs.jsonl"

def load_data(data_path):
    docs = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            if isinstance(doc.get("keys"), list):
                doc["keys"] = " ".join(doc["keys"])

            # Ensure all text fields are lowercase + strings
            for field in ["keys", "headline", "usage", "description", "examples"]:
                val = doc.get(field, "")
                if val is None:
                    doc[field] = ""
                elif isinstance(val, str):
                    doc[field] = val.lower()
            docs.append(doc)
    return docs

def create_index(data_path: str):
    print("Creating index...")
    docs = load_data(data_path)
    docs = [d for d in docs if d.get("keys") or d.get("usage") or d.get("description")]

    print("Total loaded docs:", len(docs))
    print("Docs w/ keys:", sum(1 for d in docs if d.get("keys")))



    text_fields = [
        "keys",
        "usage",
        "description",
        "headline",
        "examples"
    ]
    keyword_fields = [
        "source"
    ]

    index = Index(
        text_fields=text_fields,
        keyword_fields=keyword_fields
    )
    print(f"Fitting index...")
    index.fit(docs)
    print(f"Fit index with {len(index.docs)} entries.")
    return index


if __name__=="__main__":
    index = create_index(data_path=data_path)
    
    print("vector:", index.search("vector"))
    # print("polynomial:", index.search("polynomial"))
    # print("ring:", index.search("ring"))
    # print("hilbert:", index.search("hilbert"))