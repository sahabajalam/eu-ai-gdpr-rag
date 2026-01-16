
import os
import logging
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# RAGAS
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

# LangChain Google
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Project Imports
from src.retrieval.parent_child_retriever import ParentChildRetriever
from src.generation.generator import RAGGenerator

load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ragas_evaluator")

class RagasEvaluator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
            
        # 1. Setup Gemini for RAGAS (Judge)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite-preview-02-05",
            google_api_key=self.api_key,
            temperature=0
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=self.api_key
        )
        
        # Wrap for RAGAS
        self.ragas_llm = LangchainLLMWrapper(self.llm)
        self.ragas_embeddings = LangchainEmbeddingsWrapper(self.embeddings)
        
        # 2. Setup System to Evaluate
        self.generator = RAGGenerator() # Uses ParentChildRetriever (Smart Graph)
        
        # 3. Load Data
        self.golden_set_path = Path("data/golden_qa/compliance_test_set.json")

    def load_data(self) -> List[Dict]:
        with open(self.golden_set_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_detailed_dataset(self, test_set: List[Dict]):
        """
        Runs the RAG pipeline on the test set to generate:
        - Question
        - Answer (Generated)
        - Contexts (Retrieved)
        - Ground Truth
        """
        data_samples = {
            "question": [],
            "answer": [],
            "contexts": [],
            "ground_truth": []
        }
        
        total = len(test_set)
        for i, item in enumerate(test_set):
            q = item['question']
            gt = item['ground_truth']
            
            logger.info(f"[{i+1}/{total}] Processing: {q}")
            
            # Run Pipeline
            result = self.generator.generate_answer(q)
            
            # Extract Text from Contexts
            retrieved_texts = [d['text'] for d in result['context']]
            
            data_samples["question"].append(q)
            data_samples["answer"].append(result['answer'])
            data_samples["contexts"].append(retrieved_texts)
            data_samples["ground_truth"].append(gt)
            
        return pd.DataFrame(data_samples)

    def run(self):
        logger.info("loading test data...")
        test_data = self.load_data()
        
        # For testing, maybe limit? No, run all 30.
        # test_data = test_data[:2] 
        
        logger.info("Generating RAG outputs for evaluation...")
        dataset = self.generate_detailed_dataset(test_data)
        
        logger.info("Running RAGAS Evaluation (Metrics: Faithfulness, Relevancy, Precision, Recall)...")
        
        # Convert to Ragas Dataset
        from datasets import Dataset
        ragas_dataset = Dataset.from_pandas(dataset)
        
        # Run Evaluation
        results = evaluate(
            ragas_dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall
            ],
            llm=self.ragas_llm,
            embeddings=self.ragas_embeddings
        )
        
        # Save Results
        output_path = Path("data/reports/ragas_report.csv")
        results.to_pandas().to_csv(output_path, index=False)
        logger.info(f"RAGAS evaluation complete. Saved to {output_path}")
        
        print("\n=== RAGAS Scores ===")
        print(results)

if __name__ == "__main__":
    evaluator = RagasEvaluator()
    evaluator.run()
