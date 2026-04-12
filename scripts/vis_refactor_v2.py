import os
import json
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Config aesthetics
sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})
plt.rcParams['svg.fonttype'] = 'none'

PUBLIC_DIR = Path("web/public")
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

def parse_matpower(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    buses = []
    edges = []
    
    in_bus = False
    in_branch = False
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('%'):
            continue
            
        if line.startswith('mpc.bus = ['):
            in_bus = True
            continue
        elif line.startswith('mpc.branch = ['):
            in_branch = True
            continue
        
        if line == '];':
            in_bus = False
            in_branch = False
            continue
            
        if in_bus:
            parts = line.split()
            # first token is bus id
            bus_id = int(parts[0])
            buses.append(bus_id)
            
        if in_branch:
            parts = line.split()
            fbus = int(parts[0])
            tbus = int(parts[1])
            edges.append((fbus, tbus))
            
    G = nx.Graph()
    G.add_nodes_from(buses)
    G.add_edges_from(edges)
    return G

def draw_topology_sg(G):
    print("Generating Kamada Kawai grid topology...")
    pos = nx.kamada_kawai_layout(G)
    
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    ax.axis('off')
    
    # Calculate degree for sizing and coloring
    degrees = dict(G.degree())
    node_sizes = [min(d * 18, 150) for n, d in G.degree()]
    
    # Edges
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.06, edge_color="#334155", width=0.3)
    
    # Base nodes
    nx.draw_networkx_nodes(
        G, pos, ax=ax, node_size=[s/1.5 for s in node_sizes], 
        node_color="#0284c7", alpha=0.1, edgecolors="none"
    )
    
    # Hub nodes Exteme Glow
    hubs = [n for n, d in degrees.items() if d >= 4]
    nx.draw_networkx_nodes(
        G, pos, nodelist=hubs, ax=ax, node_size=[degrees[n] * 50 for n in hubs], 
        node_color="#0ea5e9", alpha=0.15, edgecolors="none"
    )
    nx.draw_networkx_nodes(
        G, pos, nodelist=hubs, ax=ax, node_size=[degrees[n] * 20 for n in hubs], 
        node_color="#38bdf8", alpha=0.4, edgecolors="none"
    )
    nx.draw_networkx_nodes(
        G, pos, nodelist=hubs, ax=ax, node_size=[degrees[n] * 8 for n in hubs], 
        node_color="#e0f2fe", alpha=1.0, edgecolors="#ffffff", linewidths=1.0
    )
    
    out_path = PUBLIC_DIR / "grid_topology_full118.svg"
    plt.savefig(out_path, transparent=True, bbox_inches='tight', pad_inches=0)
    plt.close()
    print(f"Saved {out_path}")

def draw_graphsage_aggregation(G):
    print("Generating GraphSAGE Aggregation...")
    pos = nx.kamada_kawai_layout(G)
    
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    # Set completely transparent
    ax.axis('off')
    
    # Base dull graph
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.15, edge_color="#475569", width=0.5)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=10, node_color="#475569", alpha=0.2)
    
    # Target node: e.g. Node 80 (high degree) or Node 69 (slack)
    target = 80
    if target not in G.nodes:
        target = list(G.nodes)[0]
        
    one_hop = list(G.neighbors(target))
    two_hop = []
    for n in one_hop:
        two_hop.extend(list(G.neighbors(n)))
    two_hop = list(set(two_hop) - set(one_hop) - {target})
    
    # Plot 2-hop edges and nodes
    two_hop_edges = [(u, v) for u, v in G.edges if ((u in two_hop and v in one_hop) or (v in two_hop and u in one_hop))]
    nx.draw_networkx_edges(G, pos, edgelist=two_hop_edges, ax=ax, alpha=0.6, edge_color="#0ea5e9", width=1.5)
    nx.draw_networkx_nodes(G, pos, nodelist=two_hop, ax=ax, node_size=40, node_color="#0ea5e9", alpha=0.8)
    
    # Plot 1-hop edges and nodes
    one_hop_edges = [(target, n) for n in one_hop]
    nx.draw_networkx_edges(G, pos, edgelist=one_hop_edges, ax=ax, alpha=0.9, edge_color="#10b981", width=2.5)
    nx.draw_networkx_nodes(G, pos, nodelist=one_hop, ax=ax, node_size=80, node_color="#10b981", alpha=0.95)
    
    # Plot target node
    nx.draw_networkx_nodes(G, pos, nodelist=[target], ax=ax, node_size=160, node_color="#facc15", edgecolors="#ffffff", linewidths=2.5)
    
    # Annotate target node
    cx, cy = pos[target]
    ax.text(cx + 0.05, cy + 0.05, f"Target Node {target}\n(Aggregation Center)", color="#1e293b", fontsize=9, fontweight='bold',
            bbox=dict(facecolor='#f8fafc', alpha=0.8, edgecolor='#e2e8f0', boxstyle='round,pad=0.3'))
    ax.text(cx - 0.2, cy - 0.2, f"1-hop Neighbors (Weight = W1)", color="#10b981", fontsize=9, fontweight='bold')
    ax.text(cx - 0.35, cy + 0.3, f"2-hop Neighbors (Weight = W2)", color="#0ea5e9", fontsize=9, fontweight='bold')
    
    out_path = PUBLIC_DIR / "graphsage_aggregation.svg"
    plt.savefig(out_path, transparent=True, bbox_inches='tight', pad_inches=0)
    plt.close()
    print(f"Saved {out_path}")

def generate_kg_json(G):
    print("Generating KG JSON (100+ instances)...")
    
    nodes = []
    links = []
    
    # Add Buses (Stations)
    degrees = dict(G.degree())
    for n in G.nodes:
        deg = degrees[n]
        node_type = "Transmission Hub" if deg >= 4 else "Substation"
        color = "#8b5cf6" if deg >= 4 else "#38bdf8"
        size = 25 if deg >= 4 else 12
        nodes.append({
            "name": f"Bus_{n}",
            "value": node_type,
            "category": node_type,
            "itemStyle": {"color": color},
            "symbolSize": size
        })
        
    # Add lines (connected_to)
    for u, v in G.edges:
        links.append({
            "source": f"Bus_{u}",
            "target": f"Bus_{v}",
            "value": "connected_to"
        })
        
    # Add some mock Transformers & Regions for richness
    regions = ["Region_North", "Region_South", "Region_East", "Region_West", "Region_Central"]
    for r in regions:
        nodes.append({
            "name": r,
            "value": "Geographic Region",
            "category": "Region",
            "itemStyle": {"color": "#ec4899"},
            "symbolSize": 45
        })
    
    # Assign buses to regions randomly
    np.random.seed(42)
    for n in G.nodes:
        region = np.random.choice(regions)
        links.append({
            "source": f"Bus_{n}",
            "target": region,
            "value": "located_in"
        })
        
        # 30% chance of having a transformer bank
        if np.random.rand() < 0.3:
            xfmr = f"XFMR_{n}"
            nodes.append({
                "name": xfmr,
                "value": "Transformer Bank",
                "category": "Transformer",
                "itemStyle": {"color": "#facc15"},
                "symbolSize": 15
            })
            links.append({
                "source": xfmr,
                "target": f"Bus_{n}",
                "value": "stepped_down_at"
            })
            
    # Add Magnetometers
    mags = ["MAG_BOU", "MAG_FRD", "MAG_NEW"]
    for m in mags:
        nodes.append({
            "name": m,
            "value": "Magnetometer",
            "category": "Magnetometer",
            "itemStyle": {"color": "#14b8a6"},
            "symbolSize": 35
        })
    
    # Magnetometers drive regions
    links.append({"source": "MAG_BOU", "target": "Region_North", "value": "drives_field"})
    links.append({"source": "MAG_BOU", "target": "Region_West", "value": "drives_field"})
    links.append({"source": "MAG_FRD", "target": "Region_East", "value": "drives_field"})
    links.append({"source": "MAG_FRD", "target": "Region_South", "value": "drives_field"})
    links.append({"source": "MAG_NEW", "target": "Region_Central", "value": "drives_field"})
    
    kg_data = {
        "nodes": nodes,
        "links": links
    }
    
    out_path = PUBLIC_DIR / "kg_instances_real.json"
    with open(out_path, "w") as f:
        json.dump(kg_data, f, indent=2)
    print(f"Saved {out_path} with {len(nodes)} nodes and {len(links)} links")

if __name__ == "__main__":
    filepath = "data/raw/grid_cases/matpower_case118_official.m"
    G = parse_matpower(filepath)
    print(f"Parsed {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    draw_topology_sg(G)
    draw_graphsage_aggregation(G)
    generate_kg_json(G)
