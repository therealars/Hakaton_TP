from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from mail_processor.processor import MailProcessor


class MailProcessorTest(unittest.TestCase):
    def test_process_copies_files_and_writes_reports(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            inbox = root / "inbox"
            output = root / "processed"
            logs = root / "logs"
            inbox.mkdir()
            (inbox / "spam.txt").write_text("Вы выиграли iPhone 15!", encoding="utf-8")
            (inbox / "critical.txt").write_text(
                "Subject: Критический инцидент\n\nGitLab недоступен",
                encoding="utf-8",
            )
            (inbox / "empty.txt").write_text("", encoding="utf-8")
            (inbox / "data.bin").write_bytes(b"\x00\x01")

            summary = MailProcessor().process(inbox, output, logs, mode="copy")

            stats = json.loads((logs / "stats.json").read_text(encoding="utf-8"))

            self.assertEqual(summary.total_files, 4)
            self.assertEqual(stats["total_files"], 4)
            self.assertTrue((output / "spam" / "spam.txt").exists())
            self.assertTrue((output / "critical_incidents" / "critical.txt").exists())
            self.assertTrue((output / "empty_mail" / "empty.txt").exists())
            self.assertTrue((output / "attachments_or_binary" / "data.bin").exists())
            self.assertTrue((logs / "processing_log.csv").exists())


if __name__ == "__main__":
    unittest.main()
