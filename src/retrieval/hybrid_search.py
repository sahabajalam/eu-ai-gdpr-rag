import logging
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Use our custom embedding function
from src.utils.embeddings import GoogleGenAIEmbeddingFunction

load_dotenv()
logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # 1. Setup ChromaDB (Vector)
        self.chroma_client = chromadb.PersistentClient(
            path="data/chroma",
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        self.embedding_fn = GoogleGenAIEmbeddingFunction(
            api_key=self.api_key,
            model_name="models/text-embedding-004"
        )
        self.collection = self.chroma_client.get_collection(
            name="eu_ai_gdpr_rules",
            embedding_function=self.embedding_fn
        )
        
        # 2. Setup BM25 (Keyword)
        logger.info("Initializing BM25 Index (this may take a moment)...")
        all_docs = self.collection.get() 
        self.documents = all_docs['documents']
        self.metadatas = all_docs['metadatas']
        self.ids = all_docs['ids']
        
        # Better Tokenization
        import re
        def preprocess(text):
            return re.findall(r'\w+', text.lower())

        self.preprocess = preprocess
        tokenized_corpus = [self.preprocess(doc) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"BM25 Index built with {len(self.documents)} documents.")
        
    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        # 1. Vector Search
        vector_results = self.collection.query(
            query_texts=[query],
            n_results=k * 2 # Fetch more for fusion candidates
        )
        
        # Format Vector Results
        vector_candidates = {}
        if vector_results['documents']:
            for i, doc_id in enumerate(vector_results['ids'][0]):
                vector_candidates[doc_id] = {
                    "rank": i + 1,
                    "doc": vector_results['documents'][0][i],
                    "meta": vector_results['metadatas'][0][i]
                }
                
        # 2. BM25 Search
        tokenized_query = self.preprocess(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        # Get top indices
        top_n_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:k*2]
        
        bm25_candidates = {}
        for rank, idx in enumerate(top_n_indices):
            doc_id = self.ids[idx]
            bm25_candidates[doc_id] = {
                "rank": rank + 1,
                "doc": self.documents[idx],
                "meta": self.metadatas[idx]
            }
            
        # 3. Reciprocal Rank Fusion (RRF)
        # score = 1 / (k + rank)
        fused_scores = {}
        all_ids = set(vector_candidates.keys()) | set(bm25_candidates.keys())
        
        RRF_K = 60
        for doc_id in all_ids:
            score = 0
            if doc_id in vector_candidates:
                score += 1 / (RRF_K + vector_candidates[doc_id]['rank'])
            if doc_id in bm25_candidates:
                score += 1 / (RRF_K + bm25_candidates[doc_id]['rank'])
            
            fused_scores[doc_id] = score
            
        # Sort by fused score
        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)[:k]
        
        # Format Final Results
        final_results = []
        for doc_id in sorted_ids:
            # Get content from either source (they share the same doc/meta)
            if doc_id in vector_candidates:
                cand = vector_candidates[doc_id]
            else:
                cand = bm25_candidates[doc_id]
                
            final_results.append({
                "text": cand['doc'],
                "metadata": cand['meta'],
                "score": fused_scores[doc_id],
                "id": doc_id
            })
            
        return final_results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    retriever = HybridRetriever()
    
    q = "machine learning training data requirements"
    print(f"\nQuery: {q}")
    results = retriever.retrieve(q)
    for r in results:
        print(f"[{r['score']:.4f}] {r['metadata']['regulation']}: {r['text'][:50]}...")
