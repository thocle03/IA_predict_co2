import sumolib
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET_FILE = os.path.join(BASE_DIR, "data", "networks", "paris.net.xml")

print(f"Testing {NET_FILE}")
if not os.path.exists(NET_FILE):
    print("File not found!")
    sys.exit(1)

try:
    net = sumolib.net.readNet(NET_FILE)
    print(f"Nodes: {len(net.getNodes())}")
    print(f"Edges: {len(net.getEdges())}")
    
    for i, edge in enumerate(net.getEdges()):
        if i > 5: break
        print(f"Edge {edge.getID()}: From {edge.getFromNode().getID()} To {edge.getToNode().getID()}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
