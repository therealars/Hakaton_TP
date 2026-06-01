from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ClassificationResult, EmailMessage


@dataclass(frozen=True)
class KeywordRule:
    phrase: str
    weight: int
    prefix: bool = False


class RuleBasedClassifier:
    #Классификатор ищет key ворды и по этому принципу распределяет письма по папкам

    RULES: dict[str, tuple[KeywordRule, ...]] = {
        "spam": (
            KeywordRule("вы выиграли", 8),
            KeywordRule("iphone 15", 8),
            KeywordRule("exclusive offer", 8),
            KeywordRule("limited time", 6),
            KeywordRule("срочная верификация", 8),
            KeywordRule("подтвердите личность", 8),
            KeywordRule("аккаунт будет заблокирован", 8),
            KeywordRule("победителем розыгрыша", 8),
            KeywordRule("для получения приза", 8),
            KeywordRule("приз", 4),
            KeywordRule("банковской карты", 6),
            KeywordRule("банковская карта", 6),
            KeywordRule("totally-not-spam", 8),
            KeywordRule("заблокирован", 4),
            KeywordRule("верификация аккаунта", 6),
        ),
        "monitoring_alerts": (
            KeywordRule("[info]", 5),
            KeywordRule("[warning]", 5),
            KeywordRule("[critical]", 5),
            KeywordRule("healthcheck", 7),
            KeywordRule("disk usage", 7),
            KeywordRule("мониторинг", 6),
            KeywordRule("автоматическое уведомление", 5),
            KeywordRule("alert", 5),
            KeywordRule("cpu usage", 5),
            KeywordRule("gpu usage", 5),
            KeywordRule("prod", 4),
        ),
        "critical_incidents": (
            KeywordRule("критический инцидент", 9),
            KeywordRule("критичный инцидент", 9),
            KeywordRule("массовый сбой", 9),
            KeywordRule("работа остановлена", 8),
            KeywordRule("работа приостановлена", 8),
            KeywordRule("ошибка", 4),
            KeywordRule("не отвечает", 6),
            KeywordRule("недоступен", 6),
            KeywordRule("не работает", 6),
            KeywordRule("падает", 6),
            KeywordRule("urgent", 3),
            KeywordRule("срочно", 3),
        ),
        "access_accounts": (
            KeywordRule("запрос доступа", 8),
            KeywordRule("нет доступа", 8),
            KeywordRule("выдать права", 8),
            KeywordRule("нужны права", 8),
            KeywordRule("необходимы права", 8),
            KeywordRule("нужен доступ", 8),
            KeywordRule("доступы для нового сотрудника", 8),
            KeywordRule("доступ для нового сотрудника", 8),
            KeywordRule("vpn", 5),
            KeywordRule("gitlab", 5),
            KeywordRule("1c", 5),
            KeywordRule("confluence", 5),
            KeywordRule("аккаунт", 3),
        ),
        "hardware": (
            KeywordRule("неисправность оборудования", 9),
            KeywordRule("нужна замена", 7),
            KeywordRule("сломался", 6),
            KeywordRule("принтер", 5),
            KeywordRule("ноутбук", 5),
            KeywordRule("гарнитура", 5),
            KeywordRule("сканер", 5),
            KeywordRule("мышь", 5),
            KeywordRule("монитор", 5),
            KeywordRule("компьютер", 5),
            KeywordRule("пк", 5),
            KeywordRule("устройство", 4),
            KeywordRule("ремонт", 4),
        ),
        "software_issues": (
            KeywordRule("после обновления", 7),
            KeywordRule("не запускается", 6),
            KeywordRule("зависает", 6),
            KeywordRule("после установки", 5),
            KeywordRule("установк", 5, prefix=True),
            KeywordRule("браузер", 5),
            KeywordRule("chrome", 5),
            KeywordRule("zoom", 5),
            KeywordRule("антивирус", 5),
            KeywordRule("excel", 5),
            KeywordRule("adobe reader", 5),
        ),
        "finance_documents": (
            KeywordRule("счет на оплату", 8),
            KeywordRule("закрывающие документы", 8),
            KeywordRule("эдо", 8),
            KeywordRule("электронные документы", 8),
            KeywordRule("акт выполненных работ", 8),
            KeywordRule("статус оплаты", 7),
            KeywordRule("оплата по договору", 7),
            KeywordRule("договору", 3),
            KeywordRule("invoice", 5),
        ),
        "hr_requests": (
            KeywordRule("заявка на отпуск", 9),
            KeywordRule("больничный лист", 9),
            KeywordRule("izmenenie grafika raboty", 9),
            KeywordRule("grafika raboty", 7),
            KeywordRule("netrudosposobnosti", 7),
            KeywordRule("изменение графика", 8),
            KeywordRule("нового сотрудника", 5),
            KeywordRule("выход на работу", 5),
            KeywordRule("отдел", 3),
        ),
        "document_workflow": (
            KeywordRule("на согласование", 8),
            KeywordRule("финальная версия", 8),
            KeywordRule("правки к", 7),
            KeywordRule("техническое задание", 7),
            KeywordRule("тз", 4),
            KeywordRule("инструкция", 5),
            KeywordRule("договор", 5),
            KeywordRule("contract", 4),
            KeywordRule("docx", 3),
            KeywordRule("версия", 3),
        ),
        "client_partner_requests": (
            KeywordRule("внешнего пользователя", 9),
            KeywordRule("вопрос от клиента", 8),
            KeywordRule("жалоба клиента", 8),
            KeywordRule("клиент", 5),
            KeywordRule("партнер", 5),
            KeywordRule("partner", 4),
            KeywordRule("тикет", 5),
            KeywordRule("api", 4),
        ),
        "meetings_newsletters": (
            KeywordRule("корпоративный дайджест", 9),
            KeywordRule("корпоратив", 7),
            KeywordRule("полная версия дайджеста", 8),
            KeywordRule("обновления корпоративного портала", 7),
            KeywordRule("плановые технические работы", 8),
            KeywordRule("приглашение на демо", 8),
            KeywordRule("перенос созвона", 8),
            KeywordRule("нужен созвон", 7),
            KeywordRule("статус задач", 5),
            KeywordRule("demo", 4),
            KeywordRule("созвон", 4),
        ),
    }

    SPECIAL_STATUS_CATEGORIES = {
        "empty": "empty_mail",
        "read_error": "needs_review",
        "system_file": "attachments_or_binary",
        "unsupported_format": "attachments_or_binary",
        "unsupported_image": "attachments_or_binary",
    }

    def classify(self, message: EmailMessage) -> ClassificationResult:
        if message.read_status in self.SPECIAL_STATUS_CATEGORIES:
            category = self.SPECIAL_STATUS_CATEGORIES[message.read_status]
            return ClassificationResult(
                category=category,
                score=0,
                reasons=(message.read_status,),
                status="edge_case",
            )

        text = self._normalize(message.text_for_classification)
        if not text:
            return ClassificationResult(
                category="needs_review",
                score=0,
                reasons=("no_text_for_classification",),
                status="fallback",
            )

        best_category = "needs_review"
        best_score = 0
        best_reasons: tuple[str, ...] = ()

        for category, rules in self.RULES.items():
            score = 0
            reasons: list[str] = []
            for rule in rules:
                if self._matches_rule(text, rule):
                    score += rule.weight
                    reasons.append(rule.phrase)

            if score > best_score:
                best_category = category
                best_score = score
                best_reasons = tuple(reasons)

        if best_score == 0:
            return ClassificationResult(
                category="needs_review",
                score=0,
                reasons=("no_rule_matched",),
                status="fallback",
            )

        return ClassificationResult(
            category=best_category,
            score=best_score,
            reasons=best_reasons,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = text.lower().replace("ё", "е")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    @classmethod
    def _matches_rule(cls, text: str, rule: KeywordRule) -> bool:
        phrase = re.escape(cls._normalize(rule.phrase))
        right_boundary = "" if rule.prefix else r"(?!\w)"
        return re.search(rf"(?<!\w){phrase}{right_boundary}", text) is not None
