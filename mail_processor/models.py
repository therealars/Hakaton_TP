from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class EmailMessage:
    path: Path
    filename: str
    raw_text: str
    subject: str = ""
    sender: str = ""
    body: str = ""
    read_status: str = "ok"
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def text_for_classification(self) -> str:
        parts = [self.subject, self.body, self.raw_text]
        return "\n".join(part for part in parts if part)


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    score: int
    reasons: tuple[str, ...] = ()
    status: str = "classified"


@dataclass(frozen=True)
class ProcessingSummary:
    total_files: int
    categories: dict[str, int]
    statuses: dict[str, int]
    output_dir: Path
    log_file: Path
    stats_file: Path