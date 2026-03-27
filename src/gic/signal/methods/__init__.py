from __future__ import annotations

from gic.signal.methods.fastica_frontend import FastICAFrontend
from gic.signal.methods.lowfreq_frontend import LowFrequencyFrontend
from gic.signal.methods.raw_baseline import RawBaselineFrontend
from gic.signal.methods.sparse_frontend import SparseFrontend


FRONTEND_REGISTRY = {
    "raw_baseline": RawBaselineFrontend,
    "lowfreq_baseline": LowFrequencyFrontend,
    "fastica": FastICAFrontend,
    "sparse_denoise": SparseFrontend,
}


def build_frontend(method_name: str):
    try:
        return FRONTEND_REGISTRY[method_name]()
    except KeyError as exc:
        known = ", ".join(sorted(FRONTEND_REGISTRY))
        raise ValueError(f"Unknown frontend method: {method_name}. Known methods: {known}") from exc
