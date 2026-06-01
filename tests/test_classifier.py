from pathlib import Path
import unittest

from mail_processor.classifier import RuleBasedClassifier
from mail_processor.models import EmailMessage


def make_message(text: str, status: str = "ok") -> EmailMessage:
    return EmailMessage(
        path=Path("mail.txt"),
        filename="mail.txt",
        raw_text=text,
        subject=text.splitlines()[0] if text else "",
        body=text,
        read_status=status,
    )


class RuleBasedClassifierTest(unittest.TestCase):
    def setUp(self) -> None:
        self.classifier = RuleBasedClassifier()

    def test_classifies_representative_categories(self) -> None:
        cases = [
            ("Вы выиграли iPhone 15! Срочно подтвердите личность", "spam"),
            ("[WARNING] Disk usage > 80% на prod. healthcheck failed", "monitoring_alerts"),
            ("Критический инцидент: GitLab недоступен, работа остановлена", "critical_incidents"),
            ("Нужны права в VPN для нового сотрудника", "access_accounts"),
            ("Неисправность оборудования: ноутбук не определяется системой", "hardware"),
            ("После обновления не запускается антивирус", "software_issues"),
            ("Закрывающие документы за март, счет на оплату", "finance_documents"),
            ("Больничный лист, period netrudosposobnosti 10 dney", "hr_requests"),
            ("Финальная версия: договор на согласование", "document_workflow"),
            ("Жалоба клиента: нет ответа на тикет", "client_partner_requests"),
            ("Корпоративный дайджест и перенос созвона", "meetings_newsletters"),
        ]

        for text, expected in cases:
            with self.subTest(expected=expected):
                result = self.classifier.classify(make_message(text))
                self.assertEqual(result.category, expected)
                self.assertGreater(result.score, 0)

    def test_edge_cases_use_safe_categories(self) -> None:
        cases = [
            ("", "empty", "empty_mail"),
            ("", "unsupported_format", "attachments_or_binary"),
            ("обычное письмо без понятных признаков", "ok", "needs_review"),
        ]

        for text, status, expected in cases:
            with self.subTest(status=status):
                result = self.classifier.classify(make_message(text, status))
                self.assertEqual(result.category, expected)


if __name__ == "__main__":
    unittest.main()
