# Hybrid Search Evaluation Report (Week 3)

## Method
- **Method**: Hybrid Retrieval (ChromaDB + BM25) with RRF (k=60).
- **Dataset**: 30 Golden Q&A.
- **Judge**: `gemini-2.0-flash-lite`.

## Results
| Metric | Baseline (Vector) | Hybrid (Vector + BM25) | Delta |
| :--- | :--- | :--- | :--- |
| **Correctness** | 3.07 | 2.77 | **-0.30** |
| **Context Relevance** | 3.97 | 3.73 | **-0.24** |

## Analysis
- **Negative Result**: Hybrid search (with simple text tokenization) performed *worse* than pure semantic search.
- **Cause**: Legal queries are highly semantic (e.g., "conditions for consent"). BM25 likely retrieved documents containing the keywords but missing the legal context, diluting the top-k results fed to the LLM.
- **Conclusion**: BM25 introduces high recall but low precision noise ("Recall-Precision Tradeoff").

## Recommendation
- **Next Step**: Implement **Cross-Encoder Re-Ranking**.
- **Reasoning**: Hybrid search is good for *Recall* (finding varied candidates). A Re-ranker will filter out the noisy BM25 matches and keep only the truly relevant ones, likely boosting the final score above the baseline.
- **Action**: Reverted `RAGGenerator` to Vector-only mode until Re-ranker is ready.
