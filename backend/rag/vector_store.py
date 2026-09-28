from pathlib import Path
from backend.config.settings import get_settings
_collection=None
def collection():
    global _collection
    if _collection is not None:return _collection
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        s=get_settings(); Path(s.chroma_path).mkdir(parents=True,exist_ok=True)
        client=chromadb.PersistentClient(path=s.chroma_path)
        ef=embedding_functions.SentenceTransformerEmbeddingFunction(model_name=s.embedding_model)
        _collection=client.get_or_create_collection('trusted_sources',embedding_function=ef)
        return _collection
    except Exception:return None
