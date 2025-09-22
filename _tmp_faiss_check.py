import faiss

idx = faiss.read_index("indices/index.faiss")
print("faiss_ntotal", idx.ntotal)
