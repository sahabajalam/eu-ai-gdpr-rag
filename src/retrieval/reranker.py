import logging
from typing import List, Dict
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class ReRanker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        logger.info(f"Loading CrossEncoder model: {model_name}...")
        self.model = CrossEncoder(model_name)
        
    def rerank(self, query: str, docs: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Re-ranks a list of retrieved documents based on their relevance to the query.
        """
        if not docs:
            return []
            
        # Prepare pairs for the model: (query, text)
        pairs = [(query, doc['text']) for doc in docs]
        
        # Predict scores
        scores = self.model.predict(pairs)
        
        # Attach scores to docs
        for i, doc in enumerate(docs):
            doc['rerank_score'] = float(scores[i])
            
        # Sort by new score
        sorted_docs = sorted(docs, key=lambda x: x['rerank_score'], reverse=True)
        
        return sorted_docs[:top_k]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    reranker = ReRanker()
    
    query = "What is GDPR?"
    docs = [
        {"text": "The GDPR is a regulation in EU law on data protection.", "metadata": {}},
        {"text": "Apples are a type of fruit.", "metadata": {}},
        {"text": "GDPR fines can be huge.", "metadata": {}}
    ]
    
    print("\nBefore Ranking:")
    for d in docs: print(f"- {d['text']}")
    
    ranked = reranker.rerank(query, docs)
    
    print("\nAfter Ranking:")
    for d in ranked: print(f"[{d['rerank_score']:.4f}] {d['text']}")
