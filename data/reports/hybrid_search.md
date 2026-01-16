# Hybrid Search & Re-Ranking: Technical Deep Dive

## Executive Summary
**Winner: Baseline Vector Search**
After implementing and evaluating both Hybrid Search (Vector + Keyword) and Cross-Encoder Re-Ranking, we found that the **Baseline Vector Retrieval** using `text-embedding-004` provided the highest accuracy and the lowest latency. The more complex pipelines introduced noise that degraded performance on this specific legal dataset.

---

## 1. Experiment Setup

### 1.1 Objective
To improve the "Correctness" score of the RAG pipeline. The Baseline (`Vector Only`) had a Correctness score of **3.07/5.0**, despite a high Context Relevance score of **3.97/5.0**. We hypothesized that adding Keyword Search (BM25) would improve recall for specific legal terms, and Re-Ranking would improve precision.

### 1.2 Methodologies Tested
1.  **Baseline (Vector)**: 
    -   Embedding: `models/text-embedding-004` (Google GenAI).
    -   Database: ChromaDB.
    -   Retrieval: Top 5 chunks by cosine similarity.
    
2.  **Hybrid (Vector + BM25)**:
    -   Combined the Baseline with `BM25Okapi` (using `rank-bm25`).
    -   Fusion: Reciprocal Rank Fusion (RRF) with `k=60`.
    -   Retrieval: Top 5 chunks from valid fused scores.

3.  **Advanced (Hybrid + Re-Ranking)**:
    -   Retrieval: Fetch Top 50 candidates using Hybrid Search.
    -   Re-Ranking: `cross-encoder/ms-marco-MiniLM-L-6-v2` (`sentence-transformers`).
    -   Use: Scores the `(query, document)` pair and selects the Top 5.

---

## 2. Quantitative Results (n=30)

| Metric | Baseline (Vector) | Hybrid (BM25+Vec) | Advanced (Re-Rank) |
| :--- | :--- | :--- | :--- |
| **Correctness** | **3.07** | 2.77 (-0.30) | 2.40 (-0.67) |
| **Context Relevance** | **3.97** | 3.73 (-0.24) | 3.20 (-0.77) |
| **API Latency** | **Fastest** | Fast | Slow (~2s/query) |
| **Cost** | Low | Low | Medium (Inference) |

---

## 3. Analysis & Failure Mode Decomposition

### 3.1 Why did Hybrid Search fail? (2.77 vs 3.07)
*   **Semantic vs. Lexical**: Legal queries in this domain (e.g., *"What are the conditions for consent?"*) are highly semantic. The exact keywords "conditions" or "consent" appear in hundreds of chunks (low IDF - Inverse Document Frequency).
*   **Noise Injection**: BM25 prioritized documents with high keyword frequency but low semantic relevance (e.g., definitions or recitals mentions), displacing the substantive Articles that the Vector model had correctly identified.
*   **Tokenization**: Even with improved regex tokenization, the "Bag of Words" approach of BM25 struggled with the nuance of legal phrasing compared to the dense vector representations.

### 3.2 Why did Re-Ranking fail? (2.40 vs 3.07)
*   **Domain Mismatch**: The Cross-Encoder model (`ms-marco-MiniLM-L-6-v2`) is trained on the MS MARCO dataset (Bing search queries). It is optimized for finding direct factoid answers in web text.
*   **Legal Complexity**: It is *not* fine-tuned for legal text. It likely down-voted complex legal clauses because they didn't look like standard "web answers," filtering out the actual ground truth chunks that the retrieval layer had found.
*   **Pipeline Compounding**: By feeding the Re-Ranker the "Top 50" from the already-noisy Hybrid search, we amplified the error.

---

## 4. Final Architecture Decision

We have **reverted** the production system to the **Baseline Configuration**.

### Justification
1.  **Performance**: The Baseline consistently retrieved the most relevant contexts (3.97/5.0).
2.  **Efficiency**: It requires no extra inference step (no Cross-Encoder latency) and no in-memory index management (BM25).
3.  **Stability**: Google's `text-embedding-004` is robust and handles the legal vocabulary better than off-the-shelf open-source models for this specific task.

### Codebase Status
- **Active**: `src/retrieval/retriever.py` (Vector Search).
- **Archived/Disabled**: `src/retrieval/hybrid_search.py` and `src/retrieval/reranker.py`.

## 5. Future Recommendations
To improve beyond the 3.07 ceiling, we should not add more retrieval complexity. Instead:
1.  **Prompt Engineering**: Improve the LLM prompts to better synthesize the answer from the high-quality context it is already receiving.
2.  **Chunking Strategy**: Experiment with larger parent chunks (`ParentDocumentRetriever`) to give the LLM more surrounding context.
