# Phase 3 Report: Graph-Enhanced Retrieval

## Objective
Evaluate if adding a **Legal Citation Graph (NetworkX)** improves retrieval accuracy by "connecting the dots" between related articles.

## Strategy Implemented
1.  **Graph Construction**: 
    -   Parsed full text to find "Article X" references.
    -   Built a Directed Graph where Node = Article, Edge = Citation.
2.  **Graph Retrieval**:
    -   Step 1: Parent-Child Vector Search (Top-k).
    -   Step 2: Check Graph for neighbors (citations) of retrieved nodes.
    -   Step 3: Add neighbors to context (Limited to 3 expansions).

## Results (n=30)
| Metric | Phase 2 (Parent-Child) | Phase 3 (Graph) | Delta |
| :--- | :--- | :--- | :--- |
| **Correctness** | **3.23** | 3.13 | -0.10 📉 |
| **Context Rel** | 1.97 | 2.03 | +0.06 📈 |

## Analysis
*   **Correctness Drop**: The graph expansion likely introduced **more noise than signal**. Legal citations are often structural ("as defined in Article 4") or procedural, which might distract the LLM from the specific question at hand if the question doesn't require that cross-reference.
*   **Context Relevance**: Slightly higher, suggesting the neighbors *were* relevant to the topic, but perhaps not critical for the *answer*.
*   **Latency**: Graph expansion adds a small overhead (graph traversal is fast, but processing more tokens takes time).

## Conclusion
**Phase 2 remains the best performing model.**
Adding naive citation expansion decreased performance. 
*   *Hypothesis*: We need "Smart Expansion" (only follow citations if confidence is low, or if the question implies a complex relationship).
*   *Decision*: Rollback to Phase 2 (Parent-Child) as the retrieval standard for the final UI, or keep Graph as an optional "Deep Search" toggle.

## Next Steps
Proceed to **Week 4: Evaluation & Refinement** (Confidence Scoring).
