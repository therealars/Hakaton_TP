from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .classifier import RuleBasedClassifier
from .models import ProcessingSummary
from .reader import MailReader


class MailProcessor:
    def __init__(
        self,
        reader: MailReader | None = None,
        classifier: RuleBasedClassifier | None = None,
    ) -> None:
        self.reader = reader or MailReader()
        self.classifier = classifier or RuleBasedClassifier()

    def process(
        self,
        input_dir: Path,
        output_dir: Path,
        log_dir: Path,
        mode: str = "copy",
    ) -> ProcessingSummary:
        if mode not in {"copy", "move"}:
            raise ValueError("mode must be either 'copy' or 'move'")
        if not input_dir.exists() or not input_dir.is_dir():
            raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

        files = sorted(path for path in input_dir.iterdir() if path.is_file())
        categories: Counter[str] = Counter()
        statuses: Counter[str] = Counter()
        rows: list[dict[str, str]] = []

        output_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)

        for path in files:
            message = self.reader.read(path)
            result = self.classifier.classify(message)
            categories[result.category] += 1
            statuses[message.read_status] += 1

            destination = output_dir / result.category / path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination = self._unique_destination(destination)
            if mode == "copy":
                shutil.copy2(path, destination)
            else:
                shutil.move(str(path), destination)

            rows.append(
                {
                    "filename": path.name,
                    "category": result.category,
                    "classification_status": result.status,
                    "read_status": message.read_status,
                    "score": str(result.score),
                    "reason": "; ".join(result.reasons),
                    "subject": message.subject,
                    "sender": message.sender,
                    "destination": str(destination),
                }
            )

        log_file = log_dir / "processing_log.csv"
        stats_file = log_dir / "stats.json"
        self._write_csv(log_file, rows)
        self._write_stats(stats_file, files, categories, statuses, output_dir)

        return ProcessingSummary(
            total_files=len(files),
            categories=dict(sorted(categories.items())),
            statuses=dict(sorted(statuses.items())),
            output_dir=output_dir,
            log_file=log_file,
            stats_file=stats_file,
        )

    @staticmethod
    def _unique_destination(destination: Path) -> Path:
        if not destination.exists():
            return destination

        stem = destination.stem
        suffix = destination.suffix
        parent = destination.parent
        counter = 1
        while True:
            candidate = parent / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    @staticmethod
    def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
        fieldnames = [
            "filename",
            "category",
            "classification_status",
            "read_status",
            "score",
            "reason",
            "subject",
            "sender",
            "destination",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _write_stats(
        path: Path,
        files: list[Path],
        categories: Counter[str],
        statuses: Counter[str],
        output_dir: Path,
    ) -> None:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_files": len(files),
            "output_dir": str(output_dir),
            "categories": dict(sorted(categories.items())),
            "read_statuses": dict(sorted(statuses.items())),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")