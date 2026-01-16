import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_retrieval():
    # Setup
    CHROMA_DIR = "data/chroma"
    api_key = os.getenv("GEMINI_API_KEY")
    api_key = os.getenv("GEMINI_API_KEY")
    
    from src.utils.embeddings import GoogleGenAIEmbeddingFunction
    embedding_fn = GoogleGenAIEmbeddingFunction(
        api_key=api_key,
        model_name="models/text-embedding-004"
    )
    
    client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(allow_reset=True, anonymized_telemetry=False))
    collection = client.get_collection("eu_ai_gdpr_rules", embedding_function=embedding_fn)
    
    count = collection.count()
    print(f"Collection Count: {count}")
    
    if count == 0:
        print("FAIL: Collection is empty.")
        return

    # Test Query
    query = "What are the fines for GDPR violations?"
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    
    print(f"\nQuery: {query}")
    print("Results:")
    for i, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][i]
        print(f"[{i+1}] {meta.get('regulation')} Art {meta.get('article_number')}: {doc[:100]}...")
        
    print("\nSUCCESS: Retrieval working.")

if __name__ == "__main__":
    verify_retrieval()
