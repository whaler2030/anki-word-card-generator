"""
音频生成模块
"""

import os
import time
from pathlib import Path
from typing import Optional, Dict, List
from gtts import gTTS
import requests
from utils.logger import get_logger

logger = get_logger(__name__)

class AudioGenerator:
    """音频生成器"""

    def __init__(self, audio_settings: Dict = None):
        self.settings = audio_settings or {}
        self.tts_engine = self.settings.get('tts_engine', 'gtts')  # gtts, edge
        self.voice_language = self.settings.get('voice_language', 'en')
        self.voice_gender = self.settings.get('voice_gender', 'female')
        self.temp_dir = Path('temp/audio')
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate_word_audio(self, word: str, output_path: str = None) -> Optional[str]:
        """生成单词发音音频文件"""
        try:
            if output_path is None:
                timestamp = int(time.time() * 1000)
                output_path = self.temp_dir / f"{word}_{timestamp}.mp3"

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"正在生成单词发音: {word}")

            if self.tts_engine == 'gtts':
                return self._generate_with_gtts(word, output_path)
            elif self.tts_engine == 'edge':
                return self._generate_with_edge(word, output_path)
            else:
                raise ValueError(f"不支持的TTS引擎: {self.tts_engine}")

        except Exception as e:
            logger.error(f"生成单词发音失败: {word}, 错误: {e}")
            # 返回None而不是抛出异常，让调用者处理
            return None

    def _generate_with_gtts(self, word: str, output_path: Path) -> str:
        """使用gTTS生成音频"""
        try:
            # 检查系统代理设置
            proxy_settings = self._get_proxy_settings()

            # 创建TTS对象，设置更长的超时
            tts = gTTS(text=word, lang=self.voice_language, slow=False)

            # 设置代理（如果配置了）
            if proxy_settings:
                logger.info(f"使用代理设置: {proxy_settings}")
                os.environ['HTTP_PROXY'] = proxy_settings.get('http', '')
                os.environ['HTTPS_PROXY'] = proxy_settings.get('https', '')

            # 生成音频文件
            tts.save(str(output_path))

            # 验证文件是否创建成功
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"gTTS音频生成成功: {output_path}")
                return str(output_path)
            else:
                raise RuntimeError("音频文件生成失败")

        except Exception as e:
            logger.error(f"gTTS音频生成失败: {e}")
            raise RuntimeError(f"gTTS音频生成失败: {e}")

    def _get_proxy_settings(self) -> Optional[Dict[str, str]]:
        """获取系统代理设置"""
        proxy_settings = {}

        # 检查环境变量
        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')

        if http_proxy:
            proxy_settings['http'] = http_proxy
        if https_proxy:
            proxy_settings['https'] = https_proxy

        return proxy_settings if proxy_settings else None

    def _generate_with_edge(self, word: str, output_path: Path) -> str:
        """使用Edge TTS生成音频"""
        try:
            # Edge TTS API端点（使用实际可用的API）
            url = "https://edge-tts.vercel.app/api/tts"

            # 构建请求数据
            data = {
                "text": word,
                "voice": f"{self.voice_language}-{self.voice_gender}",
                "rate": "0%",
                "volume": "0%"
            }

            # 获取代理设置
            proxies = None
            proxy_settings = self._get_proxy_settings()
            if proxy_settings:
                proxies = {
                    'http': proxy_settings.get('http'),
                    'https': proxy_settings.get('https')
                }
                logger.info(f"Edge TTS使用代理: {proxies}")

            # 发送请求
            response = requests.post(url, json=data, timeout=30, proxies=proxies)
            response.raise_for_status()

            # 保存音频文件
            with open(output_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Edge TTS音频生成成功: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Edge TTS音频生成失败: {e}")
            # 如果Edge失败，回退到gTTS
            logger.info("回退到gTTS引擎")
            return self._generate_with_gtts(word, output_path)

    def generate_example_audio(self, example: str, output_path: str = None) -> Optional[str]:
        """生成例句发音音频文件"""
        try:
            if output_path is None:
                timestamp = int(time.time() * 1000)
                output_path = self.temp_dir / f"example_{timestamp}.mp3"

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"正在生成例句发音")

            # 例句可能较长，使用较慢的语速
            tts = gTTS(text=example, lang=self.voice_language, slow=False)
            tts.save(str(output_path))

            logger.info(f"例句发音生成成功: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"生成例句发音失败: {e}")
            # 返回None而不是抛出异常，让调用者处理
            return None

    def batch_generate_audio(self, words: List[str], examples: List[str] = None) -> Dict[str, str]:
        """批量生成音频文件"""
        results = {}

        logger.info(f"开始批量生成音频: {len(words)} 个单词")

        # 生成单词发音
        for word in words:
            try:
                audio_path = self.generate_word_audio(word)
                results[f"word_{word}"] = audio_path
            except Exception as e:
                logger.warning(f"生成单词发音失败: {word}, 错误: {e}")
                results[f"word_{word}"] = None

        # 生成例句发音
        if examples:
            for i, example in enumerate(examples):
                try:
                    audio_path = self.generate_example_audio(example)
                    results[f"example_{i}"] = audio_path
                except Exception as e:
                    logger.warning(f"生成例句发音失败: {example[:30]}..., 错误: {e}")
                    results[f"example_{i}"] = None

        logger.info(f"批量音频生成完成: {len([r for r in results.values() if r])} 个成功")
        return results

    def cleanup_temp_files(self):
        """清理临时音频文件"""
        try:
            for file_path in self.temp_dir.glob("*.mp3"):
                file_path.unlink()
            logger.info("临时音频文件清理完成")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

    def get_audio_info(self, audio_path: str) -> Dict:
        """获取音频文件信息"""
        try:
            path = Path(audio_path)
            if not path.exists():
                return {"error": "文件不存在"}

            stat = path.stat()
            return {
                "file_path": audio_path,
                "file_size": stat.st_size,
                "created_time": stat.st_ctime,
                "file_format": "mp3"
            }
        except Exception as e:
            logger.error(f"获取音频信息失败: {e}")
            return {"error": str(e)}

    def validate_audio_file(self, audio_path: str) -> bool:
        """验证音频文件是否有效"""
        try:
            path = Path(audio_path)
            return path.exists() and path.stat().st_size > 0
        except:
            return False