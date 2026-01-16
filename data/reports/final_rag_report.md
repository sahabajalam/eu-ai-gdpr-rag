# Final RAG Experiment Report

## Objective
Maximize the accuracy of the EU AI Act/GDPR RAG system.

## Experiments & Results (n=30)
| Configuration | Retrieve | Re-Rank | Correctness | Context Rel | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline** | Vector (`text-embedding-004`) | None | **3.07** | **3.97** | 🏆 **Winner** |
| **Hybrid** | Vector + BM25 | None | 2.77 | 3.73 | Failed |
| **Advanced** | Hybrid (Top 50) | Cross-Encoder (`MiniLM`) | 2.40 | 3.20 | Failed |

## Analysis
1.  **Semantic vs Keyword**: The **Baseline** (Pure Vector) achieved the highest context relevance (3.97). This confirms that for this legal corpus, the semantic meaning of chunks is more important than exact keyword matches (BM25).
2.  **Noise Introduction**: Adding BM25 (Hybrid) lowered accuracy. This suggests that BM25 was retrieving irrelevant "keyword-heavy" chunks that displaced valid semantic matches.
3.  **Re-Ranking Failure**: The `ms-marco-MiniLM-L-6-v2` Cross-Encoder, while powerful for general search (Bing/MS Marco), degraded performance here. It likely favors "direct answer" passages over the complex legal text chunks present in this dataset.

## Conclusion
**Simpler is Better.**
We have reverted the production system to the **Baseline Configuration** (Vector Search Only).
- **Correctness**: 3.07 / 5.0
- **Cost**: Lowest (No extra Re-Ranking inference).
- **Speed**: Fastest.

## Future Recommendations
- **Domain-Specific Embedding**: Fine-tune the embedding model on legal text.
- **Larger LLM**: Upgrade generator to `gemini-1.5-pro` (smarter synthesis) instead of `flash` to improve the "Correctness" score (gap between 3.97 context and 3.07 answer).
