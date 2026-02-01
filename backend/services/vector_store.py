import os
import json
import hashlib
from pathlib import Path
import faiss
import numpy as np
from typing import List, Dict, Any, Optional
from loguru import logger
from services.azure_openai import azure_openai_service

class VectorStoreService:
    """Service for module-wise vector storage and retrieval using FAISS."""

    def __init__(self):
        self.dimension = 1536  # Azure OpenAI text-embedding-ada-002 dimension
        self.indices = {} # Map module_id -> faiss index
        self.metadata = {} # Map module_id -> List of metadata dicts

        self._storage_root = Path(os.getenv("VECTOR_STORE_DIR", ""))
        if not str(self._storage_root).strip():
            self._storage_root = Path(__file__).resolve().parent.parent / "data" / "vector_store"
        self._storage_root.mkdir(parents=True, exist_ok=True)

    def _module_key(self, module_id: str) -> str:
        return hashlib.sha256(module_id.encode("utf-8", errors="ignore")).hexdigest()

    def _module_paths(self, module_id: str):
        key = self._module_key(module_id)
        index_path = self._storage_root / f"{key}.faiss"
        meta_path = self._storage_root / f"{key}.json"
        return index_path, meta_path

    def _load_module(self, module_id: str) -> bool:
        if module_id in self.indices and module_id in self.metadata:
            return True

        index_path, meta_path = self._module_paths(module_id)
        if not index_path.exists() or not meta_path.exists():
            return False

        try:
            self.indices[module_id] = faiss.read_index(str(index_path))
            with open(meta_path, "r", encoding="utf-8") as f:
                self.metadata[module_id] = json.load(f)
            return True
        except Exception as e:
            logger.error(f"Error loading vector store for module {module_id}: {str(e)}")
            return False

    def _save_module(self, module_id: str) -> None:
        if module_id not in self.indices or module_id not in self.metadata:
            return

        index_path, meta_path = self._module_paths(module_id)
        try:
            faiss.write_index(self.indices[module_id], str(index_path))
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(self.metadata[module_id], f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving vector store for module {module_id}: {str(e)}")

    def _get_index(self, module_id: str):
        if module_id not in self.indices:
            loaded = self._load_module(module_id)
            if not loaded:
                self.indices[module_id] = faiss.IndexFlatL2(self.dimension)
                self.metadata[module_id] = []
        return self.indices[module_id]

    async def add_documents(self, module_id: str, documents: List[Dict[str, Any]]):
        """
        Add documents to the vector store for a specific module.
        documents should be a list of dicts: {"text": str, "source": str, "url": str, "metadata": dict}
        """
        try:
            index = self._get_index(module_id)
            texts = [doc["text"] for doc in documents]
            
            # Generate embeddings in batches of 50 to avoid token/limit issues
            all_embeddings = []
            batch_size = 50
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = await azure_openai_service.generate_embeddings_batch(batch)
                all_embeddings.extend(embeddings)
            
            embeddings_np = np.array(all_embeddings).astype('float32')
            index.add(embeddings_np)
            
            # Save metadata
            for doc in documents:
                self.metadata[module_id].append({
                    "source": doc.get("source", "Unknown"),
                    "url": doc.get("url", ""),
                    "text": doc["text"],
                    "metadata": doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
                })

            self._save_module(module_id)
            
            logger.info(f"Added {len(documents)} documents to vector store for module {module_id}")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise

    async def search(
        self,
        module_id: str,
        query: str,
        top_k: int = 5,
        metadata_filters: Optional[Dict[str, Any]] = None,
        overfetch_k: int = 25
    ) -> List[Dict[str, Any]]:
        """Search for relevant context in a module."""
        try:
            if module_id not in self.indices:
                self._load_module(module_id)
            if module_id not in self.indices:
                logger.warning(f"No index found for module {module_id}")
                return []
            
            index = self.indices[module_id]
            query_embedding = await azure_openai_service.generate_embedding(query)
            query_np = np.array([query_embedding]).astype('float32')
            
            k = max(top_k, int(overfetch_k or 0))
            D, I = index.search(query_np, k)
            
            results = []

            def matches_filters(doc_meta: Dict[str, Any]) -> bool:
                if not metadata_filters:
                    return True
                meta = doc_meta.get("metadata") if isinstance(doc_meta.get("metadata"), dict) else {}
                for key, expected in metadata_filters.items():
                    actual = meta.get(key)
                    if expected is None:
                        continue
                    if isinstance(expected, (list, tuple, set)):
                        if actual not in expected:
                            return False
                    else:
                        if actual != expected:
                            return False
                return True

            for pos, idx in enumerate(I[0]):
                if idx == -1 or idx >= len(self.metadata[module_id]):
                    continue
                doc = dict(self.metadata[module_id][idx])
                dist = float(D[0][pos]) if pos < len(D[0]) else None
                doc["distance"] = dist
                doc["similarity_score"] = (1.0 / (1.0 + dist)) if dist is not None else None
                if matches_filters(doc):
                    results.append(doc)
                if len(results) >= top_k:
                    break
            
            return results
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []

    def get_documents(self, module_id: str, metadata_filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Return all stored documents/chunks for a module (optionally metadata-filtered)."""
        if module_id not in self.metadata:
            self._load_module(module_id)
        if module_id not in self.metadata:
            return []

        docs = self.metadata[module_id]
        if not metadata_filters:
            return list(docs)

        filtered: List[Dict[str, Any]] = []
        for d in docs:
            meta = d.get("metadata") if isinstance(d.get("metadata"), dict) else {}
            ok = True
            for key, expected in metadata_filters.items():
                actual = meta.get(key)
                if expected is None:
                    continue
                if isinstance(expected, (list, tuple, set)):
                    if actual not in expected:
                        ok = False
                        break
                else:
                    if actual != expected:
                        ok = False
                        break
            if ok:
                filtered.append(d)
        return filtered

    def get_context_length(self, module_id: str) -> int:
        """Get number of documents for a module."""
        if module_id not in self.metadata:
            self._load_module(module_id)
        if module_id in self.metadata:
            return len(self.metadata[module_id])
        return 0

vector_store_service = VectorStoreService()
