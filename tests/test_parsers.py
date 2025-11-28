from src.m2rag.ingest.extract import parse_m2_file
from src.m2rag.ingest.reader import M2File


def test_doc_and_document_parsing():
    content = """doc///
Key
  HashTable
Headline
  the class of all hash tables
Usage
  hashTable x
Description
  Text
    A hash table consists of keys and values.
Example
  example content
SeeAlso
  foo
///

document {
    Key => "hash tables",
    Headline => "a hash table overview",
    Usage => "hash tables",
    Description => "hash description",
    SeeAlso => {foo, bar},
}
"""
    docs = parse_m2_file(M2File(path="test.m2", content=content))
    assert len(docs) == 2

    doc_entry = docs[0]
    assert doc_entry["keys"] == ["HashTable"]
    assert "hash table consists" in doc_entry["description"]
    assert doc_entry["headline"] == "the class of all hash tables"
    assert doc_entry["syntax"] == "doc"

    document_entry = docs[1]
    assert document_entry["headline"] == "a hash table overview"
    assert document_entry["keys"] == ["hash tables"]
    assert document_entry["syntax"] == "document"
