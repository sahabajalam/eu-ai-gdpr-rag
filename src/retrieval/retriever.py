import os
import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from google import genai
from dotenv import load_dotenv

# Use our custom embedding function
from src.utils.embeddings import GoogleGenAIEmbeddingFunction

load_dotenv()
logger = logging.getLogger(__name__)

class QueryClassifier:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        # Initialize new SDK client
        self.client = genai.Client(api_key=self.api_key)
        
    def classify(self, query: str) -> str:
        """
        Classifies the query into 'GDPR', 'EU_AI_Act', or 'BOTH'.
        """
        prompt = f"""
        You are a legal modification assistant. Classify the following query based on which regulation it pertains to.
        
        Options:
        - 'GDPR': If it asks about data protection, privacy, consent, personal data, DPO, etc.
        - 'EU_AI_Act': If it asks about AI systems, high-risk AI, transparency, prohibited practices, etc.
        - 'BOTH': If it asks about the intersection, comparison, or conflict between them.
        
        Query: "{query}"
        
        """
        try:
            import time
            from google.genai import types
            
            # RATE LIMIT SAFETY: Sleep briefly to prevent accidental cost spikes
            time.sleep(1.0) 
            
            # Simple retry with backoff
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model='gemini-2.0-flash-lite-preview-02-05',
                        contents=prompt
                    )
                    classification = response.text.strip()
                    
                    # Safety cleanup
                    for valid in ["GDPR", "EU_AI_Act", "BOTH"]:
                        if valid in classification:
                            return valid
                    return "BOTH" # Fallback if model hallucinates
                    
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        if attempt < max_retries - 1:
                            sleep_time = 2 
                            logger.warning(f"Rate limited. Retrying in {sleep_time}s...")
                            time.sleep(sleep_time)
                            continue
                    
                    # If we fail or run out of retries, log and fallback
                    logger.warning(f"Classification API failed: {e}. Falling back to 'BOTH'.")
                    return "BOTH"
            
            return "BOTH" # Default fallback
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return "BOTH"

class RegulationRetriever:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.chroma_client = chromadb.PersistentClient(
            path="data/chroma",
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        
        # Use Custom Embedding Function
        self.embedding_fn = GoogleGenAIEmbeddingFunction(
            api_key=self.api_key,
            model_name="models/text-embedding-004"
        )
        
        self.collection = self.chroma_client.get_collection(
            name="eu_ai_gdpr_rules",
            embedding_function=self.embedding_fn
        )
        self.classifier = QueryClassifier()
        
    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        # 1. Classify
        category = self.classifier.classify(query)
        logger.info(f"Query classified as: {category}")
        
        # 2. Define Filter
        where_filter = None
        if category == "GDPR":
            where_filter = {"regulation": "GDPR"}
        elif category == "EU_AI_Act":
            where_filter = {"regulation": "EU_AI_Act"}
        # If BOTH, no filter
        
        # 3. Query Vector Store
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where_filter
        )
        
        # 4. Format Results
        documents = []
        if results['documents']:
            for i, doc_text in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                documents.append({
                    "text": doc_text,
                    "metadata": meta,
                    "score": results['distances'][0][i] if results['distances'] else 0.0,
                    "classification": category
                })
                
        return documents

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    retriever = RegulationRetriever()
    
    queries = [
        "What is personal data?",
        "What are high-risk AI systems?",
        "How do GDPR and AI Act interact?"
    ]
    
    for q in queries:
        print(f"\n--- Query: {q} ---")
        docs = retriever.retrieve(q, k=3)
        print(f"Classification: {docs[0]['classification'] if docs else 'None'}")
        for d in docs:
            print(f"[{d['metadata']['regulation']}] {d['text'][:80]}...")
