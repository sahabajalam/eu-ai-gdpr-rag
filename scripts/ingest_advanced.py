import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.advanced_chunking import AdvancedRegulationChunker
from src.utils.embeddings import GoogleGenAIEmbeddingFunction

# Load env for API keys
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
CHROMA_DIR = Path("data/chroma")
COLLECTION_NAME = "eu_ai_gdpr_parent_child" # New optimized collection

class AdvancedIngestionManager:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
            
        self.embedding_fn = GoogleGenAIEmbeddingFunction(
            api_key=api_key,
            model_name="models/text-embedding-004"
        )
        
        # Create or Get the new collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"description": "EU AI Act and GDPR (Parent-Child Structure)"}
        )
        
    def load_data(self) -> List[Dict[str, Any]]:
        files = ["gdpr_articles.json", "eu_ai_act_articles.json"]
        all_articles = []
        for f in files:
            path = PROCESSED_DIR / f
            if path.exists():
                logger.info(f"Loading {path}...")
                with open(path, "r", encoding="utf-8") as file:
                    all_articles.extend(json.load(file))
        return all_articles

    def run(self):
        logger.info(f"Starting Advanced Ingestion to collection: {COLLECTION_NAME}")
        
        # 1. Load
        articles = self.load_data()
        if not articles:
            logger.error("No data found!")
            return

        # 2. Chunk (Advanced)
        chunker = AdvancedRegulationChunker()
        chunks = []
        logger.info("Chunking articles with metadata extraction...")
        for article in articles:
            chunks.extend(chunker.chunk_article(article))
            
        logger.info(f"Generated {len(chunks)} chunks (Paragraphs).")
        
        # 3. Ingest
        ids = [c['id'] for c in chunks]
        documents = [c['text'] for c in chunks] # Embedding child text
        metadatas = [c['metadata'] for c in chunks] # Storing parent text here
        
        BATCH_SIZE = 100
        logger.info("Upserting to ChromaDB...")
        
        for i in range(0, len(chunks), BATCH_SIZE):
            batch_ids = ids[i:i+BATCH_SIZE]
            batch_docs = documents[i:i+BATCH_SIZE]
            batch_meta = metadatas[i:i+BATCH_SIZE]
            
            self.collection.upsert(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta
            )
            print(f"Batch {i//BATCH_SIZE + 1} done...", end="\r")
            
        logger.info("\nIngestion Complete!")
        logger.info(f"Final Collection Count: {self.collection.count()}")

if __name__ == "__main__":
    manager = AdvancedIngestionManager()
    manager.run()
