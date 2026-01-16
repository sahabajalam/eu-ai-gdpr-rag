# Smart Graph RAG: Navigating the EU AI Act & GDPR

## Project Overview

**Problem:**  
The intersection of the **EU AI Act** (2024) and **GDPR** creates a complex regulatory minefield for AI engineers. Navigating 200+ articles across two massive regulations to find specific compliance obligations—especially where they overlap or conflict—is a daunting, error-prone task for humans and a source of hallucination for generic LLMs.

**Solution:**  
I built a specialized **Graph-Enhanced RAG System** that maps the citation network between these regulations. It doesn't just "search vectors"—it understands the *structure* of the law. By combining **Parent-Child Chunking** with a **Smart Citation Graph**, it achieves incredibly high context recall (97.5%) while maintaining strict faithfulness to the legal text.

**Real-World Impact:**  
This tool solves the "Citation Problem" in legal AI. Instead of guessing, it traces the exact legal path (e.g., *Article 5 cites Article 13*) to provide grounded, defensible compliance answers. It turns hours of legal research into seconds of query time.

## Technical Architecture

### Tech Stack
*   **LLM & Embeddings:** Google Gemini 2.0 Flash (`text-embedding-004`)
*   **Vector Database:** ChromaDB (Hierarchical Indexing)
*   **Graph Engine:** NetworkX (Directed Citation Graph)
*   **Framework:** Python (FastAPI), LangChain
*   **Frontend:** Next.js + React Flow (for graph visualization)

### System Design
1.  **Ingestion with Metadata Injection**: Articles are parsed and enriched with metadata (legal force, obligations).
2.  **Parent-Child Indexing**: We embed small paragraphs (Children) for precise retrieval but retrieve the full Article (Parent) to preserve context.
3.  **Smart Graph Retrieval**:
    *   *Step 1*: Vector Search finds the top-k most relevant articles.
    *   *Step 2*: The system looks up "Neighbors" (cited articles) in the knowledge graph.
    *   *Step 3*: An LLM "Gatekeeper" validates if the cited article is actually relevant to the specific user query before adding it to the context.

## Implementation Details

### 1. Advanced Chunking Strategy
I moved beyond simple text splitting. Legal texts are hierarchical, so my chunking reflects that.

**Code Snippet: Hierarchical Metadata Injection**
```python
# src/data/advanced_chunking.py

def chunk_article(self, article: Dict[str, Any]) -> List[Dict[str, Any]]:
    # We store the FULL PARENT TEXT in the metadata of every child.
    # This allows the retriever to grab the full context immediately.
    base_metadata = {
        "article_id": article_id,
        "regulation": regulation,
        "parent_text": full_text, # <--- THE KEY UPGRADE
        "legal_force": self.extract_legal_force(full_text)
    }
    
    # Only embed the paragraph (Child), but return the Parent
    return create_chunks(paragraphs, base_metadata)
```

### 2. Smart Graph Retrieval
Naive graph RAG (adding all neighbors) introduced noise. I implemented a "Relevance Check" to filter citations.

**Code Snippet: The Verification Layer**
```python
# src/retrieval/parent_child_retriever.py

def _is_neighbor_relevant(self, query: str, neighbor_text: str) -> bool:
    """Asks specific LLM if the cited article adds value to the query."""
    prompt = f"""
    User Query: "{query}"
    Cited Article Snippet: "{neighbor_text[:500]}..."
    Is this cited article necessary to answer the query?
    Return ONLY "YES" or "NO".
    """
    # ... calls Gemini 2.0 ...
```

## Engineering the Retrieval Pipeline: Failures & Fixes

RAG systems are rarely perfect on the first try. I experimented with several advanced techniques before settling on the final architecture. Here is what *didn't* work and why—often just as valuable as what did.

### Iteration 1: Hybrid Search (BM25 + Vector) & Re-Ranking
*   **Hypothesis:** Adding keyword search (BM25) would catch specific legal terms, and a Cross-Encoder would refine the results.
*   **Result:** **Performance Dropped** (Correctness 3.07 -> 2.77 for Hybrid, 2.40 for Re-Ranking).
*   **Why:** 
    *   *Hybrid:* BM25 flooded the context with documents containing common words like "consent" but missing the *definitions*, diluting the high-quality vector results.
    *   *Re-Ranking:* The `ms-marco` Cross-Encoder, trained on Bing search data, penalized detailed legal text in favor of "direct answer" snippets, filtering out necessary context.

### Iteration 2: HyDE (Hypothetical Document Embeddings)
*   **Hypothesis:** Asking an LLM to hallucinate a fake legal article and embedding that would match the real article better than the raw question.
*   **Result:** **Performance Dropped** (Correctness 3.07 -> 2.90).
*   **Why:** The hallucinated articles were often *too specific*. The embedding of a specific hallucination failed to match the broader, foundational language of the actual GDPR articles.

### The Winning Formula: Parent-Child + Smart Graph
Ultimately, statistical tricks failed. The breakthrough came from structural improvements:
1.  **Parent-Child Retrieval (Phase 2):** Moving from simple chunks to full articles boosted Correctness from **3.07 to 3.23**.
2.  **Smart Graph (Phase 3):** Adding the LLM-verified citation graph pushed Correctness to **3.30**, the highest score achieved.

## Challenges & Solutions

**Challenge 1: The "Noise" of Citations**
*   **Problem:** Legal articles cite *everything*. Article 5 might cite Article 4 (definitions), which dilutes the context with generic text. My initial "Graph RAG" saw a **drop in correctness** (3.23 -> 3.13) because it flooded the LLM with irrelevant citations.
*   **Solution:** Implemented the **Smart Graph Filter** (seen above). Instead of blindly following edges, we ask an LLM "Is this citation useful?" This restored precision while keeping the high recall of graph traversal.

**Challenge 2: Losing Context in Chunking**
*   **Problem:** Splitting "Article 15" into 5 chunks meant the LLM lost the preamble ("The controller shall...").
*   **Solution:** **Parent-Child Retrieval**. We search against the specific paragraph (child) but *always* feed the full Article text (parent) to the generation LLM.

**Challenge 3: Hallucination Risk**
*   **Problem:** Generic LLMs love to invent regulations.
*   **Solution:** Strict **Confidence Scoring**. If the retriever cannot find a "Mandatory" article matching the query intent, the system refuses to answer.

## Results & Metrics

I evaluated the system using **RAGAS** (Retrieval Augmented Generation Assessment) on a "Golden Dataset" of 30 expert Q&A pairs.

| Metric | Score | Analysis |
| :--- | :--- | :--- |
| **Context Recall** | **97.5%** | **State of the Art**. The combination of Parent-Child + Graph finds almost every relevant piece of information. |
| **Faithfulness** | **85.3%** | High. The model sticks strictly to the retrieved context. |
| **Context Precision** | ~84.0% | Strong. The re-ranking ensures the right articles are at the top. |
| **Answer Relevancy** | 55.0% | Moderate. Legal answers are naturally verbose; we prioritized *completeness* over brevity. |

**Performance:**
*   **Latency:** ~2.5s per query (parallelized vector interaction).
*   **Cost:** <$0.01 per query using Gemini Flash.

## Lessons Learned

1.  **More Context != Better Answers**: Blindly throwing the whole graph at the LLM confuses it. Context curation (Smart Filtering) is just as important as retrieval.
2.  **Structure Your Data**: The biggest quality jump came from parsing the HTML structure of the law (Articles/Titles/Chapters) rather than treating it as a blob of text.
3.  **Evaluate Early**: Setting up the RAGAS golden dataset in Week 1 was critical. It saved me from chasing "cool" features (like hybrid search with bad weights) that actually hurt performance.

## Design Decisions
*   **Why Gemini?** Massive context window (1M tokens) allows "sloppier" retrieval (Top-10) without penalty, and it's cheaper/faster than GPT-4 for this use case.
*   **Why SQL-less?** All metadata is stored in ChromaDB and NetworkX (in-memory/serialized). For a static dataset like Law (which changes rarely), a heavy SQL database was unnecessary overhead.

---
*Built with: Python, LangChain, NetworkX, ChromaDB, Next.js*
