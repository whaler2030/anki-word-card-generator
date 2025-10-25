"""
简化的音频生成模块 - 使用系统本地TTS或离线方案
"""

import os
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
from utils.logger import get_logger

logger = get_logger(__name__)

class SimpleAudioGenerator:
    """简化的音频生成器"""

    def __init__(self, audio_settings: Dict = None):
        self.settings = audio_settings or {}
        self.voice_language = self.settings.get('voice_language', 'en')
        self.voice_gender = self.settings.get('voice_gender', 'female')
        self.temp_dir = Path('temp/audio')
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate_word_audio(self, word: str, output_path: str = None) -> Optional[str]:
        """生成单词发音音频文件"""
        try:
            if output_path is None:
                # 使用简单、一致的文件名格式
                output_path = self.temp_dir / f"word_{word.lower()}.mp3"

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"正在生成单词发音: {word}")

            # 尝试不同的生成方法
            result = self._try_generate_methods(word, output_path)

            if result:
                # 检查是否生成了AIFF格式的文件
                aiff_path = output_path.with_suffix('.aiff')
                if aiff_path.exists():
                    logger.info(f"音频生成成功（AIFF格式）: {aiff_path}")
                    return str(aiff_path)
                elif output_path.exists():
                    logger.info(f"音频生成成功（MP3格式）: {output_path}")
                    return str(output_path)
                else:
                    logger.warning(f"音频生成方法返回True但找不到文件: {word}")
                    return None
            else:
                logger.warning(f"所有音频生成方法都失败了: {word}")
                return None

        except Exception as e:
            logger.error(f"生成单词发音失败: {word}, 错误: {e}")
            return None

    def _try_generate_methods(self, word: str, output_path: Path) -> bool:
        """尝试不同的音频生成方法"""
        methods = [
            self._generate_with_say,
            self._generate_with_pyttsx3,
            self._generate_with_gtts_fallback
        ]

        for method in methods:
            try:
                if method(word, output_path):
                    return True
            except Exception as e:
                logger.warning(f"方法 {method.__name__} 失败: {e}")
                continue

        return False

    def _generate_with_say(self, word: str, output_path: Path) -> bool:
        """使用macOS say命令生成音频"""
        try:
            # macOS系统内置say命令
            temp_aiff = output_path.with_suffix('.aiff')
            cmd = ['say', '-v', self._get_voice_name(), '-o', str(temp_aiff), word]

            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0 and temp_aiff.exists():
                # 尝试转换为MP3格式
                if self._convert_to_mp3(temp_aiff, output_path):
                    temp_aiff.unlink()  # 删除临时AIFF文件
                    logger.info(f"成功生成MP3音频: {output_path}")
                    return True
                else:
                    # 如果ffmpeg转换失败，保留AIFF格式但改为.aiff扩展名
                    final_path = output_path.with_suffix('.aiff')
                    if temp_aiff.rename(final_path):
                        logger.warning(f"无法转换为MP3，使用AIFF格式: {final_path}")
                        # 返回True，但文件格式是AIFF
                        return True
                    return False

            return False

        except Exception as e:
            logger.debug(f"say命令不可用: {e}")
            return False

    def _generate_with_pyttsx3(self, word: str, output_path: Path) -> bool:
        """使用pyttsx3库生成音频"""
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            voices = engine.getProperty('voices')

            # 选择合适的语音
            selected_voice = None
            for voice in voices:
                if self.voice_language in voice.languages or 'en' in voice.languages:
                    if self.voice_gender.lower() in voice.gender.lower():
                        selected_voice = voice.id
                        break

            if selected_voice:
                engine.setProperty('voice', selected_voice)

            # 保存音频文件
            engine.save_to_file(word, str(output_path))
            engine.runAndWait()

            if output_path.exists() and output_path.stat().st_size > 0:
                return True

            return False

        except ImportError:
            logger.debug("pyttsx3库未安装")
            return False
        except Exception as e:
            logger.debug(f"pyttsx3生成失败: {e}")
            return False

    def _generate_with_gtts_fallback(self, word: str, output_path: Path) -> bool:
        """使用gTTS作为最后备选"""
        try:
            from gtts import gTTS

            # 设置更长的超时
            tts = gTTS(text=word, lang=self.voice_language, slow=False)
            tts.save(str(output_path))

            if output_path.exists() and output_path.stat().st_size > 0:
                return True

            return False

        except Exception as e:
            logger.debug(f"gTTS备选方案失败: {e}")
            return False

    def _get_voice_name(self) -> str:
        """获取系统语音名称"""
        # macOS英语语音
        if self.voice_language == 'en':
            if self.voice_gender == 'male':
                return 'Alex'
            else:
                return 'Samantha'
        elif self.voice_language == 'zh':
            if self.voice_gender == 'male':
                return 'Daniel'
            else:
                return 'Tingting'
        else:
            return 'Alex'  # 默认

    def _convert_to_mp3(self, input_path: Path, output_path: Path) -> bool:
        """使用ffmpeg转换为MP3格式"""
        try:
            cmd = ['ffmpeg', '-i', str(input_path), '-acodec', 'libmp3lame', '-ab', '64k', str(output_path)]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0:
                logger.info(f"成功转换为MP3: {output_path}")
                return True
            else:
                logger.debug(f"ffmpeg转换失败，错误码: {result.returncode}")
                return False
        except FileNotFoundError:
            logger.debug("ffmpeg未找到，跳过转换")
            return False
        except Exception as e:
            logger.debug(f"ffmpeg转换失败: {e}")
            return False

    def generate_example_audio(self, example: str, output_path: str = None) -> Optional[str]:
        """生成例句发音音频文件"""
        try:
            if output_path is None:
                # 使用简单、一致的文件名格式（取前10个字符作为hash）
                example_hash = abs(hash(example)) % 10000
                output_path = self.temp_dir / f"example_{example_hash}.mp3"

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"正在生成例句发音")

            # 使用与单词相同的方法
            if self._try_generate_methods(example, output_path):
                logger.info(f"例句发音生成成功: {output_path}")
                return str(output_path)
            else:
                logger.warning("例句发音生成失败")
                return None

        except Exception as e:
            logger.error(f"生成例句发音失败: {e}")
            return None

    def cleanup_temp_files(self):
        """清理临时音频文件"""
        try:
            for file_path in self.temp_dir.glob("*.mp3"):
                file_path.unlink()
            for file_path in self.temp_dir.glob("*.aiff"):
                file_path.unlink()
            logger.info("临时音频文件清理完成")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

    def validate_audio_file(self, audio_path: str) -> bool:
        """验证音频文件是否有效"""
        try:
            path = Path(audio_path)
            return path.exists() and path.stat().st_size > 0
        except:
            return False