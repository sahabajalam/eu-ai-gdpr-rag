# Baseline Accuracy Report (Week 3)

## Method
- **Dataset**: 30 Golden Q&A pairs (GDPR, EU AI Act, Cross-Regulation).
- **Judge**: `gemini-2.0-flash-lite` (LLM-as-a-judge).
- **Scoring**: 1-5 Scale for Correctness and Context Relevance.

## Results
| Metric | Score | Interpretation |
| :--- | :--- | :--- |
| **Average Correctness** | **3.07 / 5.0** | Moderate. The system finds relevant info but sometimes fails to synthesize a precise legal answer or misses nuances. |
| **Context Relevance** | **3.97 / 5.0** | Good. The `text-embedding-004` model is effectively retrieving the correct articles most of the time. |

## Analysis
- **Strengths**: High retrieval relevance indicates the chunking strategy and basic vector search are working well.
- **Weaknesses**: The synthesis layer (Generation) needs improvement. A score of 3.07 suggests some hallucinations or incomplete answers.
- **Next Steps**: 
    1.  **Advanced Retrieval**: Implement BM25 (Hybrid Search) to catch keyword-specific queries that vector search misses.
    2.  **Re-Ranking**: Use a cross-encoder to re-rank the top K results to improve context quality for the LLM.
    3.  **Prompt Refinement**: Improve the generator prompt to be more strictly grounded in the context.
