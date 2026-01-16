import json
import logging
import re
import networkx as nx
import pickle
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
GRAPH_PATH = Path("data/knowledge_graph.pkl")

class LegalGraphBuilder:
    """
    Builds a directed graph of legal articles based on citations.
    Node: Article ID (or Number)
    Edge: Citation ("Article 5" mentions "Article 6")
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        self.reference_pattern = re.compile(r'Article\s+(\d+)', re.IGNORECASE)
        
    def load_data(self) -> List[Dict[str, Any]]:
        files = ["gdpr_articles.json", "eu_ai_act_articles.json"]
        all_articles = []
        for f in files:
            path = PROCESSED_DIR / f
            if path.exists():
                with open(path, "r", encoding="utf-8") as file:
                    all_articles.extend(json.load(file))
        return all_articles

    def build_graph(self):
        articles = self.load_data()
        logger.info(f"Building graph from {len(articles)} articles...")
        
        # 1. Add Nodes
        # We need a map from "Article Number" to "Article ID" to resolve citations
        # Problem: "Article 5" exists in BOTH GDPR and AI Act.
        # Solution: Composite Key "Regulation_ArticleNumber"
        
        article_map = {}
        
        for art in articles:
            # Create unique node ID
            reg = art.get('regulation', 'Unknown')
            num = art.get('article_number', '0')
            node_id = f"{reg}_{num}"
            
            # Store metadata in node
            self.graph.add_node(
                node_id, 
                title=art.get('title', ''), 
                full_text=art.get('full_text', ''),
                regulation=reg,
                article_number=num
            )
            
            # Index for fast lookup
            # We assume citations are internal to the same regulation implies context
            if reg not in article_map:
                article_map[reg] = {}
            article_map[reg][num] = node_id

        # 2. Add Edges (Citations)
        edge_count = 0
        for art in articles:
            source_reg = art.get('regulation')
            source_num = art.get('article_number')
            source_id = f"{source_reg}_{source_num}"
            
            text = art.get('full_text', '')
            
            # Find all citations
            cited_numbers = self.reference_pattern.findall(text)
            
            for cited_num in cited_numbers:
                if cited_num == source_num:
                    continue # Ignore self-citation
                
                # Resolve citation
                # Assumption: "Article X" refers to the SAME regulation unless specified otherwise.
                # Cross-regulation citation is harder (e.g. "GDPR Article 5" inside AI Act).
                # For now, we link internal citations only.
                
                target_id = article_map.get(source_reg, {}).get(cited_num)
                
                if target_id:
                    self.graph.add_edge(source_id, target_id, type="citation")
                    edge_count += 1
                    
        logger.info(f"Graph built: {self.graph.number_of_nodes()} nodes, {edge_count} edges.")
        
    def save_graph(self):
        with open(GRAPH_PATH, "wb") as f:
            pickle.dump(self.graph, f)
        logger.info(f"Graph saved to {GRAPH_PATH}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    builder = LegalGraphBuilder()
    builder.build_graph()
    builder.save_graph()
