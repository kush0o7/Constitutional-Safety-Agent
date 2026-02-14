import logging
import re


class RedactingFilter(logging.Filter):
    SECRET_PATTERNS = [
        re.compile(r"sk-[A-Za-z0-9]{10,}"),
        re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+/]+=*", re.IGNORECASE),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        message = str(record.getMessage())
        for pattern in self.SECRET_PATTERNS:
            message = pattern.sub("[REDACTED]", message)
        record.msg = message
        record.args = ()
        return True


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RedactingFilter())
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), handlers=[handler])
