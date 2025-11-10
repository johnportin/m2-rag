from pydantic import BaseModel
from minsearch import Index
from src.db.index import create_index

index: Index = create_index("data/m2_docs.jsonl")

class SearchDocsArgs(BaseModel):
    query: str
    k: int = 5

def search_docs(args: SearchDocsArgs) -> list[dict]:
    return index.search(args.query, num_results=args.k)
