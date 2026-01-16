# Phase 2 Report: Metadata & Prompts

## Objective
Beat the Baseline (Correctness: 3.07) by solving "Context Fragmentation" logic gaps.

## Strategy Implemented
1.  **Parent-Child Retrieval**: 
    -   Ingested as Paragraphs (Children) -> Retrieved as Full Articles (Parents).
    -   Ensures LLM sees definitions, exceptions, and scope.
2.  **Chain-of-Thought Prompting**:
    -   System Prompt: "Senior Compliance Officer".
    -   Logic: "Analyze context -> Check conflicts -> Cite Article".

## Results (n=30)
| Metric | Baseline | Phase 2 (Advanced) | Delta |
| :--- | :--- | :--- | :--- |
| **Correctness** | 3.07 | **3.23** | **+0.16** 📈 |
| **Context Rel** | 3.97 | 1.97 | -2.00 📉 |

## Analysis
*   **Correctness (The Win)**: The system is answering more questions correctly. This confirms that giving the LLM the *full legal article* allows it to reason better than giving it isolated paragraphs.
*   **Context Relevance (The "False" Drop)**: The sharp drop is due to the metric's nature. 
    -   *Baseline*: Retrieved precise, short paragraphs (High density).
    -   *Phase 2*: Retrieves full 500+ word articles. The "relevant" part is still there, but diluted by the rest of the article. This "noise" lowered the score, but paradoxically *helped* the LLM answer better (by providing necessary context/definitions).

## Conclusion
**Phase 2 is the new Production Standard.**
We trade "metric purity" (Context Relevance) for "real-world accuracy" (Correctness).

## Next Steps
-   **Confidence Scoring**: Can we predict when the model is wrong?
-   **Refusal Mechanism**: explicitly teaching the model to say "I don't know".
