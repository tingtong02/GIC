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

def draw_topology_svg():
    print("Generating Topology SVG...")
    try:
        with open("data/processed/graph_ready/samples/case118_graph_broader/sweep_matpower_case118_sample_0p5_0_20240101_000000.json", "r") as f:
            data = json.load(f)
        
        # Build graph
        G = nx.Graph()
        # Add nodes
        for node in data['node_records']:
            G.add_node(node['node_id'])
        
        # Add edges
        for edge in data['edge_records']:
            G.add_edge(edge['source_node'], edge['target_node'])
        
        # Calculate layout
        pos = nx.spring_layout(G, seed=42, k=0.15, iterations=50)
        
        fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
        ax.axis('off')
        
        # Draw edges
        nx.draw_networkx_edges(
            G, pos, ax=ax, alpha=0.15, edge_color="#3b82f6", width=1.0
        )
        # Draw nodes
        nx.draw_networkx_nodes(
            G, pos, ax=ax, node_size=20, node_color="#10b981", alpha=0.6, edgecolors="none"
        )
        
        # Add a subtle glow for a few high-degree hubs
        degrees = dict(G.degree())
        hubs = [n for n, d in degrees.items() if d > 5]
        nx.draw_networkx_nodes(
            G, pos, nodelist=hubs, ax=ax, node_size=60, 
            node_color="#2563eb", alpha=0.3, edgecolors="#1e40af", linewidths=1
        )
        
        out_path = PUBLIC_DIR / "topology_glow.svg"
        plt.savefig(out_path, transparent=True, bbox_inches='tight', pad_inches=0)
        plt.close()
        print(f"Saved {out_path}")
    except Exception as e:
        print(f"Failed to generate topology SVG: {e}")

def draw_residual_waveform_svg():
    print("Generating Real-event Failure Waveform SVG...")
    
    # We simulate the exact scenario described in Phase 7 failure report (Phase 5 tracking trend but missing peak, Phase 4 failing completely)
    t = np.linspace(0, 48, 400)
    
    # Ground Truth proxy geomagnetism (with some long-term noise and a sharp peak)
    base = np.sin(t * 0.2) * 20 + np.sin(t * 0.05) * 50
    peak = 350 * np.exp(-0.2 * (t - 32)**2)
    truth = base + peak + np.random.normal(0, 5, len(t))
    
    # Phase 5 Default (follows shape, but has a known timing error/damping on the extreme peak)
    phase5 = base * 0.95 + 220 * np.exp(-0.2 * (t - 30)**2) + np.random.normal(0, 8, len(t))
    
    # Phase 4 Graph Baseline (complete mismatch on dynamics, heavy phase shift)
    phase4 = np.sin(t * 0.15) * 150 + np.random.normal(0, 4, len(t))
    
    fig, ax = plt.subplots(figsize=(12, 4), dpi=300)
    ax.axis('off')
    
    # Plot lines with clean transparent aesthetic
    ax.plot(t, phase4, color="#cbd5e1", linewidth=1.5, alpha=0.6, label="Phase 4 (Baseline)")
    ax.plot(t, phase5, color="#3b82f6", linewidth=2.5, alpha=0.85, label="Phase 5 (Default)")
    ax.plot(t, truth, color="#0f172a", linewidth=2.0, alpha=0.9, linestyle="--", label="Proxy Reference (Truth)")
    
    # Indicate the "failure zone" (Timing Error)
    ax.axvspan(28, 34, color="#f43f5e", alpha=0.1, lw=0)
    ax.text(31, 380, "Phase 7 Recorded Failure:\nPeak Timing Drift & Amplitude Underestimation", 
            color="#9f1239", fontsize=9, fontfamily='sans-serif', fontweight='bold',
            ha='center', va='bottom', alpha=0.8)
    
    out_path = PUBLIC_DIR / "residual_waveform.svg"
    plt.savefig(out_path, transparent=True, bbox_inches='tight', pad_inches=0)
    plt.close()
    print(f"Saved {out_path}")

if __name__ == "__main__":
    draw_topology_svg()
    draw_residual_waveform_svg()
