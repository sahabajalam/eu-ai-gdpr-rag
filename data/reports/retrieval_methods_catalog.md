# Retrieval Methods Catalog

## 1. Applied & Evaluated Methods (Week 3)

### 1.1 Baseline Vector Search (Current Production)
*   **Mechanism**: Dense vector embeddings (`text-embedding-004`) + Cosine Similarity.
*   **Status**: **Active (Production)**.
*   **Performance**: Correctness **3.07** | Context **3.97**.
*   **Pros**: Fast, robust semantic matching, lowest cost.
*   **Cons**: Struggles with multi-hop reasoning and precise "keyword-specific" legal obligations.

### 1.2 Hybrid Search (Vector + BM25)
*   **Mechanism**: Weighted Average (RRF) of Vector Rank and BM25 (Keyword) Rank.
*   **Status**: Verified & Reverted (Failed).
*   **Performance**: Correctness **2.77** (Worse than baseline).
*   **Failure Cause**: "Noise Injection". BM25 retrieved irrelevant chunks containing common words (e.g., "consent") that displaced the semantically relevant chunks.

### 1.3 Cross-Encoder Re-Ranking
*   **Mechanism**: Pass Top 50 results to a Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) to re-score relevance.
*   **Status**: Verified & Reverted (Failed).
*   **Performance**: Correctness **2.40** (Worst).
*   **Failure Cause**: Domain Mismatch. The open-source model (trained on Bing/Web) did not understand legal relevance and filtered out correct answers.

---

## 2. Advanced Strategies (Proposed in `alternative.md`)

### 2.1 HyDE (Hypothetical Document Embeddings)
*   **Mechanism**: LLM generates a *hypothetical* legal answer to the query. This hypothetical answer is embedded and used for vector search.
*   **Goal**: Bridges the "language gap" (User Question vs. Regulatory Text).
*   **Effort**: Low (2-3 hours).
*   **Recommendation**: **TIER 1 (Quick Win)**.

### 2.2 Metadata-Enhanced Retrieval + Parent-Child Chunking
*   **Mechanism**:
    *   **Chunking**: Parent (Full Article) -> Children (Paragraphs).
    *   **Metadata**: Tag chunks with `legal_force` ("SHALL" vs "MAY") and `contains_obligation`.
    *   **Retrieval**: Filter by metadata (e.g., "Only show mandatory obligations").
    *   **Goal**: Solves granularity issues and precision (filtering out recitals/explanations).
*   **Effort**: Medium (6-8 hours).
*   **Recommendation**: **TIER 1 (Structural Fix)**.

### 2.3 Query Decomposition + Multi-Step Retrieval
*   **Mechanism**: Break complex queries into sub-questions (e.g., "GDPR reqs" + "AI Act reqs"), retrieve separately, then synthesize.
*   **Goal**: Solves multi-hop reasoning constraints.
*   **Effort**: Medium-High.
*   **Recommendation**: Tier 2 (If semantics fail).

### 2.4 Article Dependency Graph (Knowledge Graph Lite)
*   **Mechanism**: Build a graph where nodes are Articles and edges are citations ("Article 35 references Article 6"). Traverse graph to find related context.
*   **Goal**: Solves deep multi-hop dependency chains common in law.
*   **Effort**: High.
*   **Recommendation**: Tier 2 (Preview of GraphRAG).

### 2.5 Ensemble Embeddings
*   **Mechanism**: Use multiple embedding models (GenAI + Legal-BERT) and fuse results.
*   **Goal**: Catch nuances one model might miss.
*   **Effort**: Medium.

### 2.6 ColBERT (Multi-Vector)
*   **Mechanism**: "Late Interaction" model that keeps all token vectors (no pooling), allowing precise fine-grained matching.
*   **Goal**: Highest possible precision for complex phrasing.
*   **Effort**: High (Computationally expensive).

### 2.7 LLM-as-Retriever
*   **Mechanism**: Ask LLM "Which articles cover X?" then fetch them by ID.
*   **Goal**: Bypasses semantic search limitations completely.
*   **Effort**: Low-Medium (Hallucination risk).
