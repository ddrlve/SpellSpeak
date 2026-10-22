"""Load VAD / endpoint parameters from the single config file (vad_config.json)."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("vad_config.json")


@dataclass(frozen=True)
class VadParams:
    tier: int
    status: str
    speech_threshold: float
    min_speech_ms: int
    hesitation_ms: int
    timeout_s: float
    pre_roll_ms: int
    max_utterance_s: float


@dataclass(frozen=True)
class VadConfig:
    input_device: int | str | None
    default_tier: int
    tiers: dict[int, VadParams]

    def params_for(self, tier: int | None) -> VadParams:
        return self.tiers[tier if tier in self.tiers else self.default_tier]


def load_config(path: Path = CONFIG_PATH) -> VadConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    tiers: dict[int, VadParams] = {}
    for key, t in raw["tiers"].items():
        p = VadParams(
            tier=int(key),
            status=str(t.get("_status", "UNCALIBRATED")),
            speech_threshold=float(t["speech_threshold"]),
            min_speech_ms=int(t["min_speech_ms"]),
            hesitation_ms=int(t["hesitation_ms"]),
            timeout_s=float(t["timeout_s"]),
            pre_roll_ms=int(t["pre_roll_ms"]),
            max_utterance_s=float(t["max_utterance_s"]),
        )
        if p.status == "UNCALIBRATED":
            print(f"[vad_config] tier {p.tier} is UNCALIBRATED: values are placeholders",
                  file=sys.stderr, flush=True)
        tiers[p.tier] = p
    cfg = VadConfig(raw.get("input_device"), int(raw["default_tier"]), tiers)
    if cfg.default_tier not in tiers:
        raise ValueError("default_tier is not defined in tiers")
    return cfg
