from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import EmailMessage


class MailReader:
    #Читает входящие письма с учетом того, что могут быть некорректные или неподдерживаемые форматы

    TEXT_SUFFIXES = {".txt", ""}
    JSON_SUFFIXES = {".json"}
    IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    SYSTEM_FILES = {".DS_Store", "Thumbs.db"}

    def read(self, path: Path) -> EmailMessage:
        metadata = {"size_bytes": str(path.stat().st_size)}

        if path.name in self.SYSTEM_FILES:
            return EmailMessage(
                path=path,
                filename=path.name,
                raw_text="",
                read_status="system_file",
                metadata=metadata,
            )

        if path.stat().st_size == 0:
            return EmailMessage(
                path=path,
                filename=path.name,
                raw_text="",
                read_status="empty",
                metadata=metadata,
            )

        suffix = path.suffix.lower()
        if suffix in self.IMAGE_SUFFIXES:
            return EmailMessage(
                path=path,
                filename=path.name,
                raw_text="",
                read_status="unsupported_image",
                metadata=metadata,
            )

        if suffix not in self.TEXT_SUFFIXES | self.JSON_SUFFIXES:
            return EmailMessage(
                path=path,
                filename=path.name,
                raw_text="",
                read_status="unsupported_format",
                metadata=metadata,
            )

        try:
            data = path.read_bytes()
        except OSError as exc:
            return EmailMessage(
                path=path,
                filename=path.name,
                raw_text="",
                read_status="read_error",
                metadata={**metadata, "error": str(exc)},
            )

        if self._looks_binary(data):
            return EmailMessage(
                path=path,
                filename=path.name,
                raw_text="",
                read_status="unsupported_format",
                metadata=metadata,
            )

        text, decode_status = self._decode_text(data)
        read_status = decode_status

        if suffix in self.JSON_SUFFIXES:
            text, json_status = self._read_json_text(text)
            read_status = json_status

        subject, sender, body = self._parse_headers(text)
        return EmailMessage(
            path=path,
            filename=path.name,
            raw_text=text,
            subject=subject,
            sender=sender,
            body=body,
            read_status=read_status,
            metadata=metadata,
        )

    @staticmethod
    def _decode_text(data: bytes) -> tuple[str, str]:
        for encoding in ("utf-8", "cp1251"):
            try:
                return data.decode(encoding), "ok" if encoding == "utf-8" else "decoded_cp1251"
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace"), "decoded_with_errors"

    @staticmethod
    def _looks_binary(data: bytes) -> bool:
        if b"\x00" in data[:1024]:
            return True
        if not data:
            return False
        control_bytes = sum(byte < 9 or 14 <= byte < 32 for byte in data[:1024])
        return control_bytes / min(len(data), 1024) > 0.30

    @staticmethod
    def _read_json_text(text: str) -> tuple[str, str]:
        try:
            payload: Any = json.loads(text)
        except json.JSONDecodeError:
            return text, "malformed_json"

        if isinstance(payload, dict):
            flattened = []
            for key, value in payload.items():
                flattened.append(f"{key}: {value}")
            return "\n".join(flattened), "json"
        return str(payload), "json"

    @staticmethod
    def _parse_headers(text: str) -> tuple[str, str, str]:
        subject = ""
        sender = ""
        lines = text.splitlines()
        body_start = 0

        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "":
                body_start = index + 1
                break

            lower = stripped.lower()
            if lower.startswith(("subject:", "тема:", "tema:")):
                subject = stripped.split(":", 1)[1].strip()
            elif lower.startswith(("from:", "от кого:", "ot kogo:")):
                sender = stripped.split(":", 1)[1].strip()
        else:
            body_start = len(lines)

        body = "\n".join(lines[body_start:]).strip()
        return subject, sender, body