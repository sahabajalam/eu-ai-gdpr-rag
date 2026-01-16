# Project Task Tracker

## Week 1: Foundation
- [x] Download GDPR HTML from gdpr-info.eu
- [x] Download EU AI Act from EUR-Lex
- [x] Parse both into structured JSON format
- [x] Manually read 10 key articles (5 GDPR + 5 AI Act)
- [x] Create 10 GDPR questions with ground truth
- [x] Create 10 EU AI Act questions with ground truth
- [x] Create 10 cross-regulation questions with ground truth
- [x] Set up GitHub repository / Project Initialization
- [x] Initialize project structure
- [x] Write initial README

## Week 2: Basic RAG
- [x] Install dependencies (langchain, chromadb, openai)
- [x] Set up .env with API keys (Created .env.example)
- [x] Implement chunking strategy
- [x] Create vector store with metadata
- [x] Build query classifier (GDPR/AI Act/Both)
- [x] Implement basic retrieval
- [x] Design and test prompt template
- [x] Connect LLM for generation
- [x] Test on 10 golden questions
- [x] Calculate baseline accuracy

## Week 3: Advanced Retrieval
- [x] Install rank-bm25 library
- [x] Implement BM25 search (Hybrid Retriever)
- [x] Install sentence-transformers for re-ranking
- [x] Implement cross-encoder re-ranking
- [x] A/B test: baseline vs hybrid vs hybrid+rerank
- [x] Document improvements in README
- [x] Measure accuracy improvement
- [x] Optimize query latency (Reverted to fast Baseline)
- [x] Implement HyDE (Hypothetical Document Embeddings)
- [x] Evaluate HyDE vs Baseline (Result: 2.90, Baseline wins)

## Phase 2: Metadata & Prompts
- [x] Implement Parent-Child Chunking (Article -> Paragraphs)
- [x] Extract Legal Metadata (Obligations, Force)
- [x] Re-ingest data into new Chroma Collection
- [x] Implement Parent-Child Retriever
- [x] Design "Legal Compliance" System Prompt (Chain of Thought)
- [x] Evaluate Phase 2 vs Baseline (Result: 3.23 Correctness, New Best)

## Phase 3: Graph-Enhanced Retrieval (NetworkX)
- [x] Implement `GraphBuilder` (Extract citations -> Build NetworkX Graph)
- [x] Integrate Graph Traversal into `ParentChildRetriever`
- [x] Evaluate Phase 3 (Graph) vs Phase 2 (Result: 3.30, Winner! Smart Graph)


## Week 4: Evaluation
- [x] Install RAGAS library
- [x] Convert golden dataset to RAGAS format
- [x] Run RAGAS evaluation (4 metrics)
- [x] Analyze low-scoring questions
- [x] Implement confidence scoring function
- [x] Set confidence threshold (0.60)
- [x] Add refusal mechanism
- [ ] Set up LangSmith account and tracing
- [ ] Generate evaluation report
- [ ] Create visualization of results

## Week 5: Cross-Regulation
- [x] Implement dual retrieval (GDPR + AI Act)
- [x] Design cross-regulation synthesis prompt
- [x] Build overlap detection logic (Prompt Engineering)
- [x] Build conflict detection logic (Lex Specialis Prompt)
- [x] Test on 10 cross-regulation questions
- [x] Refine synthesis based on results
- [x] Add comparison feature (Implied in synthesis)
- [x] Implement cross-reference detection
- [ ] Measure cross-regulation accuracy
- [ ] Update evaluation report

## Week 6: Polish (Vite + React + FastAPI)
- [x] Install FastAPI & Uvicorn (Backend)
- [x] Create API Endpoints (`/chat`, `/graph`)
- [x] Initialize Vite Project (`ui/`)
- [x] Install Tailwind & Shadcn/UI
- [x] Build Chat Interface (React)
- [x] Implement Confidence Meter UI
- [x] Implement "Smart Graph" Visualization (React Flow)
- [x] Integrate Frontend with Backend API
- [x] Migrate to Next.js for Performance
- [x] Implement Streaming Responses (Server-Sent Events)
- [x] Add "Deep Dive" Modal for Citations
- [x] Add Regulation Filter (GDPR / AI Act)
- [x] Implement History Navigation (View Sources for past messages)
- [ ] Add User Feedback (Thumbs Up/Down)
- [ ] Write demo video script
- [ ] Record and edit demo video (3-5 min)
- [ ] Upload video to YouTube
- [x] Write comprehensive README
- [ ] Create architecture documentation
- [ ] Finalize evaluation report
- [ ] Final repository polish
