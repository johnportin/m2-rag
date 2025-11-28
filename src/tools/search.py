from pydantic import BaseModel

from src.db.emb_index import create_index, EmbeddedDocIndex

index: EmbeddedDocIndex = create_index()


class SearchDocsArgs(BaseModel):
    query: str
    k: int = 5


def search_docs(args: SearchDocsArgs) -> list[dict]:
    return index.search(args.query, k=args.k)
