import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.graph import create_graph
    graph = create_graph()
    print("Graph created successfully.")
    print("Nodes:", graph.nodes.keys())
except Exception as e:
    print(f"Failed to create graph: {e}")
    sys.exit(1)
