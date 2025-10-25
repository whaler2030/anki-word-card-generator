"""
在线音频生成模块 - 使用在线TTS服务，不占用本地存储
"""

import os
import time
from typing import Optional, Dict, List
from utils.logger import get_logger

logger = get_logger(__name__)

class OnlineAudioGenerator:
    """在线音频生成器"""

    def __init__(self, audio_settings: Dict = None):
        self.settings = audio_settings or {}
        self.voice_language = self.settings.get('voice_language', 'en')
        self.voice_gender = self.settings.get('voice_gender', 'female')
        self.tts_engine = self.settings.get('tts_engine', 'google')

    def generate_word_audio(self, word: str) -> Optional[str]:
        """生成单词发音的在线音频链接"""
        try:
            logger.info(f"正在生成单词发音链接: {word}")

            # 根据不同的TTS引擎生成在线链接
            audio_url = self._generate_audio_url(word)

            if audio_url:
                logger.info(f"音频链接生成成功: {word}")
                return audio_url
            else:
                logger.warning(f"音频链接生成失败: {word}")
                return None

        except Exception as e:
            logger.error(f"生成单词发音链接失败: {word}, 错误: {e}")
            return None

    def _generate_audio_url(self, word: str) -> Optional[str]:
        """生成可直接在Anki中播放的音频URL"""

        # 方案1: Oxford词典音频（最可靠）
        if self.tts_engine == 'oxford':
            return self._oxford_direct_audio_url(word)

        # 方案2: Merriam-Webster音频
        elif self.tts_engine == 'merriam':
            return self._merriam_audio_url(word)

        # 方案3: Cambridge词典音频
        elif self.tts_engine == 'cambridge':
            return self._cambridge_audio_url(word)

        # 方案4: 使用备用CDN音频
        elif self.tts_engine == 'cdn':
            return self._cdn_audio_url(word)

        # 方案5: 百度翻译TTS（在中国大陆访问稳定）
        elif self.tts_engine == 'baidu':
            return self._baidu_word_url(word)

        # 方案6: 有道翻译TTS（在中国大陆访问稳定）
        elif self.tts_engine == 'youdao':
            return self._youdao_word_url(word)

        # 默认使用Oxford词典音频
        return self._oxford_direct_audio_url(word)

    def _google_tts_direct_url(self, word: str) -> str:
        """生成可直接播放的Google TTS URL"""
        # Google翻译TTS API - 可直接播放
        lang = 'en' if self.voice_language == 'en' else 'zh-CN'
        return f"https://translate.google.com/translate_tts?ie=UTF-8&q={word}&tl={lang}&client=tw-ob&textlen={len(word)}"

    def _ttsfree_url(self, word: str) -> str:
        """生成TTSFree的URL"""
        # 使用TTSFree服务的MP3链接
        lang = 'en-us' if self.voice_language == 'en' else 'zh-cn'
        voice = 'female-voice' if self.voice_gender == 'female' else 'male-voice'
        return f"https://ttsfree.com/text-to-speech/{lang}/{voice}/{word}.mp3"

    def _oxford_direct_audio_url(self, word: str) -> str:
        """生成Oxford词典直接音频URL"""
        # Oxford词典的CDN音频源 - 最可靠
        return f"https://ssl.gstatic.com/dictionary/static/sounds/oxford/{word}--_gb_1.mp3"

    def _merriam_audio_url(self, word: str) -> str:
        """生成Merriam-Webster音频URL"""
        # Merriam-Webster词典音频
        return f"https://media.merriam-webster.com/audio/prons/en/us/mp3/{word}.mp3"

    def _cambridge_audio_url(self, word: str) -> str:
        """生成Cambridge词典音频URL"""
        # Cambridge词典音频
        return f"https://dictionary.cambridge.org/media/english/uk_pron/{word}.mp3"

    def _cdn_audio_url(self, word: str) -> str:
        """生成CDN音频URL"""
        # 备用CDN音频服务
        common_words = {
            'hello': 'https://file-examples.com/storage/fe8ccc35c638ec6b758cd1b683b2a2b3f/Hello.mp3',
            'world': 'https://file-examples.com/storage/fe8ccc35c638ec6b758cd1b683b2a2b3f/World.mp3',
            'test': 'https://file-examples.com/storage/fe8ccc35c638ec6b758cd1b683b2a2b3f/Test.mp3',
        }
        return common_words.get(word.lower(), self._oxford_direct_audio_url(word))

    def _naturalreaders_url(self, word: str) -> str:
        """生成NaturalReaders的URL"""
        lang = 'en' if self.voice_language == 'en' else 'zh'
        return f"https://www.naturalreaders.com/online/{lang}/{word}.mp3"

    def _google_tts_direct_url(self, word: str) -> str:
        """生成Google TTS URL（已不可用）"""
        # Google翻译TTS API - 现在不返回实际音频数据
        logger.warning("Google TTS现在不返回实际音频数据，建议使用Oxford引擎")
        return self._oxford_direct_audio_url(word)

    def _google_tts_url(self, word: str) -> str:
        """生成Google TTS URL（旧版，用于兼容性）"""
        lang = 'en' if self.voice_language == 'en' else 'zh-CN'
        return f"https://translate.google.com/translate_tts?ie=UTF-8&q={word}&tl={lang}&client=tw-ob"

    def _forvo_url(self, word: str) -> str:
        """生成Forvo发音URL"""
        lang = 'en' if self.voice_language == 'en' else 'zh'
        return f"https://forvo.com/word/{word}/#{lang}"

    def _oxford_url(self, word: str) -> str:
        """生成Oxford词典发音URL"""
        return f"https://www.oxfordlearnersdictionaries.com/definition/english/{word}"

    def generate_example_audio(self, example: str) -> Optional[str]:
        """生成例句发音的在线音频链接"""
        try:
            logger.info(f"正在生成例句发音链接")

            # 对于例句，使用Google TTS API（支持完整句子）
            audio_url = self._generate_sentence_audio_url(example)

            if audio_url:
                logger.info(f"例句发音链接生成成功")
                return audio_url
            else:
                logger.warning("例句发音链接生成失败")
                return None

        except Exception as e:
            logger.error(f"生成例句发音链接失败: {e}")
            return None

    def _generate_sentence_audio_url(self, sentence: str) -> Optional[str]:
        """生成句子发音的音频URL（使用支持句子的TTS服务）"""
        try:
            # 优先使用可直接播放的服务（Google TTS最适合例句）
            urls = [
                self._generate_google_tts_url(sentence),   # Google TTS：最适合例句
                self._generate_ttsfree_url(sentence),     # TTSFree：支持句子
                self._generate_azure_cognitive_url(sentence), # Azure：作为备选
                # 移除有道翻译例句（不支持长句子）
                # 移除NaturalReaders（需要重定向）
                # 移除百度翻译（需要下载）
            ]

            # 返回第一个可用的URL
            for url in urls:
                if url and self._test_audio_url(url):
                    return url

            # 如果主要服务都不可用，尝试最后选择
            backup_urls = [
                self._generate_baidu_url(sentence),      # 百度翻译：下载方式
            ]

            for url in backup_urls:
                if url and self._test_audio_url(url):
                    return url

            return urls[0] if urls else None

        except Exception as e:
            logger.error(f"生成句子音频URL失败: {e}")
            return None

    def _generate_google_tts_url(self, sentence: str) -> str:
        """生成Google TTS URL"""
        import urllib.parse
        import random

        encoded_sentence = urllib.parse.quote(sentence)
        lang = 'en' if self.voice_language == 'en' else 'zh-CN'

        # 添加随机参数避免缓存问题
        random_id = random.randint(1000, 9999)

        return f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_sentence}&tl={lang}&client=tw-ob&rand={random_id}"

    def _generate_ttsfree_url(self, sentence: str) -> str:
        """生成TTSFree URL"""
        import urllib.parse
        encoded_sentence = urllib.parse.quote(sentence)
        lang = 'en-us' if self.voice_language == 'en' else 'zh-cn'
        return f"https://ttsfree.com/text-to-speech/{lang}/female-voice/{encoded_sentence}.mp3"

    def _generate_naturalreaders_url(self, sentence: str) -> str:
        """生成NaturalReaders URL"""
        import urllib.parse
        encoded_sentence = urllib.parse.quote(sentence)
        lang = 'en' if self.voice_language == 'en' else 'zh'
        return f"https://www.naturalreaders.com/online/{lang}/{encoded_sentence}.mp3"

    def _generate_azure_cognitive_url(self, sentence: str) -> str:
        """生成Azure认知服务TTS URL（Azure CDN在中国大陆访问较快）"""
        import urllib.parse
        import random
        encoded_sentence = urllib.parse.quote(sentence)
        random_id = random.randint(1000, 9999)
        # Azure认知服务的免费TTS服务
        return f"https://eastus.tts.speech.microsoft.com/cognitiveservices/v1?text={encoded_sentence}&language=en-US&voice=en-US-JennyNeural&r={random_id}"

    def _generate_baidu_url(self, sentence: str) -> str:
        """生成百度翻译TTS URL（百度在中国大陆访问稳定）"""
        import urllib.parse
        encoded_sentence = urllib.parse.quote(sentence)
        lang = 'en' if self.voice_language == 'en' else 'zh'
        # 百度翻译的TTS服务
        return f"https://fanyi.baidu.com/gettts?lan={lang}&text={encoded_sentence}&spd=4&source=web"

    def _generate_youdao_url(self, sentence: str) -> str:
        """生成有道翻译TTS URL（有道在中国大陆访问稳定）"""
        import urllib.parse
        import random
        encoded_sentence = urllib.parse.quote(sentence)
        lang = 'en' if self.voice_language == 'en' else 'zh'
        random_id = random.randint(1000, 9999)
        # 有道翻译的TTS服务（支持句子）
        return f"https://dict.youdao.com/dictvoice?audio={encoded_sentence}&le={lang}&r={random_id}"

    def _baidu_word_url(self, word: str) -> str:
        """生成百度翻译单词TTS URL"""
        import urllib.parse
        import random
        encoded_word = urllib.parse.quote(word)
        lang = 'en' if self.voice_language == 'en' else 'zh'
        random_id = random.randint(1000, 9999)
        return f"https://fanyi.baidu.com/gettts?lan={lang}&text={encoded_word}&spd=3&source=web&r={random_id}"

    def _youdao_word_url(self, word: str) -> str:
        """生成有道翻译单词TTS URL"""
        import urllib.parse
        import random
        encoded_word = urllib.parse.quote(word)
        lang = 'en' if self.voice_language == 'en' else 'zh'
        random_id = random.randint(1000, 9999)
        return f"https://dict.youdao.com/dictvoice?audio={encoded_word}&le={lang}&r={random_id}"

    def _test_audio_url(self, url: str) -> bool:
        """测试音频URL是否可用"""
        try:
            import requests
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def _clean_text_for_url(self, text: str) -> str:
        """清理文本用于URL"""
        # 移除特殊字符，只保留字母、数字和空格
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # 替换空格为URL编码
        cleaned = cleaned.replace(' ', '%20')
        return cleaned

    def cleanup_temp_files(self):
        """在线音频生成器无需清理临时文件"""
        logger.info("在线音频生成器：无需清理临时文件")

    def validate_audio_file(self, audio_path: str) -> bool:
        """在线音频生成器：总是返回True，因为不需要本地文件"""
        return True

    def get_audio_embed_html(self, word: str) -> str:
        """获取音频嵌入HTML代码"""
        audio_url = self.generate_word_audio(word)
        if audio_url:
            return f'''
            <div class="audio-player">
                <audio controls style="width: 200px; height: 30px;">
                    <source src="{audio_url}" type="audio/mpeg">
                    <source src="{audio_url}" type="audio/wav">
                    <a href="{audio_url}">下载音频</a>
                </audio>
            </div>
            '''
        return ""

    def get_audio_link_html(self, word: str) -> str:
        """获取音频链接HTML代码"""
        audio_url = self.generate_word_audio(word)
        if audio_url:
            return f'''
            <div class="audio-container">
                <a href="{audio_url}" target="_blank" class="audio-link">
                    🔊 发音 {word}
                </a>
                <audio src="{audio_url}" style="display: none;"></audio>
            </div>
            '''
        return ""

    def get_google_translate_embed(self, word: str) -> str:
        """获取Google翻译嵌入代码"""
        return f'''
        <div class="google-translate-container">
            <iframe
                src="https://translate.google.com/translate_tts?ie=UTF-8&q={word}&tl=en&client=tw-ob"
                style="display: none;"
                onload="this.style.display='block'; this.height='60px'; this.width='300px';">
            </iframe>
        </div>
        '''