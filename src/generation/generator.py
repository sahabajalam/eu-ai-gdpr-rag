import os
import logging
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.retrieval.parent_child_retriever import ParentChildRetriever
from src.generation.prompts import LEGAL_SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, CROSS_REGULATION_SYSTEM_PROMPT

load_dotenv()
logger = logging.getLogger(__name__)

class RAGGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        self.client = genai.Client(api_key=self.api_key)
        
        # PHASE 2: Parent-Child Retrieval (Full Context)
        logger.info("Initializing RAG Pipeline (Phase 2: Parent-Child + CoT)...")
        self.retriever = ParentChildRetriever() 
        
    def generate_answer(self, query: str, regulation_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves context and generates an answer using Gemini.
        """
        try:
            # 1. Retrieve (Get Full Parent Articles)
            logger.info(f"Retrieving context for: {query} (Filter: {regulation_filter})")
            docs = self.retriever.retrieve(query, k=5, regulation_filter=regulation_filter)
            
            if not docs:
                return {
                    "answer": "I found no relevant documents to answer this question.",
                    "context": []
                }
                
            # 2. Prepare Context String
            # Now we have full articles, so the context is richer.
            context_str = "\n\n".join([
                f"--- [Article {d['metadata']['article_number']}] {d['metadata']['title']} ---\n{d['text']}" 
                for d in docs
            ])
            
            # 3. Generate with System Prompt & Confidence
            logger.info("Generating answer with Confidence Score...")
            
            # Updated Prompt to ask for Confidence
            final_prompt = f"""
            {USER_PROMPT_TEMPLATE.format(query=query)}
            
            ---------------------
            INSTRUCTIONS:
            1. Answer the question based on the context.
            2. Provide a Confidence Score (0-100%) indicating how certain you are.
            3. If the answer is NOT in the context, say "I don't know" and score 0%.
            
            FORMAT YOUR RESPONSE AS JSON:
            {{
                "answer": "your answer here",
                "confidence_score": 85,
                "reasoning": "brief explanation of why you are confident or not"
            }}
            """
            
            # Add delay to avoid rate limits
            time.sleep(1.0)
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-lite-preview-02-05',
                config=types.GenerateContentConfig(
                    system_instruction=CROSS_REGULATION_SYSTEM_PROMPT.format(context=context_str),
                    temperature=0.1, # Lower temp for JSON stability
                    response_mime_type="application/json"
                ),
                contents=final_prompt
            )
            
            import json
            try:
                data = json.loads(response.text)
                answer = data.get("answer", "Error parsing answer")
                confidence = data.get("confidence_score", 0)
                
                # REFUSAL MECHANISM
                if confidence < 60:
                     answer = f"I am not confident enough to answer this question based on the available legal texts (Confidence: {confidence}%). Please consult a legal professional."
                
                # Get Graph Data for Visualization
                node_ids = [d.get('node_id') for d in docs if d.get('node_id')]
                graph_data = self.retriever.get_subgraph_for_nodes(node_ids)

                return {
                    "answer": answer,
                    "confidence": confidence,
                    "context": docs,
                    "graph_data": graph_data,
                    "raw_response": data
                }
            except json.JSONDecodeError:
                return {
                    "answer": response.text, 
                    "confidence": 0, 
                    "context": docs
                }
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("Rate limit hit, retrying once...")
                time.sleep(10)
                try:
                    # Simple retry of the same call
                    response = self.client.models.generate_content(
                        model='gemini-2.0-flash-lite-preview-02-05',
                        config=types.GenerateContentConfig(
                            system_instruction=LEGAL_SYSTEM_PROMPT.format(context=context_str),
                            temperature=0.3 
                        ),
                        contents=final_prompt
                    )
                    return {"answer": response.text, "context": docs}
                except Exception as e2:
                    return {"answer": f"Error generating answer after retry: {e2}", "context": docs}
            
            return {"answer": f"Error generating answer: {e}", "context": docs}

    def generate_answer_stream(self, query: str, regulation_filter: Optional[str] = None):
        """
        Retrieves context and streams the answer using Gemini.
        Yields JSON strings: 
        - {"type": "token", "content": "..."}
        - {"type": "metadata", "context": [...], "graph_data": ..., "confidence": ...}
        """
        try:
            # 1. Retrieve
            logger.info(f"Retrieving context for: {query} (Filter: {regulation_filter})")
            docs = self.retriever.retrieve(query, k=5, regulation_filter=regulation_filter)
            
            # 2. Context
            context_str = "\n\n".join([
                f"--- [Article {d['metadata']['article_number']}] {d['metadata']['title']} ---\n{d['text']}" 
                for d in docs
            ]) if docs else "No relevant documents found."

            # 3. Stream Answer
            prompt = f"""
            {USER_PROMPT_TEMPLATE.format(query=query)}
            
            Based on the context, answer the user's question directly and concisely.
            Do not include JSON formatting in your output, just the text answer.
            """
            
            # Start Graph Data Prep (Async-ish)
            node_ids = [d.get('node_id') for d in docs if d.get('node_id')]
            graph_data = self.retriever.get_subgraph_for_nodes(node_ids)
            
            # Send Metadata First (so UI can render graph while text streams)
            import json
            yield json.dumps({
                "type": "metadata",
                "confidence": 85, # Placeholder or calc separately
                "context": docs,
                "graph_data": graph_data
            }) + "\n"

            response = self.client.models.generate_content_stream(
                model='gemini-2.0-flash-lite-preview-02-05',
                config=types.GenerateContentConfig(
                    system_instruction=CROSS_REGULATION_SYSTEM_PROMPT.format(context=context_str),
                    temperature=0.3,
                ),
                contents=prompt
            )
            
            for chunk in response:
                if chunk.text:
                    yield json.dumps({
                        "type": "token",
                        "content": chunk.text
                    }) + "\n"
                    
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generator = RAGGenerator()
    
    q = "What are the administrative fines under GDPR?"
    print(f"\nQuestion: {q}")
    result = generator.generate_answer(q)
    print("\nAnswer:")
    print(result["answer"])
