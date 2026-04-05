import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console)

    # Arquivo geral
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(file_handler)

    # Arquivo exclusivo para erros de estoque (auditoria)
    estoque_handler = RotatingFileHandler(
        LOG_DIR / "estoque_erros.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    estoque_handler.setLevel(logging.WARNING)
    estoque_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    estoque_logger = logging.getLogger("estoque")
    estoque_logger.addHandler(estoque_handler)


# Logger de auditoria de estoque (use em qualquer módulo)
estoque_log = logging.getLogger("estoque")
