"""
内置词库模块
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.exceptions import ImportError
from utils.logger import get_logger
from .models import WordSource

logger = get_logger(__name__)

class BuiltinDictionary:
    """内置词库管理器"""

    def __init__(self, dict_path: str = "data/builtin_words.json"):
        self.dict_path = Path(dict_path)
        self.words = []
        self.categories = {}
        self.load_dictionary()

    def load_dictionary(self):
        """加载内置词库"""
        try:
            if not self.dict_path.exists():
                logger.info(f"内置词库文件不存在，将创建新的词库: {self.dict_path}")
                self.create_default_dictionary()
                return

            with open(self.dict_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            self.words = data.get('words', [])
            self.categories = data.get('categories', {})

            logger.info(f"成功加载内置词库，共 {len(self.words)} 个单词")

        except json.JSONDecodeError as e:
            logger.error(f"词库文件格式错误: {e}")
            raise ImportError(f"词库文件格式错误: {e}")
        except Exception as e:
            logger.error(f"加载词库失败: {e}")
            raise ImportError(f"加载词库失败: {e}")

    def create_default_dictionary(self):
        """创建默认词库"""
        default_words = [
            {
                "word": "abandon",
                "difficulty": "medium",
                "category": "情感",
                "frequency": "common"
            },
            {
                "word": "ability",
                "difficulty": "easy",
                "category": "能力",
                "frequency": "common"
            },
            {
                "word": "absent",
                "difficulty": "easy",
                "category": "状态",
                "frequency": "common"
            },
            {
                "word": "absolute",
                "difficulty": "medium",
                "category": "程度",
                "frequency": "common"
            },
            {
                "word": "abstract",
                "difficulty": "hard",
                "category": "概念",
                "frequency": "less_common"
            },
            {
                "word": "academic",
                "difficulty": "medium",
                "category": "教育",
                "frequency": "common"
            },
            {
                "word": "accept",
                "difficulty": "easy",
                "category": "行为",
                "frequency": "common"
            },
            {
                "word": "access",
                "difficulty": "medium",
                "category": "行为",
                "frequency": "common"
            },
            {
                "word": "accident",
                "difficulty": "easy",
                "category": "事件",
                "frequency": "common"
            },
            {
                "word": "accomplish",
                "difficulty": "medium",
                "category": "成就",
                "frequency": "common"
            }
        ]

        default_categories = {
            "情感": ["abandon", "love", "hate", "fear"],
            "能力": ["ability", "skill", "talent"],
            "状态": ["absent", "present", "active"],
            "程度": ["absolute", "relative", "partial"],
            "概念": ["abstract", "concrete", "theory"],
            "教育": ["academic", "education", "learning"],
            "行为": ["accept", "access", "accomplish"],
            "事件": ["accident", "event", "incident"],
            "成就": ["accomplish", "achieve", "success"]
        }

        data = {
            "words": default_words,
            "categories": default_categories
        }

        self.words = default_words
        self.categories = default_categories
        self.save_dictionary()

    def save_dictionary(self):
        """保存词库到文件"""
        try:
            # 确保目录存在
            self.dict_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "words": self.words,
                "categories": self.categories
            }

            with open(self.dict_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)

            logger.info(f"词库已保存到: {self.dict_path}")

        except Exception as e:
            logger.error(f"保存词库失败: {e}")
            raise ImportError(f"保存词库失败: {e}")

    def get_all_words(self) -> List[str]:
        """获取所有单词"""
        return [word_data.get('word', '') for word_data in self.words]

    def get_words_by_category(self, category: str) -> List[str]:
        """按分类获取单词"""
        return self.categories.get(category, [])

    def get_words_by_difficulty(self, difficulty: str) -> List[str]:
        """按难度获取单词"""
        return [
            word_data.get('word', '')
            for word_data in self.words
            if word_data.get('difficulty') == difficulty
        ]

    def get_words_by_frequency(self, frequency: str) -> List[str]:
        """按频率获取单词"""
        return [
            word_data.get('word', '')
            for word_data in self.words
            if word_data.get('frequency') == frequency
        ]

    def get_random_words(self, count: int = 10) -> List[str]:
        """获取随机单词"""
        all_words = self.get_all_words()
        if len(all_words) <= count:
            return all_words
        return random.sample(all_words, count)

    def add_word(self, word: str, difficulty: str = "medium",
                 category: str = "未分类", frequency: str = "common"):
        """添加新单词"""
        word_data = {
            "word": word,
            "difficulty": difficulty,
            "category": category,
            "frequency": frequency
        }

        self.words.append(word_data)

        # 更新分类
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(word)

        self.save_dictionary()
        logger.info(f"已添加单词: {word}")

    def remove_word(self, word: str):
        """删除单词"""
        self.words = [w for w in self.words if w.get('word') != word]

        # 从分类中删除
        for category in self.categories:
            if word in self.categories[category]:
                self.categories[category].remove(word)

        self.save_dictionary()
        logger.info(f"已删除单词: {word}")

    def search_words(self, pattern: str) -> List[str]:
        """搜索单词"""
        pattern = pattern.lower()
        return [
            word_data.get('word', '')
            for word_data in self.words
            if pattern in word_data.get('word', '').lower()
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """获取词库统计信息"""
        total_words = len(self.words)
        difficulty_stats = {}
        category_stats = {}
        frequency_stats = {}

        for word_data in self.words:
            # 统计难度
            difficulty = word_data.get('difficulty', 'unknown')
            difficulty_stats[difficulty] = difficulty_stats.get(difficulty, 0) + 1

            # 统计频率
            frequency = word_data.get('frequency', 'unknown')
            frequency_stats[frequency] = frequency_stats.get(frequency, 0) + 1

        # 统计分类
        for category, words in self.categories.items():
            category_stats[category] = len(words)

        return {
            "total_words": total_words,
            "difficulty_distribution": difficulty_stats,
            "category_distribution": category_stats,
            "frequency_distribution": frequency_stats,
            "categories": list(self.categories.keys())
        }

    def get_word_info(self, word: str) -> Optional[Dict[str, Any]]:
        """获取单词信息"""
        for word_data in self.words:
            if word_data.get('word') == word:
                return word_data
        return None

    def to_word_source(self) -> WordSource:
        """转换为词库来源对象"""
        return WordSource(
            source_type="builtin",
            source_path=str(self.dict_path),
            word_count=len(self.words)
        )