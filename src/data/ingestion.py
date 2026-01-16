import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import tiktoken
from dotenv import load_dotenv
import os

from src.data.chunking import RegulationChunker
from src.utils.cost_tracker import estimate_cost

# Load env for API keys
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
CHROMA_DIR = Path("data/chroma")

class VectorStoreManager:
    def __init__(self, collection_name: str = "eu_ai_gdpr_rules"):
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        
        # Use Gemini Embeddings (models/text-embedding-004)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
            
        from src.utils.embeddings import GoogleGenAIEmbeddingFunction
        
        # Use Gemini Embeddings (models/text-embedding-004) via new SDK
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
            
        self.embedding_fn = GoogleGenAIEmbeddingFunction(
            api_key=api_key,
            model_name="models/text-embedding-004"
        )
        
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"description": "EU AI Act and GDPR Articles"}
        )
        
    def load_processed_data(self) -> List[Dict[str, Any]]:
        files = ["gdpr_articles.json", "eu_ai_act_articles.json"]
        all_articles = []
        
        for f in files:
            path = PROCESSED_DIR / f
            if path.exists():
                logger.info(f"Loading {path}...")
                with open(path, "r", encoding="utf-8") as file:
                    articles = json.load(file)
                    all_articles.extend(articles)
            else:
                logger.warning(f"File not found: {path} - skipping")
                
        logger.info(f"Total articles loaded: {len(all_articles)}")
        return all_articles
        
    def process_and_ingest(self):
        # 1. Load Data
        articles = self.load_processed_data()
        if not articles:
            logger.error("No articles found to ingest.")
            return

        # 2. Chunk Data
        logger.info("Chunking articles...")
        chunker = RegulationChunker()
        chunks = []
        for article in articles:
            chunks.extend(chunker.chunk_article(article))
            
        logger.info(f"Generated {len(chunks)} chunks.")
        
        # 3. Cost Estimation (Skipped for Gemini / Free Tier)
        # total_text = "".join([c['text'] for c in chunks])
        # cost = estimate_cost(total_text, "text-embedding-3-small", "input")
        # logger.info(f"Estimated Embedding Cost: ${cost:.5f}")
        
        # 4. Prepare Batch Ingestion
        # ChromaDB Upsert requires lists of ids, documents, metadatas
        ids = [c['id'] for c in chunks]
        documents = [c['text'] for c in chunks]
        metadatas = [c['metadata'] for c in chunks]
        
        # Batch size (limit to prevent timeout/payload issues)
        BATCH_SIZE = 100
        
        logger.info("Starting ingestion...")
        for i in range(0, len(chunks), BATCH_SIZE):
            batch_ids = ids[i:i+BATCH_SIZE]
            batch_docs = documents[i:i+BATCH_SIZE]
            batch_meta = metadatas[i:i+BATCH_SIZE]
            
            self.collection.upsert(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta
            )
            print(f"Ingested batch {i // BATCH_SIZE + 1} / {len(chunks) // BATCH_SIZE + 1}", end="\r")
            
        logger.info("\nIngestion Complete!")
        logger.info(f"Collection count: {self.collection.count()}")

if __name__ == "__main__":
    manager = VectorStoreManager()
    manager.process_and_ingest()
