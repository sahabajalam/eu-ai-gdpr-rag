import logging
import chromadb
from chromadb.config import Settings
from google import genai
from typing import List, Dict
import os
from dotenv import load_dotenv

# Use our custom embedding function
from src.utils.embeddings import GoogleGenAIEmbeddingFunction

load_dotenv()
logger = logging.getLogger(__name__)

class HyDEEnhancedRetriever:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
            
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
        
        # 2. Setup Generator for Hallucination (HyDE)
        self.client = genai.Client(api_key=self.api_key)
        
    def generate_hypothetical_document(self, query: str) -> str:
        """
        Generates a hypothetical legal regulation answering the query.
        """
        prompt = f"""You are a legal expert acting as a regulatory drafting engine.
Write a purely hypothetical legal paragraph (3-4 sentences) that would appear in the GDPR or EU AI Act to answer the following user question.
Use formal regulatory language (e.g., 'shall', 'pursuant to', 'prohibited', 'controller'). 
Do not provide an answer or explanation. Just write the hypothetical regulation text itself.
Do not invent specific article numbers like 'Article 999'.

User Question: {query}

Hypothetical Regulation Text:"""

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-lite-preview-02-05',
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"HyDE Generation failed: {e}")
            return query # Fallback/Passthrough

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """
        Retrieves using the hypothetical document embedding.
        """
        # 1. Generate Hypothetical Document
        logger.info(f"Generating HyDE document for: {query}")
        hypothetical_doc = self.generate_hypothetical_document(query)
        logger.debug(f"Hypothetical Doc: {hypothetical_doc[:100]}...")
        
        # 2. Vector Search using the Hypothetical Doc
        results = self.collection.query(
            query_texts=[hypothetical_doc],
            n_results=k
        )
        
        # Format Results
        formatted_results = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "text": doc,
                    "metadata": results['metadatas'][0][i],
                    "score": results['distances'][0][i] if results['distances'] else 0.0,
                    # We store the hypothetical doc used for debugging/analysis
                    "hyde_used": hypothetical_doc 
                })
                
        return formatted_results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    retriever = HyDEEnhancedRetriever()
    
    q = "Do I need consent for biometric data?"
    print(f"\nQuery: {q}")
    results = retriever.retrieve(q)
    
    print(f"\nHyDE Document Generated:\n{results[0]['hyde_used']}")
    print("-" * 50)
    
    for r in results:
        print(f"[{r['metadata']['regulation']}]: {r['text'][:100]}...")
