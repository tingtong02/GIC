import os
from pathlib import Path

SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 400" width="100%" height="100%">
    <defs>
        <!-- Gradients and Filters -->
        <filter id="glow-green" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter id="glow-blue" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter id="glow-yellow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        
        <!-- Arrowhead markers -->
        <marker id="arrow-green" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
        </marker>
        <marker id="arrow-blue" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#0ea5e9" />
        </marker>
        <marker id="arrow-white" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
        </marker>
    </defs>

    <!-- Background (Transparent but darkish for blending) -->
    <rect width="1000" height="400" fill="transparent" />

    <!-- LINES (2-hop to 1-hop) -->
    <path d="M 120 100 Q 180 150 250 200" stroke="#0ea5e9" stroke-width="2" stroke-dasharray="4,4" fill="none" marker-end="url(#arrow-blue)" opacity="0.6"/>
    <path d="M 100 200 L 250 200" stroke="#0ea5e9" stroke-width="2" stroke-dasharray="4,4" fill="none" marker-end="url(#arrow-blue)" opacity="0.6"/>
    <path d="M 120 300 Q 180 250 250 200" stroke="#0ea5e9" stroke-width="2" stroke-dasharray="4,4" fill="none" marker-end="url(#arrow-blue)" opacity="0.6"/>

    <path d="M 120 70 Q 180 80 250 100" stroke="#0ea5e9" stroke-width="2" stroke-dasharray="4,4" fill="none" marker-end="url(#arrow-blue)" opacity="0.6"/>
    <path d="M 140 130 Q 190 120 250 100" stroke="#0ea5e9" stroke-width="2" stroke-dasharray="4,4" fill="none" marker-end="url(#arrow-blue)" opacity="0.6"/>

    <path d="M 120 330 Q 180 320 250 300" stroke="#0ea5e9" stroke-width="2" stroke-dasharray="4,4" fill="none" marker-end="url(#arrow-blue)" opacity="0.6"/>
    <path d="M 140 270 Q 190 280 250 300" stroke="#0ea5e9" stroke-width="2" stroke-dasharray="4,4" fill="none" marker-end="url(#arrow-blue)" opacity="0.6"/>

    <!-- LINES (1-hop to Target) -->
    <path d="M 250 100 Q 320 150 400 200" stroke="#10b981" stroke-width="3" fill="none" marker-end="url(#arrow-green)"/>
    <path d="M 250 200 L 400 200" stroke="#10b981" stroke-width="3" fill="none" marker-end="url(#arrow-green)"/>
    <path d="M 250 300 Q 320 250 400 200" stroke="#10b981" stroke-width="3" fill="none" marker-end="url(#arrow-green)"/>

    <!-- LINES (Target to Aggregator) -->
    <path d="M 400 200 L 550 200" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4,2" fill="none" marker-end="url(#arrow-white)"/>
    
    <!-- LINES (Aggregator to Update) -->
    <path d="M 700 200 L 850 200" stroke="#94a3b8" stroke-width="2" fill="none" marker-end="url(#arrow-white)"/>

    <!-- NODES: 2-hop (Blue) -->
    <circle cx="120" cy="100" r="12" fill="#0f172a" stroke="#0ea5e9" stroke-width="2" filter="url(#glow-blue)" />
    <circle cx="100" cy="200" r="12" fill="#0f172a" stroke="#0ea5e9" stroke-width="2" filter="url(#glow-blue)" />
    <circle cx="120" cy="300" r="12" fill="#0f172a" stroke="#0ea5e9" stroke-width="2" filter="url(#glow-blue)" />
    
    <circle cx="120" cy="70" r="10" fill="#0f172a" stroke="#0ea5e9" stroke-width="1.5" />
    <circle cx="140" cy="130" r="10" fill="#0f172a" stroke="#0ea5e9" stroke-width="1.5" />
    <circle cx="120" cy="330" r="10" fill="#0f172a" stroke="#0ea5e9" stroke-width="1.5" />
    <circle cx="140" cy="270" r="10" fill="#0f172a" stroke="#0ea5e9" stroke-width="1.5" />

    <!-- NODES: 1-hop (Green) -->
    <text x="250" y="65" fill="#10b981" font-family="JetBrains Mono, monospace" font-size="12" text-anchor="middle" font-weight="bold">N(v)_1</text>
    <circle cx="250" cy="100" r="20" fill="#0f172a" stroke="#10b981" stroke-width="3" filter="url(#glow-green)" />
    
    <text x="250" y="165" fill="#10b981" font-family="JetBrains Mono, monospace" font-size="12" text-anchor="middle" font-weight="bold">N(v)_2</text>
    <circle cx="250" cy="200" r="20" fill="#0f172a" stroke="#10b981" stroke-width="3" filter="url(#glow-green)" />
    
    <text x="250" y="345" fill="#10b981" font-family="JetBrains Mono, monospace" font-size="12" text-anchor="middle" font-weight="bold">N(v)_3</text>
    <circle cx="250" cy="300" r="20" fill="#0f172a" stroke="#10b981" stroke-width="3" filter="url(#glow-green)" />

    <!-- NODE: Target (Yellow) Before Update -->
    <circle cx="400" cy="200" r="28" fill="#1e293b" stroke="#facc15" stroke-width="4" filter="url(#glow-yellow)" />
    <text x="400" y="205" fill="#facc15" font-family="Arial, sans-serif" font-size="18" text-anchor="middle" font-weight="bold">v</text>
    <text x="400" y="250" fill="#facc15" font-family="JetBrains Mono, monospace" font-size="14" text-anchor="middle">h_v^{(k-1)}</text>

    <!-- AGGREGATOR MATH BLOCK -->
    <rect x="550" y="150" width="150" height="100" rx="10" ry="10" fill="#1e293b" stroke="#6366f1" stroke-width="2" />
    <text x="625" y="180" fill="#818cf8" font-family="JetBrains Mono, monospace" font-size="14" text-anchor="middle" font-weight="bold">AGGREGATE</text>
    <text x="625" y="205" fill="#cbd5e1" font-family="JetBrains Mono, monospace" font-size="12" text-anchor="middle">Mean() / Max()</text>
    <text x="625" y="230" fill="#fff" font-family="JetBrains Mono, monospace" font-size="14" text-anchor="middle" font-weight="bold">σ( W • CONCAT )</text>

    <!-- NODE: Target (Yellow) After Update -->
    <circle cx="850" cy="200" r="35" fill="#0ea5e9" stroke="#38bdf8" stroke-width="4" filter="url(#glow-blue)" />
    <text x="850" y="205" fill="#fff" font-family="Arial, sans-serif" font-size="18" text-anchor="middle" font-weight="bold">v'</text>
    <text x="850" y="260" fill="#38bdf8" font-family="JetBrains Mono, monospace" font-size="16" text-anchor="middle" font-weight="bold">h_v^{(k)}</text>

    <!-- ANNOTATIONS -->
    <text x="120" y="30" fill="#0ea5e9" font-family="Arial, sans-serif" font-size="14" text-anchor="middle" font-weight="bold" opacity="0.8">2-hop Neighbors</text>
    <text x="250" y="30" fill="#10b981" font-family="Arial, sans-serif" font-size="14" text-anchor="middle" font-weight="bold">1-hop Neighbors N</text>
    <text x="400" y="30" fill="#facc15" font-family="Arial, sans-serif" font-size="14" text-anchor="middle" font-weight="bold">Target Node (v)</text>
    <text x="625" y="30" fill="#818cf8" font-family="Arial, sans-serif" font-size="14" text-anchor="middle" font-weight="bold">GraphSAGE Core</text>
    <text x="850" y="30" fill="#38bdf8" font-family="Arial, sans-serif" font-size="14" text-anchor="middle" font-weight="bold">Updated State</text>

    <!-- Information text -->
    <text x="500" y="380" fill="#94a3b8" font-family="JetBrains Mono, monospace" font-size="12" text-anchor="middle" opacity="0.7">Message passing logic: Recursively aggregates feature matrices starting from outer K-hops inwards to update Target Node</text>

</svg>
"""

if __name__ == "__main__":
    out_path = Path("web/public/graphsage_conceptual_core.svg")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(SVG_CONTENT)
    print(f"Conceptual GraphSAGE SVG generated to {out_path}!")
