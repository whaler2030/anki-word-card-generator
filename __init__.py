"""
Anki单词卡片生成器
Anki Word Card Generator

基于大模型API的智能英语学习卡片生成工具
"""

__version__ = "1.0.0"
__author__ = "Anki Card Generator Team"
__description__ = "基于大模型的Anki单词卡片批量生成工具"

# 导入主要组件
from .config.config_parser import ConfigParser
from .data.builtin_dict import BuiltinDictionary
from .data.word_importer import WordImporter
from .core.word_generator import WordCardGenerator
from .core.data_validator import DataValidator
from .export.csv_exporter import CSVExporter
from .export.anki_exporter import AnkiExporter
from .data.models import WordCard, GenerationRequest, GenerationResult

__all__ = [
    'ConfigParser',
    'BuiltinDictionary',
    'WordImporter',
    'WordCardGenerator',
    'DataValidator',
    'CSVExporter',
    'AnkiExporter',
    'WordCard',
    'GenerationRequest',
    'GenerationResult'
]