from __future__ import annotations

from typing import Any

import torch
from torch import nn

from gic.models.base import BaselineModel


class GATLayer(nn.Module):
    def __init__(self, input_dim: int, output_dim: int, heads: int = 1) -> None:
        super().__init__()
        self.output_dim = int(output_dim)
        self.heads = int(heads)
        self.linear = nn.Linear(input_dim, self.output_dim * self.heads, bias=False)
        self.attn_src = nn.Parameter(torch.empty(self.heads, self.output_dim))
        self.attn_dst = nn.Parameter(torch.empty(self.heads, self.output_dim))
        self.leaky_relu = nn.LeakyReLU(0.2)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        nn.init.xavier_uniform_(self.linear.weight)
        nn.init.xavier_uniform_(self.attn_src)
        nn.init.xavier_uniform_(self.attn_dst)

    def forward(self, features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        node_count = features.shape[0]
        transformed = self.linear(features).view(node_count, self.heads, self.output_dim)
        src_scores = (transformed * self.attn_src.unsqueeze(0)).sum(dim=-1)
        dst_scores = (transformed * self.attn_dst.unsqueeze(0)).sum(dim=-1)
        logits = self.leaky_relu(src_scores.unsqueeze(1) + dst_scores.unsqueeze(0))
        attention_mask = adjacency > 0
        logits = logits.masked_fill(~attention_mask.unsqueeze(-1), float('-inf'))
        attention = torch.softmax(logits, dim=1)
        attention = torch.nan_to_num(attention, nan=0.0, posinf=0.0, neginf=0.0)
        aggregated = torch.einsum('ijh,jhf->ihf', attention, transformed)
        return aggregated.mean(dim=1)


class GATBaseline(BaselineModel):
    model_name = 'gat'

    def __init__(self, input_dim: int, hidden_dim: int, layers: int = 2, heads: int = 2, dropout: float = 0.0) -> None:
        super().__init__()
        if input_dim <= 0:
            raise ValueError('GATBaseline input_dim must be positive')
        if layers < 1:
            raise ValueError('GATBaseline requires at least one layer')
        self.dropout = nn.Dropout(float(dropout)) if dropout > 0 else nn.Identity()
        hidden_layers: list[nn.Module] = []
        previous_dim = input_dim
        for _ in range(max(1, layers - 1)):
            hidden_layers.append(GATLayer(previous_dim, hidden_dim, heads=heads))
            previous_dim = hidden_dim
        self.hidden_layers = nn.ModuleList(hidden_layers)
        self.output_layer = nn.Linear(previous_dim, 1)

    def forward(
        self,
        features: torch.Tensor,
        *,
        adjacency: torch.Tensor | None = None,
        graph_index: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if adjacency is None:
            raise ValueError('GATBaseline requires adjacency information')
        hidden = features
        for layer in self.hidden_layers:
            hidden = torch.relu(layer(hidden, adjacency))
            hidden = self.dropout(hidden)
        return self.output_layer(hidden).squeeze(-1)



def build_gat_baseline(model_config: dict[str, Any], input_dim: int) -> GATBaseline:
    return GATBaseline(
        input_dim=input_dim,
        hidden_dim=int(model_config.get('hidden_dim', 32)),
        layers=int(model_config.get('layers', 2)),
        heads=int(model_config.get('heads', 2)),
        dropout=float(model_config.get('dropout', 0.0)),
    )
