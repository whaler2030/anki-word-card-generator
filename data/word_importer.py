"""
词库导入模块
"""

import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from utils.exceptions import ImportError
from utils.logger import get_logger
from .models import WordSource

logger = get_logger(__name__)

class WordImporter:
    """词库导入器"""

    def __init__(self):
        self.supported_formats = ['txt', 'csv', 'json']

    def import_words(self, file_path: str, format_type: str = None) -> WordSource:
        """导入词库文件"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise ImportError(f"文件不存在: {file_path}")

        # 自动检测文件格式
        if format_type is None:
            format_type = file_path.suffix.lower().lstrip('.')

        if format_type not in self.supported_formats:
            raise ImportError(f"不支持的文件格式: {format_type}")

        logger.info(f"开始导入词库文件: {file_path} (格式: {format_type})")

        try:
            if format_type == 'txt':
                words = self._import_txt(file_path)
            elif format_type == 'csv':
                words = self._import_csv(file_path)
            elif format_type == 'json':
                words = self._import_json(file_path)
            else:
                raise ImportError(f"不支持的格式: {format_type}")

            # 清理和验证单词
            words = self._clean_words(words)

            word_source = WordSource(
                source_type="user",
                source_path=str(file_path),
                word_count=len(words)
            )

            logger.info(f"成功导入 {len(words)} 个单词")
            return word_source

        except Exception as e:
            logger.error(f"导入词库失败: {e}")
            raise ImportError(f"导入词库失败: {e}")

    def _import_txt(self, file_path: Path) -> List[str]:
        """导入TXT格式文件"""
        words = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if line and not line.startswith('#'):  # 跳过空行和注释
                    # 按行分割单词
                    line_words = re.findall(r'\b[a-zA-Z]+\b', line)
                    words.extend(line_words)
        return words

    def _import_csv(self, file_path: Path) -> List[str]:
        """导入CSV格式文件"""
        words = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            # 尝试检测列名
            if 'word' in reader.fieldnames:
                word_column = 'word'
            elif 'words' in reader.fieldnames:
                word_column = 'words'
            elif '词汇' in reader.fieldnames:
                word_column = '词汇'
            elif '单词' in reader.fieldnames:
                word_column = '单词'
            else:
                # 如果没有找到明确的列名，使用第一列
                word_column = reader.fieldnames[0] if reader.fieldnames else None

            if word_column is None:
                raise ImportError("CSV文件未找到有效的单词列")

            for row in reader:
                word = row.get(word_column, '').strip()
                if word:
                    # 处理可能包含多个单词的单元格
                    cell_words = re.findall(r'\b[a-zA-Z]+\b', word)
                    words.extend(cell_words)

        return words

    def _import_json(self, file_path: Path) -> List[str]:
        """导入JSON格式文件"""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        words = []

        # 处理不同的JSON结构
        if isinstance(data, list):
            # 数组格式
            for item in data:
                if isinstance(item, str):
                    words.append(item)
                elif isinstance(item, dict):
                    # 字典格式，尝试提取单词
                    word = item.get('word') or item.get('词汇') or item.get('单词')
                    if word:
                        words.append(word)
        elif isinstance(data, dict):
            # 对象格式
            if 'words' in data:
                words.extend(data['words'])
            elif '词汇' in data:
                words.extend(data['词汇'])
            elif '单词' in data:
                words.extend(data['单词'])
            else:
                # 如果键都是单词，收集所有键
                for key in data.keys():
                    if re.match(r'^[a-zA-Z]+$', key):
                        words.append(key)

        return words

    def _clean_words(self, words: List[str]) -> List[str]:
        """清理和验证单词"""
        cleaned_words = []
        seen = set()

        for word in words:
            # 清理单词
            word = word.strip().lower()

            # 移除非字母字符
            word = re.sub(r'[^a-zA-Z]', '', word)

            # 验证单词格式
            if (word and
                len(word) > 1 and  # 至少2个字符
                word.isalpha() and  # 只包含字母
                word not in seen):   # 去重

                cleaned_words.append(word)
                seen.add(word)

        return cleaned_words

    def preview_file(self, file_path: str, format_type: str = None, max_lines: int = 10) -> Dict[str, Any]:
        """预览文件内容"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise ImportError(f"文件不存在: {file_path}")

        if format_type is None:
            format_type = file_path.suffix.lower().lstrip('.')

        try:
            if format_type == 'txt':
                return self._preview_txt(file_path, max_lines)
            elif format_type == 'csv':
                return self._preview_csv(file_path, max_lines)
            elif format_type == 'json':
                return self._preview_json(file_path)
            else:
                raise ImportError(f"不支持的格式: {format_type}")

        except Exception as e:
            raise ImportError(f"预览文件失败: {e}")

    def _preview_txt(self, file_path: Path, max_lines: int) -> Dict[str, Any]:
        """预览TXT文件"""
        lines = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for i, line in enumerate(file):
                if i >= max_lines:
                    break
                lines.append(line.strip())

        return {
            'format': 'txt',
            'total_lines': len(lines),
            'preview_lines': lines,
            'estimated_words': len(self._clean_words(self._import_txt(file_path)))
        }

    def _preview_csv(self, file_path: Path, max_lines: int) -> Dict[str, Any]:
        """预览CSV文件"""
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames or []
            rows = []
            for i, row in enumerate(reader):
                if i >= max_lines:
                    break
                rows.append(row)

        return {
            'format': 'csv',
            'columns': fieldnames,
            'total_rows': len(rows),
            'preview_rows': rows
        }

    def _preview_json(self, file_path: Path) -> Dict[str, Any]:
        """预览JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        return {
            'format': 'json',
            'data_type': type(data).__name__,
            'data_preview': str(data)[:500] + '...' if len(str(data)) > 500 else str(data)
        }

    def get_format_info(self) -> Dict[str, Dict[str, str]]:
        """获取支持的格式信息"""
        return {
            'txt': {
                'description': '纯文本格式，每行一个单词或多个单词',
                'example': 'apple\nbanana\norange'
            },
            'csv': {
                'description': 'CSV格式，支持word/words/词汇/单词列',
                'example': 'word\napple\nbanana\norange'
            },
            'json': {
                'description': 'JSON格式，支持数组或对象格式',
                'example': '["apple", "banana", "orange"]'
            }
        }

    def validate_format(self, file_path: str) -> bool:
        """验证文件格式是否支持"""
        file_path = Path(file_path)
        format_type = file_path.suffix.lower().lstrip('.')
        return format_type in self.supported_formats