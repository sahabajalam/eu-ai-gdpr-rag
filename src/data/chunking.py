from typing import List, Dict, Any
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

class RegulationChunker:
    """
    Implements a hierarchical chunking strategy:
    - Parent: Full Article text (for context)
    - Child: Paragraphs/Recitals (for embedding)
    """
    
    def chunk_article(self, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Takes a raw article object and returns a list of chunks ready for embedding.
        """
        chunks = []
        full_text = article.get('full_text', '')
        article_id = article.get('id', str(uuid4()))
        regulation = article.get('regulation', 'Unknown')
        
        # Parent metadata (shared across all chunks)
        base_metadata = {
            "article_id": article_id,
            "article_number": article.get('article_number', '0'),
            "title": article.get('title', ''),
            "regulation": regulation,
            "source_type": "official_text"
        }
        
        # Strategy: Data is already list of paragraphs in some formats,
        # but our parser joined them into full text. 
        # Let's split by double newline as a heuristic for paragraphs if not provided.
        # Ideally, we should have kept the list structure in parser. 
        # For now, we'll split quite simply.
        
        paragraphs = [p.strip() for p in full_text.split('\n') if p.strip()]
        
        for idx, para in enumerate(paragraphs):
            # Skip very short generic lines if valid
            if len(para) < 20 and "Article" in para:
                continue
                
            chunk_id = f"{article_id}_chunk_{idx}"
            
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                "chunk_id": chunk_id,
                "chunk_index": idx,
                "parent_text": full_text[:1000] + "..." if len(full_text) > 1000 else full_text # store truncate parent
            })
            
            chunks.append({
                "id": chunk_id,
                "text": para,
                "metadata": chunk_metadata
            })
            
        return chunks

def process_regulatory_data(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunker = RegulationChunker()
    all_chunks = []
    
    for article in articles:
        chunks = chunker.chunk_article(article)
        all_chunks.extend(chunks)
        
    return all_chunks
