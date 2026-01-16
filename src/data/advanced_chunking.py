from typing import List, Dict, Any
import logging
from uuid import uuid4
import re

logger = logging.getLogger(__name__)

class AdvancedRegulationChunker:
    """
    Implements Hierarchical (Parent-Child) Chunking with Legal Metadata extraction.
    
    Structure:
    - Parent: Full Article text (stored in metadata, not embedded)
    - Child: Individual Paragraphs (embedded for retrieval)
    
    Metadata:
    - legal_force: 'mandatory', 'permissive', 'explanatory'
    - contains_obligation: boolean
    """
    
    def __init__(self):
        # Regex patterns for legal analysis
        self.obligation_pattern = re.compile(r'\b(shall|must|required to|obligation)\b', re.IGNORECASE)
        self.mandatory_pattern = re.compile(r'\bshall\b', re.IGNORECASE)
        self.permissive_pattern = re.compile(r'\bmay\b', re.IGNORECASE)
        self.reference_pattern = re.compile(r'Article\s+(\d+(?:\(\d+\))?)', re.IGNORECASE)

    def extract_legal_metadata(self, text: str) -> Dict[str, Any]:
        """Analyze text for legal force and obligations."""
        metadata = {
            "contains_obligation": bool(self.obligation_pattern.search(text)),
            "legal_force": "explanatory", # default
            "referenced_articles": ",".join(self.reference_pattern.findall(text)) # ChromaDB requires string
        }
        
        if self.mandatory_pattern.search(text):
            metadata["legal_force"] = "mandatory"
        elif self.permissive_pattern.search(text):
            metadata["legal_force"] = "permissive"
            
        return metadata

    def chunk_article(self, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Takes a raw article and returns Parent-Child chunks.
        """
        chunks = []
        full_text = article.get('full_text', '')
        article_id = article.get('id', str(uuid4()))
        article_num = article.get('article_number', '0')
        regulation = article.get('regulation', 'Unknown')
        title = article.get('title', '')
        
        # 1. Base Metadata (Shared)
        # We store the FULL PARENT TEXT in the metadata of every child.
        # This allows the retriever to grab the full context immediately.
        # Note: This increases storage size but simplifies retrieval logic (no separate key-value store needed).
        base_metadata = {
            "article_id": article_id,
            "article_number": article_num,
            "title": title,
            "regulation": regulation,
            "parent_text": full_text, # <--- THE KEY UPGRADE
            "total_tokens": len(full_text.split()) # Rough estimate
        }
        
        # 2. Split into Children (Paragraphs)
        # Using double newline as heuristic for paragraph separation
        paragraphs = [p.strip() for p in full_text.split('\n') if p.strip()]
        
        for idx, para in enumerate(paragraphs):
            # Skip very short generic headers if they slipped through
            if len(para) < 20 and "Article" in para:
                continue
                
            chunk_id = f"{article_id}_p{idx}"
            
            # 3. Analyze Child
            legal_meta = self.extract_legal_metadata(para)
            
            # 4. Merge Metadata
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update(legal_meta)
            chunk_metadata.update({
                "chunk_id": chunk_id,
                "chunk_index": idx,
                "child_type": "paragraph"
            })
            
            chunks.append({
                "id": chunk_id,
                "text": para, # Only embed the paragraph
                "metadata": chunk_metadata
            })
            
        return chunks

if __name__ == "__main__":
    # Test
    chunker = AdvancedRegulationChunker()
    sample = {
        "article_number": "35",
        "title": "Data protection impact assessment",
        "regulation": "GDPR",
        "full_text": "1. Where a type of processing in particular using new technologies... shall resulted in a high risk...\n\n2. The controller shall seek the advice of the data protection officer..."
    }
    
    result = chunker.chunk_article(sample)
    for c in result:
        print(f"[{c['metadata']['legal_force'].upper()}] {c['text'][:50]}...")
