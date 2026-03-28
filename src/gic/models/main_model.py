from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import torch
from torch import nn

from gic.models.encoders import InputEncoder, TemporalEncoder
from gic.models.fusion import PhysicsFusion
from gic.models.gat_baseline import GATLayer
from gic.models.gcn_baseline import GCNLayer
from gic.models.graphsage_baseline import GraphSAGELayer
from gic.models.heads import HotspotHead, RegressionHead, RiskHead, UncertaintyHead


@dataclass(slots=True)
class MainModelInputBundle:
    sequence_node_features: torch.Tensor
    sequence_global_signal_features: torch.Tensor
    sequence_node_kg_features: torch.Tensor
    sequence_global_kg_features: torch.Tensor
    node_physics_features: torch.Tensor
    global_physics_features: torch.Tensor
    physics_quality_mask: torch.Tensor
    adjacency: torch.Tensor
    regression_targets: torch.Tensor
    hotspot_targets: torch.Tensor | None
    observed_mask: torch.Tensor
    physics_baseline: torch.Tensor
    metadata: list[list[dict[str, Any]]] = field(default_factory=list)

    def to(self, device: torch.device) -> 'MainModelInputBundle':
        return MainModelInputBundle(
            sequence_node_features=self.sequence_node_features.to(device),
            sequence_global_signal_features=self.sequence_global_signal_features.to(device),
            sequence_node_kg_features=self.sequence_node_kg_features.to(device),
            sequence_global_kg_features=self.sequence_global_kg_features.to(device),
            node_physics_features=self.node_physics_features.to(device),
            global_physics_features=self.global_physics_features.to(device),
            physics_quality_mask=self.physics_quality_mask.to(device),
            adjacency=self.adjacency.to(device),
            regression_targets=self.regression_targets.to(device),
            hotspot_targets=self.hotspot_targets.to(device) if self.hotspot_targets is not None else None,
            observed_mask=self.observed_mask.to(device),
            physics_baseline=self.physics_baseline.to(device),
            metadata=self.metadata,
        )


@dataclass(slots=True)
class MainModelOutputBundle:
    regression_prediction: torch.Tensor
    regression_target: torch.Tensor
    hotspot_logits: torch.Tensor | None
    hotspot_target: torch.Tensor | None
    risk_score: torch.Tensor | None
    uncertainty: torch.Tensor | None
    observed_mask: torch.Tensor
    physics_baseline: torch.Tensor
    metadata: list[list[dict[str, Any]]] = field(default_factory=list)


class Phase5MainModel(nn.Module):
    model_name = 'phase5_main_model'

    def __init__(
        self,
        *,
        config: dict[str, Any],
        node_input_dim: int,
        global_signal_dim: int = 0,
        node_physics_dim: int = 0,
        global_physics_dim: int = 0,
        node_kg_dim: int = 0,
        global_kg_dim: int = 0,
    ) -> None:
        super().__init__()
        model_cfg = dict(config.get('model', {}))
        tasks_cfg = dict(config.get('tasks', {}))
        dropout = float(model_cfg.get('dropout', 0.1))
        self.hidden_dim = int(model_cfg.get('hidden_dim', 32))
        self.graph_backbone = str(model_cfg.get('graph_backbone', 'graphsage'))
        self.graph_layers = int(model_cfg.get('graph_layers', 2))
        self.graph_dropout = nn.Dropout(dropout)
        self.use_hotspot = bool(tasks_cfg.get('hotspot', True))
        self.use_risk = bool(tasks_cfg.get('risk_score', False))
        self.use_uncertainty = bool(tasks_cfg.get('uncertainty', False))
        self.use_residual = bool(model_cfg.get('use_residual', True))
        self.use_signal_features = bool(model_cfg.get('use_signal_features', True))
        self.use_physics_features = bool(model_cfg.get('use_physics_features', True))
        self.use_kg_features = bool(model_cfg.get('use_kg_features', False))
        self.input_encoder = InputEncoder(
            node_input_dim=node_input_dim,
            hidden_dim=self.hidden_dim,
            global_signal_dim=global_signal_dim if self.use_signal_features else 0,
            node_kg_dim=node_kg_dim if self.use_kg_features else 0,
            global_kg_dim=global_kg_dim if self.use_kg_features else 0,
            dropout=dropout,
        )
        self.temporal_encoder = TemporalEncoder(
            input_dim=self.hidden_dim,
            hidden_dim=self.hidden_dim,
            mode=str(model_cfg.get('temporal_encoder', 'gru')),
        )
        self.graph_layers_module = nn.ModuleList(self._build_graph_layers())
        self.physics_fusion = PhysicsFusion(
            self.hidden_dim,
            node_physics_dim=node_physics_dim if self.use_physics_features else 0,
            global_physics_dim=global_physics_dim if self.use_physics_features else 0,
            mode=str(model_cfg.get('physics_fusion', 'residual')),
            use_physics_features=self.use_physics_features,
        )
        self.regression_head = RegressionHead(self.hidden_dim)
        self.hotspot_head = HotspotHead(self.hidden_dim) if self.use_hotspot else None
        self.risk_head = RiskHead(self.hidden_dim) if self.use_risk else None
        self.uncertainty_head = UncertaintyHead(self.hidden_dim) if self.use_uncertainty else None

    def _build_graph_layers(self) -> list[nn.Module]:
        layers: list[nn.Module] = []
        for _ in range(max(1, self.graph_layers)):
            if self.graph_backbone == 'gcn':
                layers.append(GCNLayer(self.hidden_dim, self.hidden_dim))
            elif self.graph_backbone == 'graphsage':
                layers.append(GraphSAGELayer(self.hidden_dim, self.hidden_dim))
            elif self.graph_backbone == 'gat':
                layers.append(GATLayer(self.hidden_dim, self.hidden_dim, heads=2))
            else:
                raise ValueError(f'Unsupported graph backbone: {self.graph_backbone}')
        return layers

    def _apply_graph_backbone(self, node_state: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        outputs: list[torch.Tensor] = []
        for graph_index in range(node_state.shape[0]):
            hidden = node_state[graph_index]
            graph_adjacency = adjacency[graph_index]
            for layer in self.graph_layers_module:
                hidden = torch.relu(layer(hidden, graph_adjacency))
                hidden = self.graph_dropout(hidden)
            outputs.append(hidden)
        return torch.stack(outputs, dim=0)

    def forward(self, batch: MainModelInputBundle) -> MainModelOutputBundle:
        encoded = self.input_encoder(
            batch.sequence_node_features,
            batch.sequence_global_signal_features if self.use_signal_features else None,
            batch.sequence_node_kg_features if self.use_kg_features else None,
            batch.sequence_global_kg_features if self.use_kg_features else None,
        )
        temporal_state = self.temporal_encoder(encoded)
        graph_state = self._apply_graph_backbone(temporal_state, batch.adjacency)
        fusion = self.physics_fusion(
            graph_state,
            batch.physics_baseline,
            node_physics_features=batch.node_physics_features if self.use_physics_features else None,
            global_physics_features=batch.global_physics_features if self.use_physics_features else None,
            physics_quality_mask=batch.physics_quality_mask if self.use_physics_features else None,
        )
        regression_prediction = self.regression_head(fusion.fused_features)
        if self.use_residual:
            regression_prediction = regression_prediction + fusion.residual_base
        hotspot_logits = self.hotspot_head(fusion.fused_features) if self.hotspot_head is not None else None
        risk_score = self.risk_head(fusion.fused_features) if self.risk_head is not None else None
        uncertainty = self.uncertainty_head(fusion.fused_features) if self.uncertainty_head is not None else None
        return MainModelOutputBundle(
            regression_prediction=regression_prediction,
            regression_target=batch.regression_targets,
            hotspot_logits=hotspot_logits,
            hotspot_target=batch.hotspot_targets,
            risk_score=risk_score,
            uncertainty=uncertainty,
            observed_mask=batch.observed_mask,
            physics_baseline=batch.physics_baseline,
            metadata=batch.metadata,
        )

    def predict_batch(self, batch: MainModelInputBundle) -> MainModelOutputBundle:
        return self.forward(batch)


def build_main_model(
    config: dict[str, Any],
    input_dim: int | None = None,
    *,
    node_input_dim: int | None = None,
    global_signal_dim: int = 0,
    node_physics_dim: int = 0,
    global_physics_dim: int = 0,
    node_kg_dim: int = 0,
    global_kg_dim: int = 0,
) -> Phase5MainModel:
    resolved_node_input_dim = node_input_dim if node_input_dim is not None else input_dim
    if resolved_node_input_dim is None:
        raise ValueError('build_main_model requires input_dim or node_input_dim')
    return Phase5MainModel(
        config=config,
        node_input_dim=int(resolved_node_input_dim),
        global_signal_dim=global_signal_dim,
        node_physics_dim=node_physics_dim,
        global_physics_dim=global_physics_dim,
        node_kg_dim=node_kg_dim,
        global_kg_dim=global_kg_dim,
    )
