import logging
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import os
import pickle
import networkx as nx
from dotenv import load_dotenv
from google import genai

# Use our custom embedding function
from src.utils.embeddings import GoogleGenAIEmbeddingFunction

load_dotenv()
logger = logging.getLogger(__name__)

# Phase 3 Configuration
COLLECTION_NAME = "eu_ai_gdpr_parent_child"
GRAPH_PATH = "data/knowledge_graph.pkl"

class ParentChildRetriever:
    """
    Retrieves chunks (Children) but returns the Full Article Text (Parent).
    Optionally expands context using Citation Graph (NetworkX).
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
            
        self.chroma_client = chromadb.PersistentClient(
            path="data/chroma",
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        self.embedding_fn = GoogleGenAIEmbeddingFunction(
            api_key=self.api_key,
            model_name="models/text-embedding-004"
        )
        self.collection = self.chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn
        )
        
        # Load Graph
        self.graph = None
        if os.path.exists(GRAPH_PATH):
            logger.info("Loading Legal Citation Graph...")
            with open(GRAPH_PATH, "rb") as f:
                self.graph = pickle.load(f)
        else:
            logger.warning("Graph not found. Retrieval will be vector-only.")


    def _is_neighbor_relevant(self, query: str, neighbor_text: str, neighbor_title: str) -> bool:
        """
        Uses LLM (Gemini) to check if a cited article is relevant to the query.
        """
        prompt = f"""
        You are a legal research assistant.
        Determine if the following CITED ARTICLE is relevant to the USER QUERY.
        
        User Query: "{query}"
        
        Cited Article: "{neighbor_title}"
        Content Snippet: "{neighbor_text[:500]}..."
        
        Is this cited article necessary to answer the query?
        Return ONLY "YES" or "NO".
        """
        try:
            # Use the existing client from __init__ if possible, or create new client
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model='gemini-2.0-flash-lite-preview-02-05',
                contents=prompt
            )
            return "YES" in response.text.strip().upper()
        except Exception as e:
            logger.warning(f"Relevance check failed: {e}")
            return False

    def retrieve(self, query: str, k: int = 5, regulation_filter: str = None) -> List[Dict[str, Any]]:
        """
        1. Embed Query
        2. Vector Search (Hybrid Parent-Child) - Optionally Filtered
        3. Smart Graph Expansion (LLM Valided Citations)
        4. Return Deduplicated Context
        """
        # --- Step 1 & 2: Vector Search ---
        where_clause = {"regulation": regulation_filter} if regulation_filter else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=k * 2,
            where=where_clause
        )
        
        unique_parents = {}
        final_results = []
        
        if results['documents']:
            metadatas = results['metadatas'][0]
            scores = results['distances'][0]
            
            for i, meta in enumerate(metadatas):
                parent_id = meta.get('article_id') 
                
                reg = meta.get('regulation')
                num = meta.get('article_number')
                graph_node_id = f"{reg}_{num}"
                
                if graph_node_id in unique_parents:
                    continue
                
                unique_parents[graph_node_id] = True
                
                final_results.append({
                    "text": meta.get('parent_text', ''),
                    "metadata": meta,
                    "score": scores[i],
                    "match_type": "vector",
                    "node_id": graph_node_id
                })
                
                if len(final_results) >= k:
                    break
        
        # --- Step 3: Smart Graph Expansion ---
        if self.graph:
            expanded_results = []
            logger.info("Checking graph for relevant citations...")
            
            for res in final_results:
                node_id = res['node_id']
                
                if self.graph.has_node(node_id):
                    neighbors = list(self.graph.successors(node_id))
                    
                    for neighbor_id in neighbors:
                        if neighbor_id not in unique_parents:
                            
                            neighbor_data = self.graph.nodes[neighbor_id]
                            n_text = neighbor_data.get('full_text', '')
                            n_title = neighbor_data.get('title', '')
                            
                            # SMART FILTER: Ask LLM if this is relevant
                            if self._is_neighbor_relevant(query, n_text, n_title):
                                logger.info(f"  -> Cited article {neighbor_id} is RELEVANT. Adding.")
                                unique_parents[neighbor_id] = True
                                
                                expanded_results.append({
                                    "text": n_text,
                                    "metadata": {
                                        "title": n_title,
                                        "article_number": neighbor_data.get('article_number'),
                                        "regulation": neighbor_data.get('regulation'),
                                        "source": "graph_citation_smart"
                                    },
                                    "score": 0.0,
                                    "match_type": "graph_smart",
                                    "node_id": neighbor_id
                                })
                            else:
                                 logger.debug(f"  -> Cited article {neighbor_id} filtered out (Irrelevant).")

            
            # Limit total context size
            MAX_EXPANSION = 3
            final_results.extend(expanded_results[:MAX_EXPANSION])
            
        return final_results

    def get_subgraph_for_nodes(self, node_ids: List[str]) -> Dict[str, Any]:
        """
        Returns nodes and edges for visualization (neighbors of retrieved docs).
        """
        if not self.graph:
            return {"nodes": [], "edges": []}
            
        nodes = []
        edges = []
        seen_nodes = set()
        
        # Add primary nodes
        for nid in node_ids:
            if self.graph.has_node(nid):
                if nid not in seen_nodes:
                    data = self.graph.nodes[nid]
                    nodes.append({
                        "id": nid,
                        "label": f"{data.get('regulation')} {data.get('article_number')}",
                        "title": data.get('title', ''),
                        "type": "retrieved"
                    })
                    seen_nodes.add(nid)
                
                # Add outgoing edges (citations)
                for neighbor in self.graph.successors(nid):
                     
                     # Add edge
                     edge_id = f"{nid}-{neighbor}"
                     edges.append({
                         "source": nid,
                         "target": neighbor,
                         "id": edge_id
                     })
                     
                     # Add neighbor node if not seen
                     if neighbor not in seen_nodes and self.graph.has_node(neighbor):
                         n_data = self.graph.nodes[neighbor]
                         nodes.append({
                             "id": neighbor,
                             "label": f"{n_data.get('regulation')} {n_data.get('article_number')}",
                             "title": n_data.get('title', ''),
                             "type": "cited"
                         })
                         seen_nodes.add(neighbor)

        return {"nodes": nodes, "edges": edges}

if __name__ == "__main__":
    retriever = ParentChildRetriever()
    q = "What are the requirements for a DPIA?"
    results = retriever.retrieve(q, k=2)
    
    for r in results:
        print(f"--- [{r['match_type'].upper()}] {r['metadata']['regulation']} Art {r['metadata']['article_number']} ---")
        print(f"Title: {r['metadata']['title']}")
        print(f"Text: {r['text'][:50]}...\n")
