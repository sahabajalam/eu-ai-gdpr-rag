# HyDE (Hypothetical Document Embeddings) Experiment Report

## Method
- **Strategy**: Ask LLM (`gemini-2.0-flash-lite`) to "hallucinate" a legal regulation answering the query, then embed that hallucination to find the real document.
- **Hypothesis**: Bridging the semantic gap between informal questions and formal legal text would improve retrieval.
- **Dataset**: 30 Golden Q&A.

## Results
| Metric | Baseline (Vector) | HyDE | Delta |
| :--- | :--- | :--- | :--- |
| **Correctness** | **3.07** | 2.90 | -0.17 |
| **Context Relevance** | **3.97** | 3.83 | -0.14 |
| **Speed** | Fast | Slow (Extra LLM call) | N/A |

## Analysis
- **Close but no Cigar**: HyDE performed decenty (2.90) but failed to beat the simple Baseline (3.07).
- **Why?**: The hypothetical documents generated were often *too* specific or slightly off-base compared to the broad, foundational Articles in the database. 
- **Example**: 
    - Query: "Do I need consent?"
    - HyDE: "Consent is required pursuant to Article 6..."
    - Actual Doc: "Processing shall be lawful only if... data subject has given consent."
    - The embedding of the *question* actually matched the *broad* article better than the *specific* hallucination.

## Conclusion
We have **reverted to the Baseline**. 
Simple Vector Search remains the most effective and efficient method for this legal dataset.
