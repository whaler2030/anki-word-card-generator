"""
Anki APKG格式导出器
"""

import genanki
import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.exceptions import ExportError
from utils.logger import get_logger
from data.models import WordCard, ExportSettings

logger = get_logger(__name__)

class AnkiExporter:
    """Anki APKG格式导出器"""

    def __init__(self, export_settings: ExportSettings):
        self.settings = export_settings
        # 初始化在线音频生成器
        try:
            from core.audio_generator_online import OnlineAudioGenerator
            self.audio_generator = OnlineAudioGenerator()
            logger.info("使用在线音频生成器")
        except ImportError:
            # 降级到本地音频生成器
            try:
                from core.audio_generator_simple import SimpleAudioGenerator
                self.audio_generator = SimpleAudioGenerator()
                logger.info("使用简化音频生成器")
            except ImportError:
                from core.audio_generator import AudioGenerator
                self.audio_generator = AudioGenerator()
                logger.info("使用标准音频生成器")

    def export_cards(self, cards: List[WordCard], output_path: str = None) -> str:
        """导出单词卡片到Anki APKG文件"""
        if not cards:
            raise ExportError("没有可导出的单词卡片")

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/anki_deck_{timestamp}.apkg"

        # 确保输出目录存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"开始导出Anki APKG文件: {output_path}")

        try:
            # 生成音频文件（如果启用）
            media_files = {}
            from config.config_parser import ConfigParser
            config = ConfigParser('config.yaml')
            audio_settings = config.get_audio_settings() or {}

            if audio_settings.get('enable_audio', False):
                logger.info("开始生成在线音频链接...")
                media_files = self._generate_audio_links(cards, audio_settings)

            # 创建Anki牌组
            deck = self._create_deck()
            # 使用统一的模型
            model = self._create_model()
            package = genanki.Package(deck)

            # 判断是否有音频需要处理（在线或本地）
            has_audio = any(card.word_audio_url or card.word_audio for card in cards)
            # 在线音频不需要本地文件，但需要设置has_audio标志

            # 添加笔记
            notes = []
            for card in cards:
                if has_audio:
                    note = self._create_note_with_media(card, model, media_files)
                else:
                    note = self._create_note(card, model)
                notes.append(note)

            # 批量添加笔记到牌组
            for note in notes:
                deck.add_note(note)

            # 保存APKG文件
            package.write_to_file(str(output_path))

            # APKG文件创建成功后，清理临时文件（如果设置启用）
            if audio_settings.get('cleanup_temp', True):
                self.audio_generator.cleanup_temp_files()

            logger.info(f"Anki APKG导出完成: {len(cards)} 个卡片已保存到 {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Anki APKG导出失败: {e}")
            raise ExportError(f"Anki APKG导出失败: {e}")

    def _generate_audio_links(self, cards: List[WordCard], audio_settings: Dict) -> Dict[str, str]:
        """生成在线音频链接"""
        media_files = {}

        try:
            # 更新音频生成器设置
            self.audio_generator.settings = audio_settings

            for card in cards:
                # 生成单词发音链接
                if audio_settings.get('generate_word_audio', True):
                    try:
                        word_audio_url = self.audio_generator.generate_word_audio(card.word)
                        if word_audio_url:
                            # 对于在线音频，我们生成一个音频链接HTML
                            audio_html = self.audio_generator.get_audio_link_html(card.word)
                            if audio_html:
                                # 更新卡片数据，保存HTML代码
                                card.word_audio_html = audio_html
                                # 同时保存URL用于可能的直接引用
                                card.word_audio_url = word_audio_url
                                # 为了兼容性，也设置word_audio为URL
                                card.word_audio = word_audio_url
                    except Exception as e:
                        logger.warning(f"生成单词发音链接失败: {card.word}, 错误: {e}")
                        card.word_audio = None

                # 生成例句发音链接
                if audio_settings.get('generate_example_audio', False):
                    example_audio_links = []
                    for i, example in enumerate(card.examples):
                        try:
                            example_audio_url = self.audio_generator.generate_example_audio(example)
                            if example_audio_url:
                                example_audio_links.append(example_audio_url)
                        except Exception as e:
                            logger.warning(f"生成例句发音链接失败: {example[:30]}..., 错误: {e}")
                    card.example_audio_urls = example_audio_links
                else:
                    # 明确设置example_audio_urls为空列表
                    card.example_audio_urls = []

        except Exception as e:
            logger.error(f"生成音频链接时发生错误: {e}")

        return media_files

    def export_deck_with_media(self, cards: List[WordCard], output_path: str = None,
                              media_files: Dict[str, str] = None) -> str:
        """导出带媒体文件的Anki牌组"""
        if not cards:
            raise ExportError("没有可导出的单词卡片")

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/anki_deck_media_{timestamp}.apkg"

        # 确保输出目录存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"开始导出带媒体文件的Anki APKG文件: {output_path}")

        try:
            # 创建牌组和模型
            deck = self._create_deck()
            model = self._create_model_with_media()
            package = genanki.Package(deck)

            # 添加媒体文件
            if media_files:
                package.media_files = list(media_files.values())

            # 添加笔记
            for card in cards:
                note = self._create_note_with_media(card, model, media_files)
                deck.add_note(note)

            # 保存APKG文件
            package.write_to_file(str(output_path))

            logger.info(f"带媒体文件的Anki APKG导出完成: {len(cards)} 个卡片已保存到 {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"带媒体文件的Anki APKG导出失败: {e}")
            raise ExportError(f"带媒体文件的Anki APKG导出失败: {e}")

    def export_csv_for_anki_import(self, cards: List[WordCard], output_path: str = None) -> str:
        """导出CSV格式用于Anki导入"""
        if not cards:
            raise ExportError("没有可导出的单词卡片")

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/anki_import_{timestamp}.csv"

        # 确保输出目录存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"开始导出Anki导入用CSV文件: {output_path}")

        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                import csv
                writer = csv.writer(csvfile)

                # 写入头部
                writer.writerow([
                    "#separator:,",
                    "#html:true",
                    "#columns:Front,Back,Phonetic,Part of Speech,Meaning,Memory Tip,Examples,Synonyms,Confusables,Tags"
                ])

                # 写入数据
                for card in cards:
                    row = [
                        self._format_front_text(card),
                        self._format_back_text(card),
                        card.phonetic,
                        card.part_of_speech,
                        card.meaning,
                        f"{card.memory_tip.type}: {card.memory_tip.content}",
                        self._format_examples_html(card),
                        self._format_synonyms_html(card.synonyms),
                        self._format_confusables_html(card.confusables),
                        self._format_tags_text(card)
                    ]
                    writer.writerow(row)

            logger.info(f"Anki导入用CSV导出完成: {len(cards)} 个卡片已保存到 {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Anki导入用CSV导出失败: {e}")
            raise ExportError(f"Anki导入用CSV导出失败: {e}")

    def _create_deck(self) -> genanki.Deck:
        """创建Anki牌组"""
        # 生成唯一的牌组ID
        deck_id = int(datetime.now().timestamp())

        return genanki.Deck(
            deck_id=deck_id,
            name=self.settings.deck_name,
            description=self.settings.deck_description
        )

    def _create_model(self) -> genanki.Model:
        """创建Anki笔记模型"""
        # 生成唯一的模型ID
        model_id = int(datetime.now().timestamp() * 1000)

        return genanki.Model(
            model_id=model_id,
            name='English Word Card',
            fields=[
                {'name': 'Front'},
                {'name': 'Back'},
                {'name': 'Phonetic'},
                {'name': 'PartOfSpeech'},
                {'name': 'Meaning'},
                {'name': 'MemoryTip'},
                {'name': 'Examples'},
                {'name': 'Synonyms'},
                {'name': 'Confusables'},
                {'name': 'WordAudio'},
                {'name': 'Tags'}
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''
<div class="word">{{Front}}</div>
{{#Phonetic}}
<div class="phonetic">{{Phonetic}}</div>
{{/Phonetic}}
{{#WordAudio}}
<div class="audio-player">
    <audio controls>
        <source src="{{WordAudio}}" type="audio/mpeg">
        <source src="{{WordAudio}}" type="audio/wav">
        <a href="{{WordAudio}}" target="_blank">🔊 播放发音</a>
    </audio>
</div>
{{/WordAudio}}
                    ''',
                    'afmt': '''
<div class="word">{{Front}}</div>
{{#Phonetic}}
<div class="phonetic">{{Phonetic}}</div>
{{/Phonetic}}
{{#WordAudio}}
<div class="audio-player">
    <audio controls>
        <source src="{{WordAudio}}" type="audio/mpeg">
        <source src="{{WordAudio}}" type="audio/wav">
        <a href="{{WordAudio}}" target="_blank">🔊 播放发音</a>
    </audio>
</div>
{{/WordAudio}}

{{#PartOfSpeech}}
<div class="section pos-section">
    <span class="label">词性:</span>
    <span class="content pos">{{PartOfSpeech}}</span>
</div>
{{/PartOfSpeech}}

<div class="section meaning-section">
    <span class="label">释义:</span>
    <span class="content meaning">{{Meaning}}</span>
</div>

{{#MemoryTip}}
<div class="section memory-section">
    <span class="label">记忆技巧:</span>
    <span class="memory-tip">{{MemoryTip}}</span>
</div>
{{/MemoryTip}}

{{#Examples}}
<div class="section examples-section">
    <span class="label">例句:</span>
    <div class="content examples">{{Examples}}</div>
</div>
{{/Examples}}

{{#Synonyms}}
<div class="section synonyms-section">
    <span class="label">同义词:</span>
    <span class="content synonyms">{{Synonyms}}</span>
</div>
{{/Synonyms}}

{{#Confusables}}
<div class="section confusables-section">
    <span class="label">易混淆词:</span>
    <span class="content confusables">{{Confusables}}</span>
</div>
{{/Confusables}}
                    '''
                }
            ],
            css='''
.card {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    padding: 28px;
    margin: 0 auto;
    max-width: 700px;
    border: 1px solid #f0f0f0;
    min-height: 200px;
    color: #1a1a1a;
}

/* 单词、音标、音频各占一行布局 */
.word {
    font-size: 32px;
    font-weight: 700;
    color: #1a1a1a;
    text-align: center;
    margin-bottom: 8px;
    text-transform: capitalize;
    line-height: 1.2;
}

.phonetic {
    font-size: 16px;
    color: #666;
    text-align: center;
    margin-bottom: 16px;
    font-style: italic;
    line-height: 1.4;
}

.audio-player {
    display: block;
    margin-bottom: 24px;
    text-align: center;
    width: 100%;
}

.audio-player audio {
    border-radius: 6px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    outline: none;
    width: 200px;
    height: 36px;
}

.audio-player audio:focus {
    box-shadow: 0 1px 3px rgba(0, 123, 255, 0.3);
    outline: 1px solid #007bff;
}

.audio-player a {
    display: inline-block;
    background: #007bff;
    color: white;
    padding: 8px 14px;
    border-radius: 18px;
    font-size: 14px;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.2s ease;
    border: 1px solid #0056b3;
    margin-left: 8px;
}

.audio-player a:hover {
    background: #0056b3;
    border-color: #004085;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
}

.section {
    margin-bottom: 14px;
    padding: 16px;
    background: #fafbfc;
    border-radius: 8px;
    border-left: 4px solid #e0e0e0;
    transition: all 0.2s ease;
}

/* 为不同部分设置不同的边框颜色 */
.pos-section {
    border-left-color: #0066cc;
}

.meaning-section {
    border-left-color: #d93025;
}

.memory-section {
    border-left-color: #1a73e8;
}

.examples-section {
    border-left-color: #137333;
}

.synonyms-section {
    border-left-color: #ea8600;
}

.confusables-section {
    border-left-color: #c5221f;
}

.label {
    display: inline-block;
    font-weight: 600;
    color: #555;
    margin-bottom: 6px;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.content {
    display: block;
    margin-top: 6px;
    color: #333;
    line-height: 1.5;
}

/* 重点内容使用颜色标注 */
.pos-section .pos {
    color: #0066cc;
    font-weight: 600;
    font-size: 15px;
}

.meaning-section .meaning {
    color: #d93025;
    font-weight: 500;
    font-size: 17px;
    line-height: 1.4;
}

.memory-section .memory-tip {
    color: #1a73e8;
    font-weight: 500;
    font-size: 15px;
    line-height: 1.5;
}

.examples-section .examples {
    color: #137333;
    font-weight: 400;
}

.examples-section ol {
    margin: 8px 0 0 18px;
    padding-left: 0;
}

.examples-section li {
    margin-bottom: 6px;
    line-height: 1.4;
}

.synonyms-section .synonyms {
    color: #ea8600;
    font-weight: 500;
}

.confusables-section .confusables {
    color: #c5221f;
    font-weight: 500;
}

.confusable-item {
    margin-bottom: 8px;
    padding: 6px 8px;
    background: rgba(197, 34, 31, 0.08);
    border-radius: 4px;
    border-left: 3px solid #c5221f;
}

.confusable-item strong {
    color: #c5221f;
    font-weight: 600;
    margin-right: 6px;
}

.tags {
    text-align: center;
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid #e0e0e0;
    color: #666;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

@media (max-width: 600px) {
    .card {
        margin: 0;
        padding: 16px;
        border-radius: 8px;
        max-width: 100%;
    }

    .word {
        font-size: 28px;
        margin-bottom: 6px;
    }

    .phonetic {
        font-size: 14px;
        margin-bottom: 12px;
    }

    .audio-player {
        margin-bottom: 16px;
    }

    .section {
        padding: 12px;
        margin-bottom: 12px;
    }

    .audio-player audio {
        width: 160px;
        height: 32px;
    }

    .audio-player a {
        padding: 6px 12px;
        font-size: 12px;
    }
}

/* 优化深色模式支持 */
@media (prefers-color-scheme: dark) {
    .card {
        background: #1a1a1a;
        border-color: #333;
        color: #ffffff !important;
    }

    .word {
        color: #ffffff !important;
    }

    .section {
        background: #252525;
        border-left-color: #444;
    }

    .label {
        color: #aaa;
    }

    .content {
        color: #ffffff;
    }

    .phonetic {
        color: #aaa;
    }

    .meaning-section .meaning {
        color: #ff6b6b;
    }

    .memory-section .memory-tip {
        color: #4dabf7;
    }

    .examples-section .examples {
        color: #51cf66;
    }

    .synonyms-section .synonyms {
        color: #ffd43b;
    }

    .confusables-section .confusables {
        color: #ff6b6b;
    }

    .confusable-item {
        background: rgba(255, 107, 107, 0.1);
        border-left-color: #ff6b6b;
    }

    .confusable-item strong {
        color: #ff6b6b;
    }
}
            '''
        )

    def _create_model_with_media(self) -> genanki.Model:
        """创建支持媒体的Anki笔记模型"""
        # 这里可以扩展支持音频、图片等媒体文件
        return self._create_model()

    def _create_note(self, card: WordCard, model: genanki.Model) -> genanki.Note:
        """创建Anki笔记"""
        # 格式化记忆技巧显示
        if card.memory_tip.type:
            memory_tip_text = f"{card.memory_tip.type}: {card.memory_tip.content}"
        else:
            memory_tip_text = card.memory_tip.content

        return genanki.Note(
            model=model,
            fields=[
                self._format_front_text(card),
                self._format_back_text(card),
                card.phonetic,
                card.part_of_speech,
                card.meaning,
                memory_tip_text,
                self._format_examples_html(card),
                self._format_synonyms_html(card.synonyms),
                self._format_confusables_html(card.confusables),
                "",  # WordAudio字段为空
                self._format_tags_text(card)
            ],
            tags=self._get_note_tags(card)
        )

    def _create_note_with_media(self, card: WordCard, model: genanki.Model,
                               media_files: Dict[str, str] = None) -> genanki.Note:
        """创建带媒体的Anki笔记"""
        # 获取音频URL或文件名
        word_audio_value = None
        if card.word_audio_url:
            # 优先使用在线音频URL
            word_audio_value = card.word_audio_url
        elif card.word_audio:
            # 如果没有URL，使用文件路径
            word_audio_value = card.word_audio

        # 格式化记忆技巧显示
        if card.memory_tip.type:
            memory_tip_text = f"{card.memory_tip.type}: {card.memory_tip.content}"
        else:
            memory_tip_text = card.memory_tip.content

        return genanki.Note(
            model=model,
            fields=[
                self._format_front_text(card),
                self._format_back_text(card),
                card.phonetic,
                card.part_of_speech,
                card.meaning,
                memory_tip_text,
                self._format_examples_html(card),
                self._format_synonyms_html(card.synonyms),
                self._format_confusables_html(card.confusables),
                word_audio_value or "",
                self._format_tags_text(card)
            ],
            tags=self._get_note_tags(card)
        )

    def _format_front_text(self, card: WordCard) -> str:
        """格式化卡片正面文本"""
        return f"{card.word}"

    def _format_back_text(self, card: WordCard) -> str:
        """格式化卡片背面文本"""
        return f"{card.word}<br>{card.phonetic}"

    def _format_examples_html(self, card: WordCard) -> str:
        """格式化例句为HTML（支持音频）"""
        examples = card.examples
        if not examples:
            return ""

        html_parts = ["<ol>"]
        for i, example in enumerate(examples[:3]):
            # 如果有例句音频URL，添加音频播放器
            audio_html = ""
            if hasattr(card, 'example_audio_urls') and card.example_audio_urls and i < len(card.example_audio_urls):
                audio_url = card.example_audio_urls[i]
                audio_html = f'''
                <div style="margin: 8px 0 8px 20px;">
                    <audio controls style="width: 180px; height: 32px;">
                        <source src="{audio_url}" type="audio/mpeg">
                        <source src="{audio_url}" type="audio/wav">
                        <a href="{audio_url}" target="_blank" style="font-size: 12px; margin-left: 8px;">🔊 播放</a>
                    </audio>
                </div>
                '''
            html_parts.append(f"<li>{example}</li>{audio_html}")
        html_parts.append("</ol>")

        return "".join(html_parts)

    def _format_synonyms_html(self, synonyms: List[str]) -> str:
        """格式化同义词为HTML（每行一个单词加中文释义）"""
        if not synonyms:
            return ""

        # 每行一个同义词，包含中文释义
        formatted_lines = []
        for synonym in synonyms[:5]:  # 最多显示5个同义词
            # 如果已经包含" - "分隔符，处理中文释义部分
            if " - " in synonym:
                parts = synonym.split(" - ", 1)  # 只分割第一次出现的" - "
                word_part = parts[0]
                definition_part = parts[1]

                # 去掉"中文释义："前缀和括号内的解释说明
                if definition_part.startswith("中文释义："):
                    definition_part = definition_part.replace("中文释义：", "")

                # 去掉括号内的解释说明（如：（易与affect混淆，但effect作动词时，意为'产生，引起'））
                import re
                definition_part = re.sub(r'（[^）]*）', '', definition_part).strip()
                definition_part = re.sub(r'\([^)]*\)', '', definition_part).strip()

                formatted_lines.append(f"{word_part} - {definition_part}")
            else:
                definition = self._get_synonym_definition(synonym)
                if definition:
                    formatted_lines.append(f"{synonym} - {definition}")
                else:
                    formatted_lines.append(synonym)

        return "<br>".join(formatted_lines)

    def _format_confusables_html(self, confusables: List[str]) -> str:
        """格式化易混淆词为HTML（每行一个单词加中文释义）"""
        if not confusables:
            return ""

        # 每行一个易混淆词，包含中文释义
        formatted_lines = []
        for confusable in confusables[:3]:  # 最多显示3个易混淆词
            # 如果已经包含" - "分隔符，处理中文释义部分
            if " - " in confusable:
                parts = confusable.split(" - ", 1)  # 只分割第一次出现的" - "
                word_part = parts[0]
                definition_part = parts[1]

                # 去掉"中文释义："前缀和括号内的解释说明
                if definition_part.startswith("中文释义："):
                    definition_part = definition_part.replace("中文释义：", "")

                # 去掉括号内的解释说明（如：（易与affect混淆，但effect作动词时，意为'产生，引起'））
                import re
                definition_part = re.sub(r'（[^）]*）', '', definition_part).strip()
                definition_part = re.sub(r'\([^)]*\)', '', definition_part).strip()

                formatted_lines.append(f"{word_part} - {definition_part}")
            else:
                definition = self._get_confusable_definition(confusable)
                if definition:
                    formatted_lines.append(f"{confusable} - {definition}")
                else:
                    formatted_lines.append(confusable)

        return "<br>".join(formatted_lines)

    def _get_synonym_definition(self, word: str) -> str:
        """获取同义词的中文释义"""
        # 常见同义词的释义映射
        definitions = {
            # A
            "ability": "能力，才能",
            "able": "能够的，有能力的",
            "about": "关于，大约",
            "above": "在...上面",
            "accept": "接受，同意",
            "across": "穿过，横过",
            "act": "行动，表演",
            "action": "行动，行为",
            "active": "活跃的，积极的",
            "actually": "实际上，事实上",
            "add": "添加，增加",
            "address": "地址，演讲",
            "admire": "钦佩，欣赏",
            "admit": "承认，允许进入",
            "adopt": "采用，收养",
            "advance": "前进，预付",
            "advantage": "优势，好处",
            "adventure": "冒险，奇遇",
            "affect": "影响，感动",
            "afraid": "害怕的，担心的",
            "agree": "同意，赞成",
            "aim": "瞄准，目的",
            "allow": "允许，让",
            "almost": "几乎，差不多",
            "alone": "独自地，仅仅",
            "along": "沿着，一起",
            "already": "已经，早已",
            "also": "也，同样",
            "although": "尽管，虽然",
            "always": "总是，永远",
            "amazing": "令人惊奇的",
            "amount": "数量，总计",
            "ancient": "古老的，古代的",
            "anger": "愤怒，生气",
            "angry": "生气的，愤怒的",
            "animal": "动物，兽性的",
            "answer": "回答，答案",
            "anxious": "焦虑的，渴望的",
            "any": "任何，一些",
            "anyone": "任何人",
            "anything": "任何事物",
            "anyway": "无论如何，不管怎样",
            "anywhere": "任何地方",
            "apart": "分开地，除外",
            "appear": "出现，显得",
            "approach": "接近，方法",
            "appropriate": "适当的，拨出",
            "area": "地区，面积",
            "argue": "争论，论证",
            "argument": "争论，论点",
            "arm": "手臂，武器",
            "around": "在周围，大约",
            "arrange": "安排，整理",
            "arrival": "到达，到来",
            "art": "艺术，美术",
            "article": "文章，条款",
            "artist": "艺术家，画家",
            "as": "作为，如同",
            "ask": "问，请求",
            "asleep": "睡着的，麻木的",
            "assist": "协助，帮助",
            "assume": "假定，承担",
            "attack": "攻击，发作",
            "attempt": "尝试，企图",
            "attention": "注意，注意力",
            "attitude": "态度，姿势",
            "attract": "吸引，引起",
            "audience": "听众，观众",
            "available": "可获得的，有空的",
            "avoid": "避免，躲开",
            "awake": "醒着的，唤醒",
            "away": "离开，远离",

            # B
            "back": "背面，后面的",
            "bad": "坏的，有害的",
            "bag": "包，袋",
            "balance": "平衡，余额",
            "ball": "球，舞会",
            "band": "带，乐队",
            "bank": "银行，岸",
            "bar": "条，酒吧",
            "bare": "赤裸的，仅仅",
            "base": "基础，基地",
            "basic": "基本的，基础的",
            "battle": "战斗，斗争",
            "be": "是，存在",
            "beautiful": "美丽的，漂亮的",
            "because": "因为，由于",
            "become": "变成，成为",
            "bed": "床，睡觉",
            "before": "在...之前",
            "begin": "开始",
            "behave": "表现，举止",
            "behind": "在...后面",
            "believe": "相信，认为",
            "belong": "属于，应归入",
            "below": "在...下面",
            "belt": "腰带，地带",
            "bench": "长凳，工作台",
            "bend": "弯曲，弯腰",
            "benefit": "利益，好处",
            "beside": "在旁边，与...相比",
            "best": "最好的，最好地",
            "better": "更好的，较好地",
            "between": "在...之间",
            "beyond": "在...那边，超出",
            "big": "大的，重要的",
            "bill": "账单，钞票",
            "bind": "绑，约束",
            "bird": "鸟，禽",
            "birth": "出生，出身",
            "bit": "一点，小块",
            "bite": "咬，叮",
            "bitter": "苦的，痛苦的",
            "black": "黑色的，黑暗的",
            "blame": "责备，责怪",
            "blank": "空白的，空白",
            "blind": "盲的，盲目的",
            "block": "块，街区，阻塞",
            "blood": "血，血统",
            "blow": "吹，打击",
            "blue": "蓝色的，忧郁的",
            "board": "木板，委员会",
            "boat": "小船，艇",
            "body": "身体，主体",
            "boil": "煮沸，激动",
            "bold": "大胆的，粗体的",
            "bomb": "炸弹，轰炸",
            "bone": "骨，骨骼",
            "book": "书，预订",
            "border": "边界，边沿",
            "bore": "钻孔，厌烦",
            "born": "出生，天生的",
            "borrow": "借入，借用",
            "boss": "老板，首领",
            "both": "两者都，不但...而且",
            "bother": "打扰，麻烦",
            "bottle": "瓶子，装瓶",
            "bottom": "底部，屁股",
            "bounce": "弹跳，跳跃",
            "boundary": "边界，分界线",
            "bow": "弓，鞠躬",
            "bowl": "碗，保龄球",
            "box": "盒子，箱",
            "boy": "男孩，儿子",
            "brain": "大脑，智力",
            "branch": "树枝，分支",
            "brave": "勇敢的，华丽的",
            "bread": "面包，生计",
            "break": "打破，中断",
            "breakfast": "早餐",
            "breath": "呼吸，气息",
            "breathe": "呼吸，流露",
            "bridge": "桥梁，桥牌",
            "bright": "明亮的，聪明的",
            "brilliant": "灿烂的，杰出的",
            "bring": "带来，引起",
            "broad": "宽的，概括的",
            "broadcast": "广播，播撒",
            "broken": "破碎的，破产的",
            "brother": "兄弟，同事",
            "brown": "棕色的，褐色的",
            "brush": "刷子，画笔",
            "build": "建造，建立",
            "building": "建筑物，建筑",
            "burn": "烧，烧伤",
            "burst": "破裂，爆发",

            # C
            "call": "呼叫，称呼",
            "calm": "平静的，安静的",
            "camera": "相机，摄像机",
            "camp": "露营，营地",
            "can": "能够，可以",
            "cancel": "取消，删去",
            "cancer": "癌症，恶性肿瘤",
            "capable": "能够的，有能力的",
            "capital": "首都，大写字母",
            "capture": "捕获，俘虏",
            "care": "关心，照顾",
            "careful": "小心的，仔细的",
            "careless": "粗心的，不小心的",
            "carry": "携带，搬运",
            "case": "情况，案例",
            "catch": "抓住，赶上",
            "cause": "原因，事业",
            "celebrate": "庆祝，庆贺",
            "center": "中心，中央",
            "century": "世纪，百年",
            "ceremony": "典礼，仪式",
            "certain": "确定的，某些",
            "chair": "椅子，主持",
            "challenge": "挑战，质疑",
            "chance": "机会，可能性",
            "change": "改变，零钱",
            "channel": "频道，渠道",
            "chapter": "章节，回",
            "character": "性格，角色",
            "charge": "收费，充电",
            "chase": "追逐，追赶",
            "cheap": "便宜的，廉价的",
            "check": "检查，支票",
            "cheer": "欢呼，高兴",
            "chemical": "化学的，化学制品",
            "chief": "主要的，首领",
            "child": "孩子，儿童",
            "choice": "选择，精选",
            "choose": "选择，挑选",
            "circle": "圆圈，循环",
            "citizen": "公民，市民",
            "city": "城市，都市",
            "claim": "声称，要求",
            "class": "班级，阶级",
            "clean": "清洁的，打扫",
            "clear": "清楚的，明朗的",
            "climate": "气候，风气",
            "climb": "攀登，爬升",
            "clock": "时钟，计时器",
            "close": "关闭，亲密的",
            "cloth": "布，织物",
            "clothes": "衣服，服装",
            "cloud": "云，云状物",
            "club": "俱乐部，棍棒",
            "coach": "教练，长途汽车",
            "coal": "煤，煤块",
            "coast": "海岸，海滨",
            "coat": "外套，涂层",
            "coffee": "咖啡，咖啡色",
            "cold": "冷的，感冒",
            "collect": "收集，聚集",
            "college": "学院，大学",
            "color": "颜色，着色",
            "comb": "梳子，结合",
            "come": "来，出现",
            "comfort": "舒适，安慰",
            "command": "命令，指挥",
            "comment": "评论，意见",
            "common": "共同的，普通的",
            "company": "公司，陪伴",
            "compare": "比较，相比",
            "compete": "竞争，比赛",
            "complete": "完整的，完成",
            "complex": "复杂的，综合的",
            "concern": "关心，关注",
            "condition": "条件，状况",
            "conduct": "进行，行为",
            "confess": "承认，忏悔",
            "confidence": "信心，信任",
            "connect": "连接，联系",
            "conscious": "有意识的，神志清醒的",
            "consider": "考虑，认为",
            "consist": "由...组成，一致",
            "contact": "接触，联系",
            "contain": "包含，容纳",
            "content": "内容，满足的",
            "continue": "继续，连续",
            "contract": "合同，收缩",
            "control": "控制，管理",
            "conversation": "谈话，会话",
            "cook": "烹饪，厨师",
            "cool": "凉爽的，酷的",
            "copy": "复制，副本",
            "corner": "角落，拐角",
            "correct": "正确的，纠正",
            "cost": "成本，花费",
            "cottage": "小屋，村舍",
            "cotton": "棉花，棉布",
            "cough": "咳嗽，咳嗽声",
            "count": "计数，计算",
            "country": "国家，乡村",
            "couple": "一对，夫妻",
            "courage": "勇气，胆量",
            "course": "课程，过程",
            "cover": "覆盖，封面",
            "crash": "碰撞，崩溃",
            "crazy": "疯狂的，狂热的",
            "create": "创造，创作",
            "creature": "生物，动物",
            "credit": "信用，学分",
            "crime": "犯罪，罪行",
            "criticize": "批评，评论",
            "crop": "作物，收成",
            "cross": "十字，交叉",
            "crowd": "人群，群众",
            "crowded": "拥挤的，人满为患的",
            "cry": "哭，喊叫",
            "culture": "文化，培养",
            "cup": "杯子，杯状物",
            "cure": "治愈，疗法",
            "curious": "好奇的，奇特的",
            "current": "当前的，水流",
            "curtain": "窗帘，幕",
            "curve": "曲线，弯曲",
            "custom": "习惯的，定制的",
            "customer": "顾客，客户",
            "cut": "切割，削减",

            # D
            "damage": "损害，破坏",
            "dance": "舞蹈，跳舞",
            "danger": "危险，威胁",
            "dark": "黑暗的，暗的",
            "data": "数据，资料",
            "date": "日期，约会",
            "daughter": "女儿",
            "day": "天，白天",
            "dead": "死的，无感觉的",
            "deal": "交易，处理",
            "dear": "亲爱的，昂贵的",
            "death": "死亡，逝世",
            "debt": "债务，欠款",
            "decide": "决定，下决心",
            "deep": "深的，深刻的",
            "defeat": "击败，失败",
            "defense": "防御，保卫",
            "degree": "程度，学位",
            "delay": "延迟，耽搁",
            "delicate": "精致的，易碎的",
            "delicious": "美味的，可口的",
            "delight": "快乐，高兴",
            "deliver": "递送，发表",
            "demand": "要求，需求",
            "depart": "离开，出发",
            "depend": "依赖，依靠",
            "describe": "描述，描绘",
            "desert": "沙漠，抛弃",
            "deserve": "应受，值得",
            "design": "设计，图案",
            "desire": "渴望，欲望",
            "desk": "书桌，办公桌",
            "destroy": "破坏，消灭",
            "detail": "细节，详情",
            "develop": "发展，开发",
            "device": "装置，设备",
            "dialogue": "对话，对白",
            "difference": "差异，不同",
            "difficult": "困难的，艰难的",
            "dinner": "晚餐，正餐",
            "direct": "直接的，指导",
            "direction": "方向，指导",
            "dirty": "脏的，卑鄙的",
            "discover": "发现，发觉",
            "discuss": "讨论，议论",
            "disease": "疾病，弊病",
            "dish": "盘子，菜肴",
            "dismiss": "解散，解雇",
            "display": "显示，展览",
            "distance": "距离，远处",
            "distribute": "分配，分发",
            "district": "地区，区域",
            "divide": "划分，除",
            "divorce": "离婚，分离",
            "do": "做，干",
            "doctor": "医生，博士",
            "document": "文件，文献",
            "dog": "狗，犬",
            "domestic": "家庭的，国内的",
            "door": "门，入口",
            "double": "双倍的，双重",
            "doubt": "怀疑，疑惑",
            "down": "向下，在下面",
            "draft": "草稿，征兵",
            "drag": "拖，拉",
            "draw": "画，拉",
            "dream": "梦，梦想",
            "dress": "连衣裙，穿着",
            "drink": "喝，饮料",
            "drive": "驾驶，驱赶",
            "drop": "掉下，滴",
            "drug": "药物，毒品",
            "drum": "鼓，圆桶",
            "dry": "干的，干燥的",
            "duck": "鸭子，闪避",
            "due": "应支付的，预期的",
            "dull": "迟钝的，枯燥的",
            "during": "在...期间",
            "dust": "灰尘，尘土",
            "duty": "责任，义务",

            # E
            "each": "每个，各自",
            "eager": "渴望的，热切的",
            "early": "早的，早期的",
            "earn": "赚得，赢得",
            "earth": "地球，泥土",
            "ease": "容易，舒适",
            "east": "东，东方",
            "edge": "边缘，刀口",
            "educate": "教育，培养",
            "effect": "效果，影响",
            "effort": "努力，尝试",
            "egg": "蛋，卵",
            "eight": "八",
            "either": "任一的，也",
            "elder": "年长者，资格老的",
            "elect": "选举，选择",
            "electric": "电的，电动的",
            "elegant": "优雅的，高雅的",
            "element": "元素，要素",
            "elephant": "大象，庞然大物",
            "else": "其他，否则",
            "embarrass": "使尴尬，使窘迫",
            "emerge": "出现，浮现",
            "emergency": "紧急情况，突发事件",
            "emotion": "情感，情绪",
            "employ": "雇用，使用",
            "empty": "空的，空洞的",
            "enable": "使能够，使可能",
            "encourage": "鼓励，激励",
            "end": "结束，端",
            "enemy": "敌人，仇敌",
            "energy": "能量，精力",
            "engage": "从事，订婚",
            "engine": "发动机，引擎",
            "enjoy": "享受，喜欢",
            "enough": "足够的",
            "enter": "进入，加入",
            "entertainment": "娱乐，招待",
            "enthusiastic": "热情的，热心的",
            "entire": "全部的，整个的",
            "entrance": "入口，进入",
            "envelope": "信封，包裹",
            "environment": "环境，外界",
            "equal": "平等的，等于",
            "equip": "装备，配备",
            "error": "错误，误差",
            "escape": "逃跑，逃避",
            "especially": "特别，尤其",
            "establish": "建立，确立",
            "estimate": "估计，评价",
            "even": "甚至，平坦的",
            "evening": "晚上，傍晚",
            "event": "事件，活动",
            "eventually": "最终，后来",
            "ever": "曾经，永远",
            "every": "每个，每一",
            "evidence": "证据，迹象",
            "exact": "精确的，确切的",
            "examine": "检查，诊察",
            "example": "例子，榜样",
            "excellent": "优秀的，卓越的",
            "except": "除了...之外",
            "exchange": "交换，交流",
            "excite": "使兴奋，使激动",
            "excuse": "借口，原谅",
            "exercise": "锻炼，练习",
            "exhibition": "展览，显示",
            "exist": "存在，生存",
            "exit": "出口，离开",
            "expect": "期望，预期",
            "expensive": "昂贵的",
            "experience": "经验，体验",
            "experiment": "实验，试验",
            "expert": "专家，熟练的",
            "explain": "解释，说明",
            "explode": "爆炸，爆发",
            "explore": "探索，探测",
            "export": "出口，输出",
            "express": "表达，表示",
            "extend": "延伸，扩展",
            "extra": "额外的，附加的",
            "extreme": "极端的，极度的",
            "eye": "眼睛，眼光",

            # F
            "face": "脸，面对",
            "fact": "事实，实际情况",
            "factory": "工厂，制造厂",
            "fail": "失败，不及格",
            "fair": "公平的，集市",
            "faith": "信任，信仰",
            "fall": "落下，秋天",
            "false": "假的，错误的",
            "family": "家庭，家族",
            "famous": "著名的",
            "fan": "扇子，爱好者",
            "fancy": "幻想，花式的",
            "fantastic": "极好的，奇异的",
            "far": "远的，遥远的",
            "farm": "农场，养殖",
            "fashion": "时尚，方式",
            "fast": "快的，紧的",
            "fat": "胖的，脂肪",
            "father": "父亲",
            "fault": "错误，缺点",
            "favor": "喜爱，偏爱",
            "favorite": "最喜欢的",
            "fear": "恐惧，担心",
            "feather": "羽毛",
            "feature": "特征，特色",
            "fee": "费，酬金",
            "feed": "喂养，饲料",
            "feel": "感觉，触摸",
            "female": "女性的，雌性的",
            "fence": "栅栏，围墙",
            "festival": "节日，庆祝活动",
            "few": "很少的，一些",
            "field": "田野，领域",
            "fierce": "凶猛的，强烈的",
            "fight": "打架，战斗",
            "figure": "数字，人物",
            "fill": "填充，装满",
            "film": "电影，薄膜",
            "final": "最终的，决赛",
            "find": "找到，发现",
            "fine": "好的，罚款",
            "finger": "手指，指针",
            "finish": "完成，结束",
            "fire": "火，解雇",
            "firm": "公司，坚固的",
            "first": "第一，首先",
            "fish": "鱼，鱼肉",
            "fit": "适合的，健康的",
            "five": "五",
            "fix": "固定，修理",
            "flag": "旗帜，标记",
            "flame": "火焰，热情",
            "flash": "闪光，闪现",
            "flat": "平的，公寓",
            "flee": "逃跑，逃离",
            "flesh": "肉，肉体",
            "flight": "航班，飞行",
            "float": "漂浮，浮动",
            "flood": "洪水，水灾",
            "floor": "地板，楼层",
            "flour": "面粉",
            "flow": "流动，流量",
            "flower": "花，开花",
            "fly": "飞，苍蝇",
            "focus": "焦点，集中",
            "fog": "雾，烟雾",
            "fold": "折叠，羊圈",
            "follow": "跟随，遵循",
            "food": "食物，食品",
            "fool": "傻瓜，愚弄",
            "foolish": "愚蠢的，傻的",
            "foot": "脚，英尺",
            "football": "足球",
            "for": "为了，因为",
            "force": "力量，强制",
            "foreign": "外国的，外来的",
            "forest": "森林",
            "forget": "忘记，忽略",
            "form": "形式，表格",
            "formal": "正式的，形式的",
            "former": "以前的，前者",
            "fortunate": "幸运的，侥幸的",
            "fortune": "财富，运气",
            "forward": "向前，转寄",
            "found": "找到，创立",
            "four": "四",
            "fourth": "第四",
            "frame": "框架，帧",
            "free": "自由的，免费的",
            "freedom": "自由，自主",
            "freeze": "冷冻，结冰",
            "fresh": "新鲜的，淡水的",
            "fridge": "冰箱",
            "friend": "朋友，友好",
            "friendly": "友好的，朋友般的",
            "frighten": "使惊恐，吓唬",
            "frog": "青蛙",
            "from": "从，来自",
            "front": "前面，正面",
            "fruit": "水果，结果",
            "fry": "油炸，煎",
            "fuel": "燃料，刺激",
            "full": "满的，完全的",
            "fun": "乐趣，开玩笑",
            "function": "功能，函数",
            "funny": "有趣的，滑稽的",
            "furniture": "家具",
            "future": "将来，未来"
        }

        # 获取释义，如果找不到则生成通用说明
        definition = definitions.get(word.lower())
        if definition:
            return definition
        else:
            # 对于未在映射中的词，返回简单的说明
            return self._generate_synonym_definition(word)

    def _generate_synonym_definition(self, word: str) -> str:
        """为未知同义词生成合理的中文释义"""
        # 基于常见词根和词缀的分析

        if word.startswith('un'):
            return "不，非，相反的"
        elif word.startswith('re'):
            return "再，重新，回来"
        elif word.startswith('dis'):
            return "不，分离，相反的"
        elif word.startswith('mis'):
            return "错误的，不好的"
        elif word.startswith('pre'):
            return "在...之前，预先"
        elif word.startswith('post'):
            return "在...之后，后来的"
        elif word.startswith('fore'):
            return "前，先，预先"
        elif word.endswith('able'):
            return "能够...的，可以...的"
        elif word.endswith('ible'):
            return "能够...的，可以...的"
        elif word.endswith('ful'):
            return "充满...的，有...性质的"
        elif word.endswith('less'):
            return "没有...的，不...的"
        elif word.endswith('ment'):
            return "...的行为或状态"
        elif word.endswith('tion'):
            return "...的行为或过程"
        elif word.endswith('sion'):
            return "...的行为或状态"
        elif word.endswith('ness'):
            return "...的性质或状态"
        elif word.endswith('ity'):
            return "...的性质或状态"
        elif word.endswith('ize'):
            return "使...化，变成..."
        elif word.endswith('ism'):
            return "...主义，学说"
        elif word.endswith('ist'):
            return "...主义者，从事...的人"
        elif word.endswith('or'):
            return "...的人，...物"
        elif word.endswith('er'):
            return "...的人，从事...的人"
        elif word.endswith('ary'):
            return "...的，与...有关的"
        elif word.endswith('ic'):
            return "...的，与...有关的"
        elif word.endswith('al'):
            return "...的，与...有关的"
        elif word.endswith('ous'):
            return "充满...的，多...的"
        elif word.endswith('ive'):
            return "有...倾向的，...性的"
        elif word.endswith('ly'):
            return "...地，以...方式"
        elif word.endswith('ward'):
            return "向...的，朝...方向的"
        elif word.endswith('wise'):
            return "在...方面，关于...地"
        else:
            # 完全无法推测的词，给出一个通用的说明
            return "含义相近的词"

    def _get_confusable_definition(self, word: str) -> str:
        """获取易混淆词的中文释义"""
        # 完整的易混淆词释义映射
        definitions = {
            # A
            "affect": "影响（动词）",
            "effect": "效果（名词）",
            "accept": "接受",
            "except": "除了",
            "advice": "建议（名词）",
            "advise": "建议（动词）",
            "aisle": "过道",
            "isle": "小岛",
            "allusion": "暗示",
            "illusion": "幻觉",
            "altar": "祭坛",
            "alter": "改变",

            # B
            "bare": "赤裸的",
            "bear": "熊",
            "board": "木板",
            "bored": "无聊的",
            "brake": "刹车",
            "break": "打破",
            "buy": "买",
            "by": "被",
            "bye": "再见",

            # C
            "capital": "首都/大写字母",
            "capitol": "国会大厦",
            "cell": "细胞",
            "sell": "卖",
            "cite": "引用",
            "site": "地点",
            "sight": "视力",
            "complement": "补充",
            "compliment": "赞美",
            "coarse": "粗糙的",
            "course": "课程",
            "confidant": "知己",
            "confident": "自信的",

            # D
            "desert": "沙漠",
            "dessert": "甜点",
            "discreet": "谨慎的",
            "discrete": "离散的",

            # E
            "emigrate": "移居国外",
            "immigrate": "移居入境",
            "eminent": "著名的",
            "imminent": "即将发生的",
            "everyday": "日常的",
            "every day": "每天",

            # F
            "fair": "公平的",
            "fare": "费用",
            "find": "找到",
            "fined": "被罚款",
            "flea": "跳蚤",
            "flee": "逃跑",

            # G
            "grate": "磨碎",
            "great": "伟大的",

            # H
            "hear": "听到",
            "here": "这里",
            "hole": "洞",
            "whole": "整个",
            "horde": "人群",
            "hoard": "囤积",

            # I
            "its": "它的",
            "it's": "它是",

            # K
            "knight": "骑士",
            "night": "夜晚",

            # L
            "loose": "松的",
            "lose": "失去",
            "lead": "领导",
            "led": "领导过",
            "lightning": "闪电",
            "lightening": "变亮",

            # M
            "mail": "邮件",
            "male": "男性",
            "mantle": "披风",
            "mental": "精神的",
            "miner": "矿工",
            "minor": "较小的",

            # N
            "no": "不",
            "know": "知道",
            "not": "不",
            "knot": "结",

            # P
            "pail": "桶",
            "pale": "苍白的",
            "pair": "一对",
            "pear": "梨",
            "patience": "耐心",
            "patients": "病人",
            "peace": "和平",
            "piece": "一块",
            "plain": "朴素的",
            "plane": "飞机",
            "poor": "贫穷的",
            "pour": "倒",
            "pray": "祈祷",
            "prey": "猎物",
            "principal": "主要的/校长",
            "principle": "原则",

            # Q
            "quart": "夸脱",
            "court": "法庭",

            # R
            "rain": "雨",
            "reign": "统治",
            "rein": "缰绳",
            "raise": "举起",
            "raze": "夷平",
            "rap": "说唱/轻敲",
            "wrap": "包装/包裹",
            "crap": "废话/废物",
            "trap": "陷阱",
            "warp": "弯曲/变形",
            "read": "阅读",
            "red": "红色",

            # S
            "sail": "航行",
            "sale": "销售",
            "seam": "接缝",
            "seem": "似乎",
            "seed": "种子",
            "cede": "割让",
            "sight": "视力",
            "site": "地点",
            "cite": "引用",
            "sole": "唯一的",
            "soul": "灵魂",
            "some": "一些",
            "sum": "总计",
            "stationary": "静止的",
            "stationery": "文具",

            # T
            "than": "比",
            "then": "然后",
            "their": "他们的",
            "there": "那里",
            "they're": "他们是",
            "through": "通过",
            "threw": "投掷",
            "throne": "王位",
            "thrown": "被投掷",
            "to": "到",
            "too": "也",
            "two": "二",

            # V
            "vale": "山谷",
            "veil": "面纱",

            # W
            "wait": "等待",
            "weight": "重量",
            "waive": "放弃",
            "wave": "波浪",
            "weak": "弱的",
            "week": "周",
            "weather": "天气",
            "whether": "是否",
            "which": "哪个",
            "witch": "女巫",
            "who's": "谁是",
            "whose": "谁的",
            "wood": "木头",
            "would": "将会",

            # Y
            "yoke": "轭",
            "yolk": "蛋黄",

            # Y
            "your": "你的",
            "you're": "你是"
        }

        # 获取释义，如果找不到则生成通用说明
        definition = definitions.get(word.lower())
        if definition:
            return definition
        else:
            # 对于未在映射中的词，通过词根和词义分析提供合理释义
            return self._generate_confusable_definition(word)

    def _generate_confusable_definition(self, word: str) -> str:
        """为未知易混淆词生成合理的中文释义"""
        # 基于常见易混淆词模式的分析

        # 常见易混淆词的发音/拼写模式
        common_patterns = {
            # 相似结尾（按具体程度排序，更具体的模式放前面）
            "disability$": "残疾，无能力",
            "liability$": "责任，负债",
            "ability$": "能力，才能",
            "abide$": "忍受，居住",
            "abandon$": "放弃，抛弃",
            "able$": "能够的，有能力的",
            "about$": "关于，大约",
            "above$": "在...上面",
            "abroad$": "在国外，到国外",
            "absence$": "缺席，不在",
            "absent$": "缺席的，不在的",
            "absolute$": "绝对的，完全的",
            "absorb$": "吸收，吸引",
            "abstract$": "抽象的，摘要",
            "abundant$": "丰富的，充裕的",
            "abuse$": "滥用，虐待",
            "academic$": "学术的，学院的",
            "academy$": "学院，研究院",
            "accelerate$": "加速，促进",
            "accent$": "口音，重音",
            "accept$": "接受，同意",
            "acceptable$": "可接受的",
            "access$": "进入，使用权",
            "accessible$": "可接近的，易理解的",
            "accident$": "事故，意外",
            "accidental$": "意外的，偶然的",
            "accommodate$": "适应，容纳",
            "accompany$": "陪伴，伴随",
            "accomplish$": "完成，实现",
            "accord$": "符合，协议",
            "according$": "根据，按照",
            "accordingly$": "因此，相应地",
            "account$": "账户，说明",
            "accumulate$": "积累，聚集",
            "accuracy$": "准确性，精确度",
            "accurate$": "准确的，精确的",
            "accuse$": "指责，控告",
            "accustom$": "使习惯于",
            "achieve$": "实现，达到",
            "achievement$": "成就，功绩",
            "acid$": "酸，酸性的",
            "acknowledge$": "承认，确认",
            "acquire$": "获得，学到",
            "acquisition$": "获得，收购",
            "across$": "穿过，交叉",
            "act$": "行动，表演",
            "action$": "行动，行为",
            "active$": "活跃的，积极的",
            "activity$": "活动，行为",
            "actor$": "演员，行动者",
            "actual$": "实际的，真实的",
            "actually$": "实际上，事实上",
            "acute$": "急性的，敏锐的",
            "adapt$": "适应，改编",
            "add$": "添加，增加",
            "addition$": "加法，附加物",
            "additional$": "额外的，附加的",
            "address$": "地址，演讲",
            "adequate$": "充足的，适当的",
            "adjust$": "调整，适应",
            "administration$": "管理，行政",
            "administrative$": "管理的，行政的",
            "admire$": "钦佩，欣赏",
            "admission$": "允许进入，承认",
            "admit$": "承认，允许进入",
            "adopt$": "采用，收养",
            "adult$": "成年人，成年的",
            "advance$": "前进，预付",
            "advanced$": "先进的，高级的",
            "advantage$": "优势，好处",
            "adventure$": "冒险，奇遇",
            "adverse$": "不利的，相反的",
            "advertise$": "做广告，宣传",
            "advertisement$": "广告，宣传",
            "advice$": "建议，忠告",
            "advise$": "建议，劝告",
            "advocate$": "提倡，拥护者",
            "affair$": "事务，事件",
            "affect$": "影响，感动",
            "affection$": "喜爱，感情",
            "afford$": "负担得起，提供",
            "afraid$": "害怕的，担心的",
            "Africa$": "非洲",
            "African$": "非洲的，非洲人",
            "after$": "在...之后",
            "afternoon$": "下午，午后",
            "afterward$": "后来，然后",
            "again$": "又，再次",
            "against$": "反对，靠着",
            "age$": "年龄，时代",
            "aged$": "年老的，...岁的",
            "agency$": "代理机构，中介",
            "agent$": "代理人，特工",
            "aggressive$": "侵略的，积极的",
            "ago$": "以前，前",
            "agree$": "同意，赞成",
            "agreement$": "同意，协议",
            "agriculture$": "农业，农学",
            "ahead$": "在前，向前",
            "aid$": "帮助，援助",
            "aim$": "瞄准，目的",
            "air$": "空气，航空",
            "aircraft$": "飞机，航空器",
            "airline$": "航空公司",
            "airplane$": "飞机",
            "airport$": "机场",
            "alarm$": "警报，惊慌",
            "album$": "专辑，相册",
            "alcohol$": "酒精，乙醇",
            "alert$": "警觉的，警报",
            "alike$": "相似的，同样地",
            "alive$": "活着的，活跃的",
            "all$": "所有，全部",
            "alliance$": "联盟，联姻",
            "allow$": "允许，让",
            "allowance$": "津贴，允许",
            "almost$": "几乎，差不多",
            "alone$": "独自地，仅仅",
            "along$": "沿着，一起",
            "alongside$": "在旁边，与...并排",
            "already$": "已经，早已",
            "also$": "也，同样",
            "alter$": "改变，修改",
            "alternative$": "替代的，选择",
            "although$": "尽管，虽然",
            "altogether$": "完全，总共",
            "always$": "总是，永远",
            "amazing$": "令人惊奇的",
            "ambition$": "野心，雄心",
            "ambulance$": "救护车",
            "among$": "在...之中",
            "amongst$": "在...之中",
            "amount$": "数量，总计",
            "analysis$": "分析，解析",
            "analyze$": "分析，解析",
            "ancient$": "古老的，古代的",
            "anger$": "愤怒，生气",
            "angle$": "角度，角",
            "angry$": "生气的，愤怒的",
            "animal$": "动物，兽性的",
            "anniversary$": "周年纪念",
            "announce$": "宣布，发表",
            "annoy$": "使烦恼，打扰",
            "annual$": "年度的，每年的",
            "another$": "另一个，又一个",
            "answer$": "回答，答案",
            "anticipate$": "预期，预料",
            "anxiety$": "焦虑，担忧",
            "anxious$": "焦虑的，渴望的",
            "any$": "任何，一些",
            "anybody$": "任何人，重要人物",
            "anyhow$": "无论如何，不管怎样",
            "anyone$": "任何人",
            "anything$": "任何事物",
            "anyway$": "无论如何，不管怎样",
            "anywhere$": "任何地方",
            "apart$": "分开地，除外",
            "apartment$": "公寓，房间",
            "apologize$": "道歉，谢罪",
            "apology$": "道歉，谢罪",
            "apparent$": "明显的，表面的",
            "apparently$": "显然，表面上",
            "appeal$": "呼吁，吸引力",
            "appear$": "出现，显得",
            "appearance$": "外貌，出现",
            "apple$": "苹果",
            "application$": "申请，应用",
            "apply$": "申请，应用",
            "appoint$": "任命，约定",
            "appointment$": "约会，任命",
            "appreciate$": "欣赏，感激",
            "approach$": "接近，方法",
            "appropriate$": "适当的，拨出",
            "approval$": "批准，赞成",
            "approve$": "批准，赞成",
            "approximately$": "大约，近似地",
            "April$": "四月",
            "arbitrary$": "任意的，专断的",
            "architect$": "建筑师",
            "architecture$": "建筑学，建筑",
            "area$": "地区，面积",
            "argue$": "争论，论证",
            "argument$": "争论，论点",
            "arise$": "出现，产生",
            "arm$": "手臂，武器",
            "armed$": "武装的，有扶手的",
            "army$": "军队，陆军",
            "around$": "在周围，大约",
            "arrange$": "安排，整理",
            "arrangement$": "安排，整理",
            "arrest$": "逮捕，阻止",
            "arrival$": "到达，到来",
            "arrive$": "到达，成功",
            "arrow$": "箭，箭头",
            "art$": "艺术，美术",
            "article$": "文章，条款",
            "artificial$": "人工的，人造的",
            "artist$": "艺术家，画家",
            "artistic$": "艺术的，有艺术天赋的",
            "as$": "作为，如同",
            "ashamed$": "羞愧的，惭愧的",
            "Asia$": "亚洲",
            "Asian$": "亚洲的，亚洲人",
            "aside$": "在旁边，除...外",
            "ask$": "问，请求",
            "asleep$": "睡着的，麻木的",
            "aspect$": "方面，样子",
            "assess$": "评估，评定",
            "assessment$": "评估，评定",
            "assign$": "分配，指派",
            "assignment$": "任务，分配",
            "assist$": "协助，帮助",
            "assistance$": "协助，帮助",
            "assistant$": "助手，助理",
            "associate$": "联系，同事",
            "association$": "协会，联系",
            "assume$": "假定，承担",
            "assumption$": "假定，假设",
            "assure$": "保证，使确信",
            "astonish$": "使惊讶，使吃惊",
            "astronaut$": "宇航员",
            "at$": "在，向",
            "athlete$": "运动员，体育家",
            "athletic$": "运动的，体育的",
            "Atlantic$": "大西洋的",
            "atmosphere$": "大气，气氛",
            "atom$": "原子，微粒",
            "atomic$": "原子的，原子能的",
            "attach$": "附上，贴上",
            "attack$": "攻击，发作",
            "attempt$": "尝试，企图",
            "attend$": "出席，参加",
            "attention$": "注意，注意力",
            "attitude$": "态度，姿势",
            "attorney$": "律师，代理人",
            "attract$": "吸引，引起",
            "attraction$": "吸引，吸引力",
            "attractive$": "有吸引力的",
            "audience$": "听众，观众",
            "August$": "八月",
            "aunt$": "姑，姨，婶",
            "Australia$": "澳大利亚",
            "Australian$": "澳大利亚的，澳大利亚人",
            "author$": "作者，创始人",
            "authority$": "权威，当局",
            "auto$": "汽车，自动的",
            "automatic$": "自动的，机械的",
            "autumn$": "秋天，秋季",
            "available$": "可获得的，有空的",
            "avenue$": "大道，途径",
            "average$": "平均的，普通的",
            "avoid$": "避免，躲开",
            "award$": "奖，授予",
            "aware$": "意识到的，知道的",
            "away$": "离开，远离",
            "awful$": "糟糕的，可怕的",
            "baby$": "婴儿，幼稚的",
            "back$": "背面，后面的",
            "background$": "背景，经历",
            "backward$": "向后的，落后的",
            "bad$": "坏的，有害的",
            "badly$": "坏地，严重地",
            "bag$": "包，袋",
            "baggage$": "行李",
            "bake$": "烤，烘焙",
            "balance$": "平衡，余额",
            "ball$": "球，舞会",
            "balloon$": "气球",
            "banana$": "香蕉",
            "band$": "带，乐队",
            "bank$": "银行，岸",
            "bar$": "条，酒吧",
            "bare$": "赤裸的，仅仅",
            "barely$": "仅仅，几乎没有",
            "bargain$": "便宜货，交易",
            "bark$": "狗叫，树皮",
            "barrel$": "桶，枪管",
            "barrier$": "障碍物，屏障",
            "base$": "基础，基地",
            "baseball$": "棒球",
            "basic$": "基本的，基础的",
            "basically$": "基本上，主要地",
            "basin$": "盆地，脸盆",
            "basis$": "基础，根据",
            "basket$": "篮，筐",
            "basketball$": "篮球",
            "bat$": "蝙蝠，球棒",
            "bath$": "洗澡，浴缸",
            "bathe$": "洗澡，游泳",
            "bathroom$": "浴室，盥洗室",
            "battery$": "电池，炮组",
            "battle$": "战斗，斗争",
            "bay$": "海湾，狗吠声",
            "be$": "是，存在",
            "beach$": "海滩",
            "beam$": "梁，光束",
            "bean$": "豆，豆类",
            "bear$": "熊，忍受",
            "beard$": "胡须",
            "beast$": "野兽，牲畜",
            "beat$": "打，击败",
            "beautiful$": "美丽的，漂亮的",
            "beauty$": "美丽，美人",
            "because$": "因为，由于",
            "become$": "变成，成为",
            "bed$": "床，睡觉",
            "bedroom$": "卧室",
            "bee$": "蜜蜂",
            "beef$": "牛肉",
            "beer$": "啤酒",
            "before$": "在...之前",
            "beg$": "乞求，请求",
            "begin$": "开始",
            "beginning$": "开始，开端",
            "behalf$": "代表，利益",
            "behave$": "表现，举止",
            "behavior$": "行为，举止",
            "behind$": "在...后面",
            "being$": "存在，生物",
            "belief$": "信念，信仰",
            "believe$": "相信，认为",
            "bell$": "铃，钟声",
            "belong$": "属于，应归入",
            "below$": "在...下面",
            "belt$": "腰带，地带",
            "bench$": "长凳，工作台",
            "bend$": "弯曲，弯腰",
            "beneath$": "在...下方",
            "beneficial$": "有益的，有利的",
            "benefit$": "利益，好处",
            "beside$": "在旁边，与...相比",
            "besides$": "此外，而且",
            "best$": "最好的，最好地",
            "bet$": "打赌，确信",
            "better$": "更好的，较好地",
            "between$": "在...之间",
            "beyond$": "在...那边，超出",
            "Bible$": "圣经",
            "bicycle$": "自行车",
            "big$": "大的，重要的",
            "bike$": "自行车，摩托车",
            "bill$": "账单，钞票",
            "billion$": "十亿",
            "bind$": "绑，约束",
            "biology$": "生物学",
            "bird$": "鸟，禽",
            "birth$": "出生，出身",
            "birthday$": "生日",
            "bit$": "一点，小块",
            "bite$": "咬，叮",
            "bitter$": "苦的，痛苦的",
            "black$": "黑色的，黑暗的",
            "blade$": "刀片，叶片",
            "blame$": "责备，责怪",
            "blank$": "空白的，空白",
            "blanket$": "毯子，厚层",
            "blast$": "爆炸，一阵",
            "bleed$": "流血，榨取",
            "blend$": "混合，融合",
            "bless$": "祝福，保佑",
            "blind$": "盲的，盲目的",
            "block$": "块，街区，阻塞",
            "blood$": "血，血统",
            "bloody$": "有血的，非常的",
            "bloom$": "开花，繁荣",
            "blow$": "吹，打击",
            "blue$": "蓝色的，忧郁的",
            "blush$": "脸红，害羞",
            "board$": "木板，委员会",
            "boast$": "自夸，以...自豪",
            "boat$": "小船，艇",
            "body$": "身体，主体",
            "boil$": "煮沸，激动",
            "bold$": "大胆的，粗体的",
            "bomb$": "炸弹，轰炸",
            "bond$": " bond，粘合剂",
            "bone$": "骨，骨骼",
            "book$": "书，预订",
            "boom$": "繁荣，隆隆声",
            "boost$": "提高，推动",
            "boot$": "靴子，启动",
            "border$": "边界，边沿",
            "bored$": "无聊的，烦人的",
            "boring$": "无聊的，钻孔的",
            "born$": "出生，天生的",
            "borrow$": "借入，借用",
            "boss$": "老板，首领",
            "both$": "两者都，不但...而且",
            "bother$": "打扰，麻烦",
            "bottle$": "瓶子，装瓶",
            "bottom$": "底部，屁股",
            "bounce$": "弹跳，跳跃",
            "bound$": "有义务的，必定的",
            "boundary$": "边界，分界线",
            "bow$": "弓，鞠躬",
            "bowl$": "碗，保龄球",
            "box$": "盒子，箱",
            "boy$": "男孩，儿子",
            "brain$": "大脑，智力",
            "brake$": "刹车，阻碍",
            "branch$": "树枝，分支",
            "brand$": "商标，烙印",
            "brave$": "勇敢的，华丽的",
            "bread$": "面包，生计",
            "break$": "打破，中断",
            "breakfast$": "早餐",
            "breast$": "胸部，乳房",
            "breath$": "呼吸，气息",
            "breathe$": "呼吸，流露",
            "breed$": "繁殖，品种",
            "breeze$": "微风，轻而易举的事",
            "brick$": "砖，砖块",
            "bride$": "新娘",
            "bridge$": "桥梁，桥牌",
            "brief$": "简短的，简介",
            "bright$": "明亮的，聪明的",
            "brilliant$": "灿烂的，杰出的",
            "bring$": "带来，引起",
            "broad$": "宽的，概括的",
            "broadcast$": "广播，播撒",
            "broken$": "破碎的，破产的",
            "brother$": "兄弟，同事",
            "brow$": "眉毛，坡顶",
            "brown$": "棕色的，褐色的",
            "brush$": "刷子，画笔",
            "bubble$": "气泡，泡沫",
            "bucket$": "桶，水桶",
            "budget$": "预算，便宜的",
            "build$": "建造，建立",
            "building$": "建筑物，建筑",
            "bulb$": "灯泡，球茎",
            "bulk$": "大量，大部分",
            "bull$": "公牛，雄性的",
            "bullet$": "子弹",
            "bunch$": "束，群",
            "bundle$": "捆，束",
            "burden$": "负担，责任",
            "bureau$": "局，办事处",
            "burn$": "烧，烧伤",
            "burst$": "破裂，爆发",
            "bury$": "埋葬，专心致志于",
            "bus$": "公共汽车",
            "bush$": "灌木丛",
            "business$": "商业，事务",
            "busy$": "忙的，正在使用的",
            "but$": "但是，而是",
            "butter$": "黄油，奉承",
            "button$": "按钮，纽扣",
            "buy$": "买",
            "by$": "被，经过",
            "bye$": "再见"
        }

        # 检查匹配的模式
        for pattern, definition in common_patterns.items():
            if word.lower().endswith(pattern.rstrip('$')):
                return definition

        # 如果没有匹配的模式，尝试从词根推断
        if word.startswith('ab'):
            return "与...分离的，离开的"
        elif word.startswith('ac'):
            return "朝向...的，增加的"
        elif word.startswith('ad'):
            return "向...的，添加的"
        elif word.startswith('un'):
            return "不，非，相反的"
        elif word.startswith('re'):
            return "再，重新，回来"
        elif word.startswith('dis'):
            return "不，分离，相反的"
        elif word.startswith('mis'):
            return "错误的，不好的"
        elif word.startswith('pre'):
            return "在...之前，预先"
        elif word.startswith('post'):
            return "在...之后，后来的"
        elif word.startswith('fore'):
            return "前，先，预先"
        elif word.endswith('able'):
            return "能够...的，可以...的"
        elif word.endswith('ible'):
            return "能够...的，可以...的"
        elif word.endswith('ful'):
            return "充满...的，有...性质的"
        elif word.endswith('less'):
            return "没有...的，不...的"
        elif word.endswith('ment'):
            return "...的行为或状态"
        elif word.endswith('tion'):
            return "...的行为或过程"
        elif word.endswith('sion'):
            return "...的行为或状态"
        elif word.endswith('ness'):
            return "...的性质或状态"
        elif word.endswith('ity'):
            return "...的性质或状态"
        elif word.endswith('ize'):
            return "使...化，变成..."
        elif word.endswith('ism'):
            return "...主义，学说"
        elif word.endswith('ist'):
            return "...主义者，从事...的人"
        elif word.endswith('or'):
            return "...的人，...物"
        elif word.endswith('er'):
            return "...的人，从事...的人"
        elif word.endswith('ary'):
            return "...的，与...有关的"
        elif word.endswith('ic'):
            return "...的，与...有关的"
        elif word.endswith('al'):
            return "...的，与...有关的"
        elif word.endswith('ous'):
            return "充满...的，多...的"
        elif word.endswith('ive'):
            return "有...倾向的，...性的"
        elif word.endswith('ly'):
            return "...地，以...方式"
        elif word.endswith('ward'):
            return "向...的，朝...方向的"
        elif word.endswith('wise'):
            return "在...方面，关于...地"
        else:
            # 完全无法推测的词，给出一个通用的说明
            return "拼写或发音相近的词"

    def _format_tags_text(self, card: WordCard) -> str:
        """格式化标签"""
        tags = []

        # 清理词性标签
        pos_tag = card.part_of_speech.replace('.', '').replace(',', '').replace(' ', '')
        if pos_tag:
            tags.append(pos_tag.lower())

        # 添加记忆技巧类型标签（如果存在）
        if card.memory_tip.type:
            tip_tag = card.memory_tip.type.replace(' ', '_').replace(',', '').replace('.', '')
            if tip_tag:
                tags.append(tip_tag.lower())

        return " ".join(tags)

    def _get_note_tags(self, card: WordCard) -> List[str]:
        """获取笔记标签"""
        tags = ["english", "vocabulary"]

        # 清理词性标签，移除空格和逗号
        pos_tag = card.part_of_speech.replace('.', '').replace(',', '').replace(' ', '')
        if pos_tag:
            tags.append(pos_tag.lower())

        # 添加记忆技巧类型标签（如果存在）
        if card.memory_tip.type:
            tip_tag = card.memory_tip.type.replace(' ', '_').replace(',', '').replace('.', '')
            if tip_tag:
                tags.append(tip_tag.lower())

        return tags

    def validate_apkg_file(self, file_path: str) -> bool:
        """验证APKG文件是否有效"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # 检查是否包含必要的文件
                file_list = zip_file.namelist()
                required_files = ['media', 'cards.tsv', 'notes.tsv', 'decks.tsv']
                return any(required_file in file_list for required_file in required_files)
        except:
            return False

    def get_import_instructions(self) -> str:
        """获取Anki导入说明"""
        return """
Anki APKG文件导入说明：

1. 直接导入APKG文件：
   - 打开Anki
   - 选择"文件" > "导入..."
   - 选择生成的.apkg文件
   - 牌组将自动导入

2. 使用CSV文件导入：
   - 打开Anki
   - 选择"文件" > "导入..."
   - 选择生成的CSV文件
   - 按提示选择字段映射
   - 确保选择"启用HTML"

3. 字段说明：
   - Front: 卡片正面（单词）
   - Back: 卡片背面（详细信息）
   - Phonetic: 音标
   - Part of Speech: 词性
   - Meaning: 释义
   - Memory Tip: 记忆技巧
   - Examples: 例句
   - Synonyms: 同义词
   - Confusables: 易混淆词
   - Tags: 标签

注意：导入时请确保字符编码为UTF-8。
        """

    def preview_deck_info(self, cards: List[WordCard]) -> Dict[str, Any]:
        """预览牌组信息"""
        if not cards:
            return {"error": "没有可预览的卡片"}

        # 统计词性分布
        pos_stats = {}
        for card in cards:
            pos = card.part_of_speech
            pos_stats[pos] = pos_stats.get(pos, 0) + 1

        # 统计记忆技巧分布
        tip_stats = {}
        for card in cards:
            tip_type = card.memory_tip.type
            tip_stats[tip_type] = tip_stats.get(tip_type, 0) + 1

        return {
            "deck_name": self.settings.deck_name,
            "total_cards": len(cards),
            "part_of_speech_distribution": pos_stats,
            "memory_tip_distribution": tip_stats,
            "sample_words": [card.word for card in cards[:5]],
            "file_size_estimate": len(cards) * 1024  # 估算文件大小
        }