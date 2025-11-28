def search_docs(query, k=5):
    qvec = model.encode(query, normalize_embeddings=True)
    D, I = index.search(np.array([qvec], dtype="float32"), k)
    return [metadata[i] for i in I[0]]
