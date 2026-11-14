from dataclasses import dataclass, field


@dataclass
class AgentResult:
    name: str
    score: float | None  # -1 (very negative) .. +1 (very positive); None = agent couldn't run
    label: str
    points: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return self.score is not None


def unavailable(name: str, reason: str) -> AgentResult:
    return AgentResult(name, None, "Unavailable", warnings=[reason])


def clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def stance(score: float, threshold: float = 0.25) -> str:
    return "Bullish" if score > threshold else "Bearish" if score < -threshold else "Neutral"


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:+.{digits}f}%"
