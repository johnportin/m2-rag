import json

from src.m2rag.ingest.extract import parse_all_docs


def main():
    docs, warn_count = parse_all_docs("data/macaulay2docs", with_stats=True)
    print(f"Parsed {len(docs)} documentation entries.")
    with open("data/m2_docs.jsonl", "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print("Saved to m2_docs.jsonl")
    if warn_count:
        print(f"[WARN] {warn_count} entries missing headline/description")
    else:
        print("[OK] No missing headline/description entries")


if __name__ == "__main__":
    main()
