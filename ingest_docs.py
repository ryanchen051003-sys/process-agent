from retrieve import ingest_docs

if __name__ == "__main__":
    n = ingest_docs()
    print(f"ingested {n} chunks from docs/")
