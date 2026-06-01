from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from mail_processor.reader import MailReader


class MailReaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reader = MailReader()

    def test_reads_text_headers(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "mail.txt"
            path.write_text(
                "From: test@example.com\nSubject: Ошибка 500\n\nТело письма",
                encoding="utf-8",
            )

            message = self.reader.read(path)

        self.assertEqual(message.read_status, "ok")
        self.assertEqual(message.sender, "test@example.com")
        self.assertEqual(message.subject, "Ошибка 500")
        self.assertEqual(message.body, "Тело письма")

    def test_reads_text_file_without_extension(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "mail_0106"
            path.write_text("Subject: [INFO] API Gateway\n\nhealthcheck ok", encoding="utf-8")

            message = self.reader.read(path)

        self.assertEqual(message.read_status, "ok")
        self.assertEqual(message.subject, "[INFO] API Gateway")

    def test_malformed_json_does_not_crash(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "mail.json"
            path.write_text('{"subject": "Ваш аккаунт будет заблокирован"', encoding="utf-8")

            message = self.reader.read(path)

        self.assertEqual(message.read_status, "malformed_json")
        self.assertIn("аккаунт", message.raw_text)

    def test_binary_file_is_marked_as_unsupported(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "mail.bin"
            path.write_bytes(b"\x00\x01\x02\x03")

            message = self.reader.read(path)

        self.assertEqual(message.read_status, "unsupported_format")
        self.assertEqual(message.raw_text, "")

    def test_empty_file_is_marked_as_empty(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.txt"
            path.write_text("", encoding="utf-8")

            message = self.reader.read(path)

        self.assertEqual(message.read_status, "empty")

if __name__ == "__main__":
    unittest.main()
