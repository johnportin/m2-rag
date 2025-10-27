from extract_docs import parse_all_docs
import json

if __name__ == "__main__":
    docs = parse_all_docs("data/macaulay2docs")
    print(f"Parsed {len(docs)} documentation entries.")
    with open("data/m2_docs.jsonl", "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print("Saved to m2_docs.jsonl")