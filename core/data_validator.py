"""
数据验证模块
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from utils.exceptions import DataValidationError
from utils.logger import get_logger
from data.models import WordCard, MemoryTip

logger = get_logger(__name__)

class DataValidator:
    """数据验证器"""

    def __init__(self):
        self.part_of_speech_patterns = [
            r'^n\.?$|^noun$',
            r'^v\.?$|^verb$',
            r'^adj\.?$|^adjective$',
            r'^adv\.?$|^adverb$',
            r'^prep\.?$|^preposition$',
            r'^conj\.?$|^conjunction$',
            r'^interj\.?$|^interjection$',
            r'^pron\.?$|^pronoun$',
            r'^art\.?$|^article$'
        ]

        self.tip_types = ["谐音法", "拆分法", "词根法"]

    def validate_word_card(self, data: Dict[str, Any], strict: bool = True) -> WordCard:
        """验证单词卡片数据"""
        errors = []

        # 验证必填字段
        required_fields = ['word', 'phonetic', 'part_of_speech', 'meaning', 'memory_tip', 'examples', 'synonyms', 'confusables']
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必填字段: {field}")

        if errors and strict:
            raise DataValidationError(f"数据验证失败: {'; '.join(errors)}")

        # 验证单词
        validated_word = self._validate_word(data.get('word', ''))
        if validated_word is None:
            errors.append("单词格式无效")

        # 验证音标
        validated_phonetic = self._validate_phonetic(data.get('phonetic', ''))
        if validated_phonetic is None:
            errors.append("音标格式无效")

        # 验证词性
        validated_pos = self._validate_part_of_speech(data.get('part_of_speech', ''))
        if validated_pos is None:
            errors.append("词性格式无效")

        # 验证释义
        validated_meaning = self._validate_meaning(data.get('meaning', ''))
        if validated_meaning is None:
            errors.append("释义格式无效")

        # 验证记忆技巧
        validated_memory_tip = self._validate_memory_tip(data.get('memory_tip', {}))
        if validated_memory_tip is None:
            errors.append("记忆技巧格式无效")

        # 验证例句
        validated_examples = self._validate_examples(data.get('examples', []))
        if validated_examples is None:
            errors.append("例句格式无效")

        # 验证同义词
        validated_synonyms = self._validate_synonyms(data.get('synonyms', []))
        if validated_synonyms is None:
            errors.append("同义词格式无效")

        # 验证易混淆词
        validated_confusables = self._validate_confusables(data.get('confusables', []))
        if validated_confusables is None:
            errors.append("易混淆词格式无效")

        if errors and strict:
            raise DataValidationError(f"数据验证失败: {'; '.join(errors)}")

        # 如果有警告但不严格，记录日志
        if errors and not strict:
            logger.warning(f"数据验证发现问题: {'; '.join(errors)}")

        # 创建验证后的单词卡片对象
        try:
            return WordCard(
                word=validated_word or '',
                phonetic=validated_phonetic or '',
                part_of_speech=validated_pos or '',
                meaning=validated_meaning or '',
                memory_tip=validated_memory_tip or MemoryTip(type='', content=''),
                examples=validated_examples or [],
                synonyms=validated_synonyms or [],
                confusables=validated_confusables or []
            )
        except Exception as e:
            if strict:
                raise DataValidationError(f"创建单词卡片失败: {e}")
            else:
                logger.error(f"创建单词卡片失败: {e}")
                return None

    def _validate_word(self, word: str) -> Optional[str]:
        """验证单词格式"""
        if not isinstance(word, str):
            return None

        word = word.strip().lower()

        # 基本验证
        if (not word or
            len(word) < 2 or
            len(word) > 50 or
            not word.isalpha()):

            return None

        return word

    def _validate_phonetic(self, phonetic: str) -> Optional[str]:
        """验证音标格式"""
        if not isinstance(phonetic, str):
            return None

        phonetic = phonetic.strip()

        # 基本验证
        if not phonetic:
            return ""

        # 音标通常包含 / 或 [] 包围的符号
        if not (phonetic.startswith('/') and phonetic.endswith('/') or
                phonetic.startswith('[') and phonetic.endswith(']')):
            # 如果没有包围符号，尝试添加
            if re.search(r'[ˈˌ]', phonetic):  # 包含重音符号
                phonetic = f"/{phonetic}/"

        return phonetic

    def _validate_part_of_speech(self, pos: str) -> Optional[str]:
        """验证词性格式"""
        if not isinstance(pos, str):
            return None

        pos = pos.strip()

        # 检查是否符合常见词性模式
        for pattern in self.part_of_speech_patterns:
            if re.match(pattern, pos, re.IGNORECASE):
                # 标准化词性格式
                if re.match(r'^n\.?$', pos, re.IGNORECASE):
                    return 'n.'
                elif re.match(r'^v\.?$', pos, re.IGNORECASE):
                    return 'v.'
                elif re.match(r'^adj\.?$', pos, re.IGNORECASE):
                    return 'adj.'
                elif re.match(r'^adv\.?$', pos, re.IGNORECASE):
                    return 'adv.'
                elif re.match(r'^prep\.?$', pos, re.IGNORECASE):
                    return 'prep.'
                elif re.match(r'^conj\.?$', pos, re.IGNORECASE):
                    return 'conj.'
                elif re.match(r'^interj\.?$', pos, re.IGNORECASE):
                    return 'interj.'
                elif re.match(r'^pron\.?$', pos, re.IGNORECASE):
                    return 'pron.'
                elif re.match(r'^art\.?$', pos, re.IGNORECASE):
                    return 'art.'

        # 如果不符合常见模式，返回原值但发出警告
        logger.warning(f"不常见的词性格式: {pos}")
        return pos

    def _validate_meaning(self, meaning: str) -> Optional[str]:
        """验证释义格式"""
        if not isinstance(meaning, str):
            return None

        meaning = meaning.strip()

        # 基本验证
        if not meaning or len(meaning) > 500:
            return None

        return meaning

    def _validate_memory_tip(self, tip_data: Dict[str, Any]) -> Optional[MemoryTip]:
        """验证记忆技巧格式"""
        if not isinstance(tip_data, dict):
            return None

        tip_type = tip_data.get('type', '').strip()
        tip_content = tip_data.get('content', '').strip()

        # 验证技巧类型
        if tip_type not in self.tip_types:
            if tip_type:  # 如果有值但不在列表中
                logger.warning(f"未知的记忆技巧类型: {tip_type}")
            return None

        # 验证技巧内容
        if not tip_content or len(tip_content) > 200:
            return None

        return MemoryTip(type=tip_type, content=tip_content)

    def _validate_examples(self, examples: List[str]) -> Optional[List[str]]:
        """验证例句格式"""
        if not isinstance(examples, list):
            return None

        validated_examples = []

        for example in examples:
            if not isinstance(example, str):
                continue

            example = example.strip()

            # 基本验证
            if (not example or
                len(example) < 10 or
                len(example) > 500):

                continue

            # 检查是否包含单词（简单的字母检查）
            if not re.search(r'[a-zA-Z]', example):
                continue

            validated_examples.append(example)

        # 确保至少有一个有效例句
        if len(validated_examples) == 0:
            return None

        # 限制例句数量
        return validated_examples[:5]

    def _validate_synonyms(self, synonyms: List[str]) -> Optional[List[str]]:
        """验证同义词格式"""
        if not isinstance(synonyms, list):
            return None

        validated_synonyms = []

        for synonym in synonyms:
            if not isinstance(synonym, str):
                continue

            synonym = synonym.strip().lower()

            # 基本验证
            if (not synonym or
                len(synonym) < 2 or
                len(synonym) > 30 or
                not synonym.isalpha()):

                continue

            validated_synonyms.append(synonym)

        # 同义词可以为空列表
        return validated_synonyms[:10]

    def _validate_confusables(self, confusables: List[str]) -> Optional[List[str]]:
        """验证易混淆词格式"""
        if not isinstance(confusables, list):
            return None

        validated_confusables = []

        for confusable in confusables:
            if not isinstance(confusable, str):
                continue

            confusable = confusable.strip().lower()

            # 基本验证
            if (not confusable or
                len(confusable) < 2 or
                len(confusable) > 30 or
                not confusable.isalpha()):

                continue

            validated_confusables.append(confusable)

        # 易混淆词可以为空列表
        return validated_confusables[:5]

    def validate_batch_data(self, data_list: List[Dict[str, Any]], strict: bool = True) -> Tuple[List[WordCard], List[Dict[str, Any]]]:
        """批量验证数据"""
        validated_cards = []
        failed_items = []

        for i, data in enumerate(data_list):
            try:
                card = self.validate_word_card(data, strict)
                if card:
                    validated_cards.append(card)
                else:
                    failed_items.append({
                        'index': i,
                        'data': data,
                        'error': '验证失败'
                    })
            except Exception as e:
                failed_items.append({
                    'index': i,
                    'data': data,
                    'error': str(e)
                })

        logger.info(f"批量验证完成: 成功 {len(validated_cards)}, 失败 {len(failed_items)}")
        return validated_cards, failed_items

    def clean_and_fix_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理和修复数据"""
        cleaned_data = data.copy()

        # 清理单词
        if 'word' in cleaned_data:
            cleaned_data['word'] = self._clean_word(cleaned_data['word'])

        # 清理音标
        if 'phonetic' in cleaned_data:
            cleaned_data['phonetic'] = self._clean_phonetic(cleaned_data['phonetic'])

        # 清理词性
        if 'part_of_speech' in cleaned_data:
            cleaned_data['part_of_speech'] = self._clean_part_of_speech(cleaned_data['part_of_speech'])

        # 清理列表数据
        if 'examples' in cleaned_data:
            cleaned_data['examples'] = self._clean_list(cleaned_data['examples'])

        if 'synonyms' in cleaned_data:
            cleaned_data['synonyms'] = self._clean_list(cleaned_data['synonyms'])

        if 'confusables' in cleaned_data:
            cleaned_data['confusables'] = self._clean_list(cleaned_data['confusables'])

        return cleaned_data

    def _clean_word(self, word: str) -> str:
        """清理单词"""
        if isinstance(word, str):
            return word.strip().lower()
        return str(word).strip().lower()

    def _clean_phonetic(self, phonetic: str) -> str:
        """清理音标"""
        if isinstance(phonetic, str):
            phonetic = phonetic.strip()
            # 移除多余空格
            phonetic = re.sub(r'\s+', ' ', phonetic)
            return phonetic
        return str(phonetic).strip()

    def _clean_part_of_speech(self, pos: str) -> str:
        """清理词性"""
        if isinstance(pos, str):
            pos = pos.strip().lower()
            # 简单标准化
            if pos in ['noun', 'n']:
                return 'n.'
            elif pos in ['verb', 'v']:
                return 'v.'
            elif pos in ['adjective', 'adj']:
                return 'adj.'
            elif pos in ['adverb', 'adv']:
                return 'adv.'
            return pos
        return str(pos).strip()

    def _clean_list(self, items: list) -> List[str]:
        """清理列表数据"""
        if not isinstance(items, list):
            return []

        cleaned = []
        for item in items:
            if isinstance(item, str):
                cleaned_item = item.strip()
                if cleaned_item:
                    cleaned.append(cleaned_item)

        return cleaned