import json
import logging
import os
import time
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from google import genai

from src.generation.generator import RAGGenerator

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEvaluator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        self.client = genai.Client(api_key=self.api_key)
        self.generator = RAGGenerator()
        self.golden_set_path = Path("data/golden_qa/compliance_test_set.json")
        
    def load_test_set(self) -> List[Dict]:
        if not self.golden_set_path.exists():
            raise FileNotFoundError(f"Golden set not found at {self.golden_set_path}")
        with open(self.golden_set_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def evaluate_answer(self, question: str, ground_truth: str, generated_answer: str, context: List[Dict]) -> Dict[str, Any]:
        """
        Uses an LLM judge to evaluate the correctness of the generated answer.
        """
        # Context Check (Did we retrieve the right article?)
        retrieved_texts = "\n".join([c['text'] for c in context])
        
        prompt = f"""
        You are an expert impartial judge for a RAG system.
        Evaluate the AI's generated answer against the ground truth and the retrieved context.
        
        Question: {question}
        Ground Truth: {ground_truth}
        Generated Answer: {generated_answer}
        Retrieved Context: {retrieved_texts[:2000]}... (truncated)
        
        Task:
        1. Score correctness (1-5): 5=Perfect Match, 1=Completely Wrong.
        2. Score context_relevance (1-5): 5=Context contains the answer, 1=Irrelevant context.
        3. Provide a brief explanation.
        
        Return JSON ONLY:
        {{
            "correctness_score": int,
            "context_score": int,
            "explanation": "string"
        }}
        """
        
        try:
            # Retry logic for Judge
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Rate limit safety
                    time.sleep(2.0) # Increased sleep
                    
                    response = self.client.models.generate_content(
                        model='gemini-2.0-flash-lite-preview-02-05',
                        contents=prompt,
                        config={'response_mime_type': 'application/json'}
                    )
                    return json.loads(response.text)
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                         if attempt < max_retries - 1:
                            sleep_time = (attempt + 1) * 5
                            logger.warning(f"Judge Rate Limit. Retrying in {sleep_time}s...")
                            time.sleep(sleep_time)
                            continue
                    raise e
                    
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"correctness_score": 0, "context_score": 0, "explanation": str(e)}

    def run_evaluation(self, limit: int = None):
        logger.info("Starting Evaluation Run...")
        test_set = self.load_test_set()
        
        if limit:
            test_set = test_set[:limit]
            
        results = []
        
        for i, item in enumerate(test_set):
            q = item['question']
            gt = item['ground_truth']
            logger.info(f"[{i+1}/{len(test_set)}] Evaluate: {q}")
            
            # Generate
            gen_result = self.generator.generate_answer(q)
            answer = gen_result['answer']
            context = gen_result['context']
            
            # Evaluate
            eval_metrics = self.evaluate_answer(q, gt, answer, context)
            
            result_entry = {
                "id": item.get('id', str(i)),
                "question": q,
                "ground_truth": gt,
                "generated_answer": answer,
                "metrics": eval_metrics
            }
            results.append(result_entry)
            
            # Backup save every 5 items
            if (i+1) % 5 == 0:
                self._save_report(results, "partial_results.json")
                
        self._save_report(results, "smart_graph_report.json")
        self._print_summary(results)
        
    def _save_report(self, results: List[Dict], filename: str):
        path = Path(f"data/reports/{filename}")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
    def _print_summary(self, results: List[Dict]):
        total = len(results)
        avg_correct = sum(r['metrics']['correctness_score'] for r in results) / total if total else 0
        avg_context = sum(r['metrics']['context_score'] for r in results) / total if total else 0
        
        print("\n=== Evaluation Summary ===")
        print(f"Total Questions: {total}")
        print(f"Avg Correctness: {avg_correct:.2f}/5.0")
        print(f"Avg Context Rel: {avg_context:.2f}/5.0")

if __name__ == "__main__":
    evaluator = RAGEvaluator()
    # Run slightly smaller batch first to test
    evaluator.run_evaluation() # Full run 
