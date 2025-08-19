import os
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import structlog
import PyPDF2
from io import BytesIO

from app.settings import config

logger = structlog.get_logger()


class RAGService:
    def __init__(self):
        self.model = None  # Lazy load to avoid import issues on startup
        self.index = None
        self.documents = []
        self.index_path = Path("faiss_index")
        self.documents_path = self.index_path / "documents.json"
        self.index_file = self.index_path / "index.faiss"
        
        # Create index directory if it doesn't exist
        self.index_path.mkdir(exist_ok=True)
        
        # Load existing index if available
        self.load_index()
    
    def _init_model(self):
        """Lazy initialization of the sentence transformer model"""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Sentence transformer model loaded")
            except ImportError as e:
                logger.error(f"Failed to import sentence-transformers: {e}")
                logger.warning("RAG functionality will be limited")
                return False
        return True
    
    def load_index(self):
        """Load existing FAISS index and documents"""
        try:
            if self.index_file.exists() and self.documents_path.exists():
                try:
                    import faiss
                    self.index = faiss.read_index(str(self.index_file))
                    with open(self.documents_path, 'r', encoding='utf-8') as f:
                        self.documents = json.load(f)
                    logger.info(f"Loaded index with {len(self.documents)} documents")
                except ImportError:
                    logger.warning("FAISS not available, RAG search disabled")
            else:
                logger.info("No existing index found, will create new one")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            self.index = None
            self.documents = []
    
    def save_index(self):
        """Save FAISS index and documents to disk"""
        try:
            if self.index is not None:
                import faiss
                faiss.write_index(self.index, str(self.index_file))
                with open(self.documents_path, 'w', encoding='utf-8') as f:
                    json.dump(self.documents, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved index with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def load_faqs_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """Load FAQs from CSV file"""
        documents = []
        try:
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                documents.append({
                    "text": f"Q: {row['question']}\nA: {row['answer']}",
                    "source": "faq",
                    "metadata": {
                        "question": row['question'],
                        "answer": row['answer'],
                        "tags": row.get('tags', '')
                    }
                })
        except Exception as e:
            logger.error(f"Error loading FAQs from {csv_path}: {e}")
        
        return documents
    
    def load_menu_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """Load menu items from CSV file"""
        documents = []
        try:
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                if row.get('available', True):
                    text = f"Producto: {row['name']}\nPrecio: ${row['price']}"
                    if pd.notna(row.get('description')):
                        text += f"\nDescripción: {row['description']}"
                    if pd.notna(row.get('category')):
                        text += f"\nCategoría: {row['category']}"
                    
                    documents.append({
                        "text": text,
                        "source": "menu",
                        "metadata": {
                            "name": row['name'],
                            "price": row['price'],
                            "description": row.get('description', ''),
                            "category": row.get('category', ''),
                            "product_id": row.get('id', None)
                        }
                    })
        except Exception as e:
            logger.error(f"Error loading menu from {csv_path}: {e}")
        
        return documents
    
    def load_document_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load and chunk document from file"""
        documents = []
        path = Path(file_path)
        
        try:
            if path.suffix.lower() == '.pdf':
                text = self._extract_pdf_text(file_path)
            elif path.suffix.lower() in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                logger.warning(f"Unsupported file type: {path.suffix}")
                return documents
            
            chunks = self.chunk_text(text, config.get("retrieval", {}).get("chunk_size", 300))
            
            for i, chunk in enumerate(chunks):
                documents.append({
                    "text": chunk,
                    "source": "document",
                    "metadata": {
                        "file_name": path.name,
                        "file_path": str(path),
                        "chunk_id": i,
                        "total_chunks": len(chunks)
                    }
                })
        
        except Exception as e:
            logger.error(f"Error loading document from {file_path}: {e}")
        
        return documents
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
        return text
    
    def rebuild_index(self) -> Dict[str, int]:
        """Rebuild the entire FAISS index from data sources"""
        logger.info("Starting index rebuild")
        
        # Initialize model if needed
        if not self._init_model():
            return {"error": "Failed to initialize AI model", "faqs": 0, "menu": 0, "docs": 0}
        
        all_documents = []
        stats = {"faqs": 0, "menu": 0, "docs": 0}
        
        # Load FAQs
        faq_path = Path("data/faqs.csv")
        if faq_path.exists():
            faq_docs = self.load_faqs_from_csv(str(faq_path))
            all_documents.extend(faq_docs)
            stats["faqs"] = len(faq_docs)
        
        # Load Menu
        menu_path = Path("data/menu.csv")
        if menu_path.exists():
            menu_docs = self.load_menu_from_csv(str(menu_path))
            all_documents.extend(menu_docs)
            stats["menu"] = len(menu_docs)
        
        # Load Documents
        docs_dir = Path("data/docs")
        if docs_dir.exists():
            for file_path in docs_dir.glob("*"):
                if file_path.is_file():
                    doc_docs = self.load_document_from_file(str(file_path))
                    all_documents.extend(doc_docs)
                    stats["docs"] += len(doc_docs)
        
        if not all_documents:
            logger.warning("No documents found to index")
            return stats
        
        try:
            import faiss
            
            # Generate embeddings
            texts = [doc["text"] for doc in all_documents]
            embeddings = self.model.encode(texts, convert_to_tensor=False, show_progress_bar=True)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings.astype('float32'))
            
            # Store documents
            self.documents = all_documents
            
            # Save to disk
            self.save_index()
            
            logger.info(f"Index rebuilt with {len(all_documents)} documents")
            return stats
        
        except ImportError:
            logger.error("FAISS not available for indexing")
            return {"error": "FAISS not available", "faqs": 0, "menu": 0, "docs": 0}
    
    def search(self, query: str, top_k: int = 4, min_score: float = 0.5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        if self.index is None or not self.documents:
            logger.warning("No index available for search")
            # Fallback to simple text search
            return self._simple_text_search(query, top_k)
        
        try:
            import faiss
            
            # Initialize model if needed
            if not self._init_model():
                return self._simple_text_search(query, top_k)
            
            # Generate query embedding
            query_embedding = self.model.encode([query], convert_to_tensor=False)
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and score >= min_score:
                    doc = self.documents[idx].copy()
                    doc["score"] = float(score)
                    results.append(doc)
            
            return results
        
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return self._simple_text_search(query, top_k)
    
    def _simple_text_search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Fallback simple text search when FAISS is not available"""
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            text_lower = doc["text"].lower()
            score = 0.0
            
            # Simple keyword matching
            query_words = query_lower.split()
            for word in query_words:
                if word in text_lower:
                    score += 1.0 / len(query_words)
            
            if score > 0:
                doc_copy = doc.copy()
                doc_copy["score"] = score
                results.append(doc_copy)
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


# Global RAG service instance
rag_service = RAGService()