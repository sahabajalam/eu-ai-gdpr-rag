import logging
import os
from typing import List, Optional

from chromadb import Documents, EmbeddingFunction, Embeddings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class GoogleGenAIEmbeddingFunction(EmbeddingFunction):
    """
    Custom EmbeddingFunction for ChromaDB using the new `google-genai` SDK.
    Replaces the deprecated `google.generativeai` implementation.
    """
    def __init__(self, api_key: str, model_name: str = "models/text-embedding-004"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def __call__(self, input: Documents) -> Embeddings:
        """
        Generates embeddings for the input documents.
        """
        if not input:
            return []
            
        try:
            # The new SDK supports batched generation
            # API expects 'model' and 'content'
            # We map input documents to the expected format
            
            # Note: The Google GenAI SDK might have specific batch limits. 
            # ChromaDB usually sends batches, but we should process carefully.
            
            embeddings = []
            
            # Simple iteration for now to ensure robustness, or batch if SDK supports list
            # looking at SDK docs pattern: client.models.embed_content(model=..., contents=[...])
            
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=input,
                config=types.EmbedContentConfig(output_dimensionality=768) # Standard for 004
            )
            
            # Response should contain list of embeddings
            # Structure depends on SDK version, usually response.embeddings
            
            if hasattr(response, 'embeddings'):
                 # Each embedding object usually has a 'values' attribute
                return [e.values for e in response.embeddings]
            else:
                # Fallback or single item check (unlikely with list input)
                logger.error(f"Unexpected response format from Google GenAI: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Error generating embeddings with Google GenAI: {e}")
            raise e
