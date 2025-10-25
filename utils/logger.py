"""
日志工具模块
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

class Logger:
    """日志管理器"""

    def __init__(self, name: str = "anki_card_generator"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.setup_logger()

    def setup_logger(self, level: str = "INFO", log_file: Optional[str] = None):
        """设置日志配置"""

        # 设置日志级别
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)

        # 清除现有处理器
        self.logger.handlers.clear()

        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器（如果指定了日志文件）
        if log_file:
            # 确保日志目录存在
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            # 使用RotatingFileHandler进行日志轮转
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def info(self, message: str):
        """记录信息级别日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """记录警告级别日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """记录错误级别日志"""
        self.logger.error(message)

    def debug(self, message: str):
        """记录调试级别日志"""
        self.logger.debug(message)

    def exception(self, message: str):
        """记录异常信息"""
        self.logger.exception(message)

# 全局日志实例
logger = Logger()

def get_logger(name: str = "anki_card_generator") -> Logger:
    """获取日志实例"""
    return Logger(name)