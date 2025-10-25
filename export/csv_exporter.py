"""
CSV格式导出器
"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from utils.exceptions import ExportError
from utils.logger import get_logger
from data.models import WordCard, ExportSettings

logger = get_logger(__name__)

class CSVExporter:
    """CSV格式导出器"""

    def __init__(self, export_settings: ExportSettings):
        self.settings = export_settings
        self.delimiter = export_settings.csv_delimiter or ','

    def export_cards(self, cards: List[WordCard], output_path: str = None) -> str:
        """导出单词卡片到CSV文件"""
        if not cards:
            raise ExportError("没有可导出的单词卡片")

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/anki_cards_{timestamp}.csv"

        # 确保输出目录存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"开始导出CSV文件: {output_path}")

        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                # 写入Anki格式的CSV头部
                writer = csv.writer(csvfile, delimiter=self.delimiter)

                # 写入头部注释（说明字段含义）
                writer.writerow([f"# Anki单词卡片 - 生成时间: {datetime.now()}"])
                writer.writerow([f"# 牌组名称: {self.settings.deck_name}"])
                writer.writerow([f"# 牌组描述: {self.settings.deck_description}"])
                writer.writerow([])

                # 写入列标题（Anki字段名）
                writer.writerow([
                    "Front",           # 前面（单词）
                    "Back",            # 背面（详细信息）
                    "Phonetic",        # 音标
                    "Part of Speech",  # 词性
                    "Meaning",         # 释义
                    "Memory Tip Type", # 记忆技巧类型
                    "Memory Tip Content", # 记忆技巧内容
                    "Examples",        # 例句
                    "Synonyms",        # 同义词
                    "Confusables",     # 易混淆词
                    "Tags"             # 标签
                ])

                # 写入数据行
                for card in cards:
                    # 格式化卡片的正面和背面
                    front_text = self._format_front(card)
                    back_text = self._format_back(card)

                    row = [
                        front_text,
                        back_text,
                        card.phonetic,
                        card.part_of_speech,
                        card.meaning,
                        card.memory_tip.type or "",
                        card.memory_tip.content,
                        self._format_examples(card.examples),
                        self._format_synonyms(card.synonyms),
                        self._format_confusables(card.confusables),
                        self._format_tags(card)
                    ]

                    writer.writerow(row)

            logger.info(f"CSV导出完成: {len(cards)} 个卡片已保存到 {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"CSV导出失败: {e}")
            raise ExportError(f"CSV导出失败: {e}")

    def export_simple_format(self, cards: List[WordCard], output_path: str = None) -> str:
        """导出简化格式的CSV文件"""
        if not cards:
            raise ExportError("没有可导出的单词卡片")

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/word_cards_simple_{timestamp}.csv"

        # 确保输出目录存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"开始导出简化CSV文件: {output_path}")

        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter)

                # 写入头部
                writer.writerow([
                    "单词", "音标", "词性", "释义", "记忆技巧", "例句", "同义词", "易混淆词"
                ])

                # 写入数据
                for card in cards:
                    row = [
                        card.word,
                        card.phonetic,
                        card.part_of_speech,
                        card.meaning,
                        f"{card.memory_tip.type + ': ' if card.memory_tip.type else ''}{card.memory_tip.content}",
                        self._format_examples(card.examples),
                        self._format_synonyms(card.synonyms),
                        self._format_confusables(card.confusables)
                    ]

                    writer.writerow(row)

            logger.info(f"简化CSV导出完成: {len(cards)} 个卡片已保存到 {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"简化CSV导出失败: {e}")
            raise ExportError(f"简化CSV导出失败: {e}")

    def export_study_guide(self, cards: List[WordCard], output_path: str = None) -> str:
        """导出学习指南CSV文件"""
        if not cards:
            raise ExportError("没有可导出的单词卡片")

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/study_guide_{timestamp}.csv"

        # 确保输出目录存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"开始导出学习指南CSV文件: {output_path}")

        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter)

                # 写入学习指南标题
                writer.writerow([f"英语单词学习指南 - {datetime.now().strftime('%Y-%m-%d')}"])
                writer.writerow([])

                # 写入列标题
                writer.writerow([
                    "单词", "音标", "词性", "中文释义", "记忆技巧", "例句1", "例句2", "例句3",
                    "同义词", "易混淆词", "学习建议"
                ])

                # 写入数据
                for card in cards:
                    examples = self._format_examples_for_study(card.examples)
                    study_suggestion = self._generate_study_suggestion(card)

                    row = [
                        card.word,
                        card.phonetic,
                        card.part_of_speech,
                        card.meaning,
                        f"{card.memory_tip.type + ': ' if card.memory_tip.type else ''}{card.memory_tip.content}",
                        examples.get('example1', ''),
                        examples.get('example2', ''),
                        examples.get('example3', ''),
                        self._format_synonyms(card.synonyms),
                        self._format_confusables(card.confusables),
                        study_suggestion
                    ]

                    writer.writerow(row)

            logger.info(f"学习指南CSV导出完成: {len(cards)} 个卡片已保存到 {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"学习指南CSV导出失败: {e}")
            raise ExportError(f"学习指南CSV导出失败: {e}")

    def _format_front(self, card: WordCard) -> str:
        """格式化卡片正面"""
        return f"{card.word}\n{card.phonetic}"

    def _format_back(self, card: WordCard) -> str:
        """格式化卡片背面"""
        back_parts = [
            f"<b>词性:</b> {card.part_of_speech}",
            f"<b>释义:</b> {card.meaning}",
            f"<b>记忆技巧:</b> {card.memory_tip.type + ': ' if card.memory_tip.type else ''}{card.memory_tip.content}",
        ]

        if card.examples:
            back_parts.append("<b>例句:</b>")
            for i, example in enumerate(card.examples[:3], 1):
                back_parts.append(f"{i}. {example}")

        if card.synonyms:
            back_parts.append(f"<b>同义词:</b> {', '.join(card.synonyms)}")

        if card.confusables:
            back_parts.append(f"<b>易混淆词:</b> {', '.join(card.confusables)}")

        return "<br>".join(back_parts)

    def _format_examples(self, examples: List[str]) -> str:
        """格式化例句"""
        return "; ".join(examples)

    def _format_synonyms(self, synonyms: List[str]) -> str:
        """格式化同义词"""
        return ", ".join(synonyms)

    def _format_confusables(self, confusables: List[str]) -> str:
        """格式化易混淆词"""
        return ", ".join(confusables)

    def _format_tags(self, card: WordCard) -> str:
        """格式化标签"""
        tags = [card.part_of_speech.replace('.', '')]
        if card.memory_tip.type:
            tags.append(card.memory_tip.type)
        return " ".join(tags)

    def _format_examples_for_study(self, examples: List[str]) -> Dict[str, str]:
        """格式化学习用的例句"""
        result = {}
        for i, example in enumerate(examples[:3], 1):
            result[f'example{i}'] = example
        return result

    def _generate_study_suggestion(self, card: WordCard) -> str:
        """生成学习建议"""
        suggestions = []

        # 基于记忆技巧给出建议（如果有类型）
        if card.memory_tip.type:
            if "谐音" in card.memory_tip.type or "Harmonic" in card.memory_tip.type:
                suggestions.append("重点记忆谐音联想")
            elif "拆分" in card.memory_tip.type or "Split" in card.memory_tip.type:
                suggestions.append("注意词根词缀分析")
            elif "词根" in card.memory_tip.type or "Root" in card.memory_tip.type:
                suggestions.append("掌握词根含义，扩展词汇量")
            else:
                suggestions.append(f"运用{card.memory_tip.type}加强记忆")

        # 基于单词特性给出建议
        if len(card.synonyms) > 2:
            suggestions.append("多关注同义词辨析")

        if len(card.confusables) > 1:
            suggestions.append("注意易混淆词区分")

        return "; ".join(suggestions) if suggestions else "常规记忆"

    def get_export_formats(self) -> Dict[str, str]:
        """获取支持的导出格式"""
        return {
            "anki": "Anki标准格式（包含HTML格式）",
            "simple": "简化格式（适合查看）",
            "study_guide": "学习指南格式（适合学习）"
        }

    def preview_export(self, cards: List[WordCard], format_type: str = "anki") -> Dict[str, Any]:
        """预览导出内容"""
        if not cards:
            return {"error": "没有可预览的卡片"}

        preview_cards = cards[:3]  # 只预览前3个卡片

        try:
            if format_type == "anki":
                return {
                    "format": "anki",
                    "sample_cards": [
                        {
                            "front": self._format_front(card),
                            "back": self._format_back(card),
                            "phonetic": card.phonetic,
                            "part_of_speech": card.part_of_speech,
                            "meaning": card.meaning
                        }
                        for card in preview_cards
                    ]
                }
            elif format_type == "simple":
                return {
                    "format": "simple",
                    "sample_cards": [
                        {
                            "单词": card.word,
                            "音标": card.phonetic,
                            "词性": card.part_of_speech,
                            "释义": card.meaning,
                            "记忆技巧": f"{card.memory_tip.type + ': ' if card.memory_tip.type else ''}{card.memory_tip.content}",
                            "例句": self._format_examples(card.examples),
                            "同义词": self._format_synonyms(card.synonyms),
                            "易混淆词": self._format_confusables(card.confusables)
                        }
                        for card in preview_cards
                    ]
                }
            else:
                return {"error": f"不支持的格式: {format_type}"}

        except Exception as e:
            return {"error": f"预览失败: {e}"}