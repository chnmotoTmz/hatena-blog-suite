import os
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
import logging
import json # For exporting graph data

# Ensure a non-GUI backend for Matplotlib if running in headless environments
try:
    matplotlib.use('Agg')
except ImportError: # Can happen if tkinter is not installed etc.
    pass
except Exception: # Other potential errors with matplotlib.use()
    pass


logger = logging.getLogger(__name__)

class KnowledgeGraphManager:
    """
    Manages a knowledge graph using NetworkX.
    Allows adding nodes (e.g., articles, entities) and edges (relationships),
    performing basic analysis, and visualizing the graph.
    """

    def __init__(self, graph_attributes: Optional[Dict[str, Any]] = None):
        """
        Initializes the KnowledgeGraphManager.

        Args:
            graph_attributes: Optional dictionary of attributes for the graph itself
                              (e.g., {"name": "My Knowledge Graph", "created_by": "AI"}).
        """
        self.graph = nx.Graph(**(graph_attributes or {}))
        logger.info(f"KnowledgeGraph initialized with attributes: {self.graph.graph}")

    def add_node(self, node_id: Any, **attributes: Any) -> bool:
        """
        Adds a node to the graph.

        Args:
            node_id: The unique identifier for the node.
            **attributes: Keyword arguments representing node attributes (e.g., type="article", title="...").

        Returns:
            True if node was added or already existed, False on error.
        """
        if node_id is None:
            logger.error("Node ID cannot be None.")
            return False
        try:
            self.graph.add_node(node_id, **attributes)
            # logger.debug(f"Node '{node_id}' added/updated with attributes: {attributes}")
            return True
        except Exception as e:
            logger.error(f"Error adding node '{node_id}': {e}")
            return False

    def add_edge(self, node1_id: Any, node2_id: Any, weight: float = 1.0, **attributes: Any) -> bool:
        """
        Adds an edge between two nodes.

        Args:
            node1_id: Identifier of the first node.
            node2_id: Identifier of the second node.
            weight: Weight of the edge (e.g., similarity score, strength of relationship).
            **attributes: Keyword arguments representing edge attributes (e.g., type="related_to").

        Returns:
            True if edge was added/updated, False on error.
        """
        if node1_id is None or node2_id is None:
            logger.error("Node IDs for an edge cannot be None.")
            return False
        if not self.graph.has_node(node1_id):
            logger.warning(f"Node '{node1_id}' not found in graph. Adding edge might be problematic or create the node.")
            # self.add_node(node1_id) # Optionally auto-add nodes
        if not self.graph.has_node(node2_id):
            logger.warning(f"Node '{node2_id}' not found in graph. Adding edge might be problematic or create the node.")
            # self.add_node(node2_id)

        try:
            self.graph.add_edge(node1_id, node2_id, weight=weight, **attributes)
            # logger.debug(f"Edge added/updated between '{node1_id}' and '{node2_id}' with weight {weight}, attributes: {attributes}")
            return True
        except Exception as e:
            logger.error(f"Error adding edge between '{node1_id}' and '{node2_id}': {e}")
            return False

    def get_node_attributes(self, node_id: Any) -> Optional[Dict[str, Any]]:
        """Retrieves attributes of a specific node."""
        if not self.graph.has_node(node_id):
            logger.warning(f"Node '{node_id}' not found.")
            return None
        return self.graph.nodes[node_id]

    def get_edge_attributes(self, node1_id: Any, node2_id: Any) -> Optional[Dict[str, Any]]:
        """Retrieves attributes of a specific edge."""
        if not self.graph.has_edge(node1_id, node2_id):
            logger.warning(f"Edge between '{node1_id}' and '{node2_id}' not found.")
            return None
        return self.graph.edges[node1_id, node2_id]

    def get_neighbors(self, node_id: Any) -> List[Any]:
        """Returns a list of neighbors for a given node."""
        if not self.graph.has_node(node_id):
            logger.warning(f"Node '{node_id}' not found for getting neighbors.")
            return []
        return list(self.graph.neighbors(node_id))

    def calculate_basic_stats(self) -> Dict[str, Any]:
        """Calculates basic statistics of the graph."""
        if not self.graph:
            return {"error": "Graph not initialized."}
        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()
        stats = {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "is_connected": nx.is_connected(self.graph) if num_nodes > 0 else True,
            "num_connected_components": nx.number_connected_components(self.graph) if num_nodes > 0 else 0,
            "density": nx.density(self.graph) if num_nodes > 0 else 0.0,
        }
        if num_nodes > 0 and stats["num_connected_components"] > 0:
             largest_cc = max(nx.connected_components(self.graph), key=len, default=set())
             stats["largest_component_size"] = len(largest_cc)
        else:
            stats["largest_component_size"] = 0

        return stats

    def calculate_centrality_measures(self, top_n: int = 5) -> Dict[str, List[Tuple[Any, float]]]:
        """
        Calculates common centrality measures for nodes.

        Args:
            top_n: The number of top nodes to return for each measure.

        Returns:
            A dictionary where keys are centrality measure names and values are lists
            of (node_id, score) tuples for the top_n nodes.
        """
        if self.graph.number_of_nodes() == 0:
            return {"message": "Graph is empty, no centrality measures to calculate."}

        centralities = {}
        try:
            degree_centrality = nx.degree_centrality(self.graph)
            centralities["degree_centrality"] = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:top_n]

            if self.graph.number_of_nodes() < 300: # Betweenness can be slow for large graphs
                betweenness_centrality = nx.betweenness_centrality(self.graph)
                centralities["betweenness_centrality"] = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:top_n]
            else:
                logger.warning("Skipping betweenness centrality for large graph ( >300 nodes).")


            # Eigenvector centrality can fail on graphs with multiple components
            if nx.is_connected(self.graph):
                 try:
                    eigenvector_centrality = nx.eigenvector_centrality_numpy(self.graph) # Using numpy version
                    centralities["eigenvector_centrality"] = sorted(eigenvector_centrality.items(), key=lambda x: x[1], reverse=True)[:top_n]
                 except (nx.NetworkXError, nx.NetworkXException, ValueError) as e: # Catch specific errors for eigenvector
                    logger.warning(f"Could not compute eigenvector centrality: {e}. Graph might be disconnected or have other issues.")

            closeness_centrality = nx.closeness_centrality(self.graph)
            centralities["closeness_centrality"] = sorted(closeness_centrality.items(), key=lambda x: x[1], reverse=True)[:top_n]

        except Exception as e:
            logger.error(f"Error calculating centrality measures: {e}", exc_info=True)
            # Return what has been computed so far
        return centralities

    def find_communities(self, algorithm: str = "louvain", **kwargs) -> Optional[List[Set[Any]]]:
        """
        Finds communities in the graph using a specified algorithm.
        Currently supports 'louvain' (via networkx.community).

        Args:
            algorithm: The community detection algorithm to use. Currently "louvain".
            **kwargs: Additional arguments for the community detection algorithm.

        Returns:
            A list of sets, where each set contains the node IDs of a community.
            Returns None if algorithm is not supported or an error occurs.
        """
        if self.graph.number_of_nodes() == 0:
            logger.info("Graph is empty, no communities to find.")
            return []

        if algorithm == "louvain":
            try:
                # Ensure networkx.community is available (it's part of networkx)
                # The Louvain implementation in networkx is under `nx.community.louvain_communities`
                # or more generally `nx.community.greedy_modularity_communities` for an alternative
                # For Louvain specifically, you might need an external library if nx's version is limited.
                # Let's use a common one: greedy_modularity_communities as a stand-in or if louvain is not directly exposed.
                # communities_generator = nx.community.greedy_modularity_communities(self.graph, **kwargs)
                # communities = [set(c) for c in communities_generator]

                # NetworkX 2.x and later has louvain_communities directly
                if hasattr(nx.community, 'louvain_communities'):
                    communities_generator = nx.community.louvain_communities(self.graph, weight='weight', **kwargs)
                    communities = [set(c) for c in communities_generator] # Convert frozensets to sets
                    logger.info(f"Found {len(communities)} communities using Louvain algorithm.")
                    return communities
                else: # Fallback if louvain_communities is not found (older nx or different structure)
                    logger.warning("nx.community.louvain_communities not found. Trying greedy_modularity_communities.")
                    communities_generator = nx.community.greedy_modularity_communities(self.graph, **kwargs)
                    communities = [set(c) for c in communities_generator]
                    logger.info(f"Found {len(communities)} communities using greedy_modularity_communities.")
                    return communities

            except Exception as e:
                logger.error(f"Error finding communities with {algorithm}: {e}", exc_info=True)
                return None
        else:
            logger.error(f"Unsupported community detection algorithm: {algorithm}")
            return None

    def visualize_graph(
        self,
        output_filepath: str = "knowledge_graph.png",
        layout_type: str = "spring", # spring, circular, random, kamada_kawai
        show_labels: bool = True,
        node_size_multiplier: int = 300,
        font_size: int = 8,
        fig_size: Tuple[int, int] = (15, 10),
        node_colors: Optional[Any] = None, # Can be a single color string or a list/dict of colors
        edge_weights_as_alpha: bool = True
    ):
        """
        Generates and saves a visualization of the graph.

        Args:
            output_filepath: Path to save the image file.
            layout_type: Layout algorithm for node positioning.
            show_labels: Whether to display node labels.
            node_size_multiplier: Base size for nodes (can be scaled by degree).
            font_size: Font size for labels.
            fig_size: Figure size (width, height) in inches.
            node_colors: Color(s) for the nodes. Can be a single color string,
                         a list of colors (one per node in graph.nodes() order),
                         or a dictionary mapping community_id to color and provide node_to_community_map.
            edge_weights_as_alpha: If True, edge transparency is based on 'weight' attribute.
        """
        if self.graph.number_of_nodes() == 0:
            logger.info("Graph is empty. Nothing to visualize.")
            return

        plt.figure(figsize=fig_size)

        # Determine layout
        if layout_type == "spring":
            pos = nx.spring_layout(self.graph, k=0.15, iterations=50)
        elif layout_type == "circular":
            pos = nx.circular_layout(self.graph)
        elif layout_type == "kamada_kawai":
            pos = nx.kamada_kawai_layout(self.graph)
        else: # random
            pos = nx.random_layout(self.graph, seed=42)

        # Node sizes based on degree (optional)
        degrees = [self.graph.degree(n) for n in self.graph.nodes()]
        node_sizes = [d * node_size_multiplier/5 + node_size_multiplier/2 for d in degrees] if degrees else node_size_multiplier


        # Edge alpha based on weight
        edge_alpha_values = 0.3
        if edge_weights_as_alpha:
            weights = [self.graph.edges[u,v].get('weight', 0.1) for u,v in self.graph.edges()]
            if weights: # Normalize weights if they vary a lot
                min_w, max_w = min(weights), max(weights)
                if max_w > min_w:
                    edge_alpha_values = [(w - min_w) / (max_w - min_w) * 0.7 + 0.1 for w in weights] # Scale to 0.1-0.8
                else: # All weights are same
                    edge_alpha_values = [0.3] * len(weights)


        nx.draw_networkx_nodes(self.graph, pos, node_size=node_sizes, node_color=node_colors if node_colors else 'skyblue', alpha=0.8)
        nx.draw_networkx_edges(self.graph, pos, alpha=edge_alpha_values, edge_color='gray')

        if show_labels:
            # For very large graphs, labels can be overwhelming. Consider showing only for top N nodes.
            labels = {n: str(n)[:20] for n in self.graph.nodes()} # Truncate long labels
            nx.draw_networkx_labels(self.graph, pos, labels=labels, font_size=font_size)

        plt.title(self.graph.graph.get("name", "Knowledge Graph Visualization"), fontsize=16)
        plt.axis('off')

        try:
            plt.savefig(output_filepath, dpi=300, bbox_inches='tight')
            logger.info(f"Graph visualization saved to {output_filepath}")
        except Exception as e:
            logger.error(f"Failed to save graph visualization: {e}")
        finally:
            plt.close() # Close the figure to free memory

    def export_to_json(self, filepath: str = "knowledge_graph_export.json"):
        """Exports the graph data to a JSON format (node-link data)."""
        try:
            data = nx.node_link_data(self.graph)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Graph exported to JSON (node-link format) at {filepath}")
        except Exception as e:
            logger.error(f"Error exporting graph to JSON: {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("--- Testing KnowledgeGraphManager ---")

    # Create a manager
    kg_manager = KnowledgeGraphManager(graph_attributes={"name": "Test KG", "version": "1.0"})

    # Add nodes (e.g., articles)
    articles_data = {
        "art1": {"title": "Introduction to Python", "type": "article", "tags": ["python", "beginner"]},
        "art2": {"title": "Advanced Python Techniques", "type": "article", "tags": ["python", "advanced"]},
        "art3": {"title": "Data Science with Python", "type": "article", "tags": ["python", "data_science"]},
        "art4": {"title": "Web Development with Django", "type": "article", "tags": ["python", "web", "django"]},
        "art5": {"title": "Understanding Algorithms", "type": "concept", "tags": ["cs", "algorithms"]},
    }
    for node_id, attrs in articles_data.items():
        kg_manager.add_node(node_id, **attrs)

    # Add edges (e.g., relationships based on similarity or links)
    edges_data = [
        ("art1", "art2", 0.7, {"type": "prerequisite"}),
        ("art1", "art3", 0.6, {"type": "related_topic"}),
        ("art2", "art3", 0.8, {"type": "uses_concepts_from"}),
        ("art2", "art4", 0.5, {"type": "related_application"}),
        ("art3", "art5", 0.9, {"type": "foundational_to"}), # art5 is a concept
    ]
    for u, v, w, attrs in edges_data:
        kg_manager.add_edge(u, v, weight=w, **attrs)
    kg_manager.add_edge("art1", "art5", 0.4, type="mentions") # Add one more

    print("\\n--- Basic Graph Stats ---")
    stats = kg_manager.calculate_basic_stats()
    print(json.dumps(stats, indent=2))
    assert stats["num_nodes"] == 5
    assert stats["num_edges"] == 6

    print("\\n--- Centrality Measures (Top 3) ---")
    centralities = kg_manager.calculate_centrality_measures(top_n=3)
    for measure, nodes in centralities.items():
        print(f"  {measure.replace('_', ' ').title()}:")
        for node_id, score in nodes:
            print(f"    - {node_id} ({articles_data.get(node_id,{}).get('title','N/A')}): {score:.3f}")

    print("\\n--- Community Detection (Louvain) ---")
    communities = kg_manager.find_communities()
    if communities:
        print(f"Found {len(communities)} communities:")
        for i, community_nodes in enumerate(communities):
            community_titles = [articles_data.get(n, {}).get('title', n) for n in community_nodes]
            print(f"  Community {i+1}: {community_titles}")

    # Assign colors based on communities for visualization
    node_color_map = {}
    community_colors = ['red', 'blue', 'green', 'yellow', 'purple']
    if communities:
        for i, community_set in enumerate(communities):
            color = community_colors[i % len(community_colors)]
            for node_id_in_comm in community_set:
                node_color_map[node_id_in_comm] = color

    # Convert map to list in order of graph.nodes() for nx.draw
    ordered_node_colors = [node_color_map.get(n, 'grey') for n in kg_manager.graph.nodes()]


    print("\\n--- Visualizing Graph ---")
    viz_path = "test_knowledge_graph.png"
    kg_manager.visualize_graph(
        output_filepath=viz_path,
        show_labels=True,
        node_colors=ordered_node_colors,
        node_size_multiplier=500 # Make nodes larger for small graph
    )
    if os.path.exists(viz_path):
        print(f"Graph visualization saved to {viz_path}")
    else:
        print(f"Graph visualization FAILED to save at {viz_path}")

    print("\\n--- Exporting Graph to JSON ---")
    json_export_path = "test_kg_export.json"
    kg_manager.export_to_json(filepath=json_export_path)
    if os.path.exists(json_export_path):
        print(f"Graph exported to {json_export_path}")
        # 간단한 내용 검증
        with open(json_export_path, 'r') as f:
            exported_data = json.load(f)
        assert len(exported_data.get('nodes',[])) == stats["num_nodes"]
        assert len(exported_data.get('links',[])) == stats["num_edges"]


    print("\\nKnowledgeGraphManager tests finished.")
