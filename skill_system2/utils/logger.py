"""
Logger utilities.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


# 配置日志：控制台输出 + 可选文件输出
def setup_logger(
    name: str = "skill_system2",
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure a logger with console output and optional file output.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper()))

    if format_string is None:
        format_string = (
            "[%(asctime)s] [%(name)s] [%(levelname)s] "
            "%(filename)s:%(lineno)d - %(message)s"
        )

    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 获取指定名称的日志实例
def get_logger(name: str = "skill_system2") -> logging.Logger:
    """
    Get a configured logger by name.
    """
    return logging.getLogger(name)
