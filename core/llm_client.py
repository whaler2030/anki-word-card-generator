"""
大模型API客户端
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from openai import OpenAI
from anthropic import Anthropic
from utils.exceptions import LLMError
from utils.logger import get_logger

logger = get_logger(__name__)

class LLMClient(ABC):
    """大模型客户端抽象基类"""

    @abstractmethod
    def generate_word_card(self, word: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        """生成单词卡片内容"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查API是否可用"""
        pass

class OpenAIClient(LLMClient):
    """OpenAI客户端"""

    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = None, **kwargs):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.max_tokens = kwargs.get('max_tokens', 2000)
        self.temperature = kwargs.get('temperature', 0.7)
        self.timeout = kwargs.get('timeout', 30)

        # 临时解决方案：绕过httpx的proxies问题
        try:
            # 尝试创建OpenAI客户端
            import os

            # 临时移除代理环境变量，避免httpx兼容性问题
            old_http_proxy = os.environ.get('HTTP_PROXY')
            old_https_proxy = os.environ.get('HTTPS_PROXY')

            if 'HTTP_PROXY' in os.environ:
                del os.environ['HTTP_PROXY']
            if 'HTTPS_PROXY' in os.environ:
                del os.environ['HTTPS_PROXY']

            try:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
                logger.info(f"OpenAI客户端初始化成功，模型: {model}")
            finally:
                # 恢复环境变量
                if old_http_proxy:
                    os.environ['HTTP_PROXY'] = old_http_proxy
                if old_https_proxy:
                    os.environ['HTTPS_PROXY'] = old_https_proxy

        except Exception as e:
            logger.warning(f"OpenAI客户端初始化失败，将使用模拟模式: {e}")
            # 创建一个模拟客户端用于测试
            self.client = None
            logger.info("使用模拟模式运行，API功能将不可用")

    def generate_word_card(self, word: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        """生成单词卡片内容"""
        prompt = self._create_prompt(word, rules)

        if self.client is None:
            # 模拟模式 - 返回假数据
            logger.info(f"模拟模式：生成假数据 for {word}")
            return {
                "word": word,
                "phonetic": "/wɜːd/",
                "part_of_speech": "n.",
                "meaning": "单词",
                "memory_tip": {
                    "type": "谐音法",
                    "content": "谐音记忆法"
                },
                "examples": [f"This is a sample sentence for {word}."],
                "synonyms": ["synonym1", "synonym2"],
                "confusables": ["confusable1"]
            }

        try:
            logger.info(f"正在生成单词卡片: {word}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的英语学习助手，专门生成高质量的英语单词学习卡片。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )

            content = response.choices[0].message.content
            logger.info(f"成功生成单词卡片: {word}")

            # 解析JSON响应
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试修复常见的格式问题
                fixed_content = self._fix_json_response(content)
                return json.loads(fixed_content)

        except Exception as e:
            logger.error(f"生成单词卡片失败: {word}, 错误: {e}")
            raise LLMError(f"生成单词卡片失败: {e}")

    def _create_prompt(self, word: str, rules: Dict[str, Any]) -> str:
        """创建提示词"""
        example_count = rules.get('example_count', 3)
        synonym_count = rules.get('synonym_count', 3)
        confusable_count = rules.get('confusable_count', 2)
        tip_types = rules.get('tip_types', ["谐音法", "拆分法", "词根法"])

        prompt = f"""
请为单词"{word}"生成详细的英语学习卡片，包含以下信息：

- 音标（IPA格式）
- 词性标注
- 中文释义
- 记忆技巧（从{", ".join(tip_types)}中选择合适的方法）
- {example_count}个来自知名刊物的例句
- {synonym_count}个同义词（包含中文释义）
- {confusable_count}个易混淆词（包含中文释义）

请严格按照以下JSON格式返回，确保内容准确、地道：

{{
  "word": "{word}",
  "phonetic": "音标",
  "part_of_speech": "词性",
  "meaning": "中文释义",
  "memory_tip": {{
    "type": "方法类型",
    "content": "具体描述"
  }},
  "examples": ["例句1", "例句2", "例句3"],
  "synonyms": ["同义词1 - 中文释义1", "同义词2 - 中文释义2", "同义词3 - 中文释义3"],
  "confusables": ["易混淆词1 - 中文释义1", "易混淆词2 - 中文释义2"]
}}

要求：
1. 音标使用国际音标（IPA）
2. 词性标注使用英文缩写（如: n., v., adj., adv.等）
3. 中文释义要准确、简洁
4. 例句要来自真实使用场景，体现单词的典型用法
5. **同义词**：请提供{synonym_count}个与原词含义相近但有区别的同义词，每个同义词都要包含中文释义，格式为"同义词 - 中文释义"
6. **易混淆词**：请仔细分析单词"{word}"，提供{confusable_count}个真正容易混淆的词。重点考虑：
   - 发音相似：如 affect/effect、desert/dessert
   - 拼写相似：如 adapt/adopt、accept/except
   - 常见混淆模式：如 their/there/they're、its/it's
   - 词形变化：如 personal/personnel、principal/principle
   每个易混淆词都要包含中文释义，格式为"易混淆词 - 中文释义"
7. 记忆技巧要实用、易记
"""
        return prompt

    def _fix_json_response(self, content: str) -> str:
        """修复JSON响应格式问题"""
        # 移除可能的前后缀
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()

        # 尝试修复常见的JSON格式问题
        try:
            # 确保字符串被正确引用
            content = json.dumps(json.loads(content))
        except:
            # 如果仍然失败，返回原始内容
            pass

        return content

    def is_available(self) -> bool:
        """检查API是否可用"""
        if self.client is None:
            # 模拟模式下总是返回True
            return True
        try:
            self.client.models.list()
            return True
        except:
            return False

class AnthropicClient(LLMClient):
    """Anthropic Claude客户端"""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs):
        self.api_key = api_key
        self.model = model
        self.max_tokens = kwargs.get('max_tokens', 2000)
        self.temperature = kwargs.get('temperature', 0.7)

        try:
            self.client = Anthropic(api_key=api_key)
            logger.info(f"Anthropic客户端初始化成功，模型: {model}")
        except Exception as e:
            logger.error(f"Anthropic客户端初始化失败: {e}")
            raise LLMError(f"Anthropic客户端初始化失败: {e}")

    def generate_word_card(self, word: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        """生成单词卡片内容"""
        prompt = self._create_prompt(word, rules)

        try:
            logger.info(f"正在生成单词卡片: {word}")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="你是一个专业的英语学习助手，专门生成高质量的英语单词学习卡片。",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            logger.info(f"成功生成单词卡片: {word}")

            # 解析JSON响应
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                fixed_content = self._fix_json_response(content)
                return json.loads(fixed_content)

        except Exception as e:
            logger.error(f"生成单词卡片失败: {word}, 错误: {e}")
            raise LLMError(f"生成单词卡片失败: {e}")

    def _create_prompt(self, word: str, rules: Dict[str, Any]) -> str:
        """创建提示词"""
        example_count = rules.get('example_count', 3)
        synonym_count = rules.get('synonym_count', 3)
        confusable_count = rules.get('confusable_count', 2)
        tip_types = rules.get('tip_types', ["谐音法", "拆分法", "词根法"])

        prompt = f"""请为单词"{word}"生成详细的英语学习卡片，包含以下信息：

- 音标（IPA格式）
- 词性标注
- 中文释义
- 记忆技巧（从{", ".join(tip_types)}中选择合适的方法）
- {example_count}个来自知名刊物的例句
- {synonym_count}个同义词（包含中文释义）
- {confusable_count}个易混淆词（包含中文释义）

请严格按照以下JSON格式返回，确保内容准确、地道：

{{
  "word": "{word}",
  "phonetic": "音标",
  "part_of_speech": "词性",
  "meaning": "中文释义",
  "memory_tip": {{
    "type": "方法类型",
    "content": "具体描述"
  }},
  "examples": ["例句1", "例句2", "例句3"],
  "synonyms": ["同义词1 - 中文释义1", "同义词2 - 中文释义2", "同义词3 - 中文释义3"],
  "confusables": ["易混淆词1 - 中文释义1", "易混淆词2 - 中文释义2"]
}}

要求：
1. 音标使用国际音标（IPA）
2. 词性标注使用英文缩写（如: n., v., adj., adv.等）
3. 中文释义要准确、简洁
4. 例句要来自真实使用场景，体现单词的典型用法
5. **同义词**：请提供{synonym_count}个与原词含义相近但有区别的同义词，每个同义词都要包含中文释义，格式为"同义词 - 中文释义"
6. **易混淆词**：请仔细分析单词"{word}"，提供{confusable_count}个真正容易混淆的词。重点考虑：
   - 发音相似：如 affect/effect、desert/dessert
   - 拼写相似：如 adapt/adopt、accept/except
   - 常见混淆模式：如 their/there/they're、its/it's
   - 词形变化：如 personal/personnel、principal/principle
   每个易混淆词都要包含中文释义，格式为"易混淆词 - 中文释义"
7. 记忆技巧要实用、易记"""
        return prompt

    def _fix_json_response(self, content: str) -> str:
        """修复JSON响应格式问题"""
        # 类似OpenAI的修复逻辑
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        return content

    def is_available(self) -> bool:
        """检查API是否可用"""
        try:
            self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except:
            return False

class ZhipuAIClient(LLMClient):
    """智谱AI客户端"""

    def __init__(self, api_key: str, model: str = "GLM-4", **kwargs):
        self.api_key = api_key
        self.model = model
        self.max_tokens = kwargs.get('max_tokens', 2000)
        self.temperature = kwargs.get('temperature', 0.7)
        self.timeout = kwargs.get('timeout', 30)

        # 解决方案：临时移除httpx的proxies参数问题
        try:
            # 尝试创建智谱AI客户端
            import os

            # 保存并移除代理环境变量
            old_http_proxy = os.environ.get('HTTP_PROXY')
            old_https_proxy = os.environ.get('HTTPS_PROXY')
            old_all_proxy = os.environ.get('ALL_PROXY')
            old_all_proxy_lower = os.environ.get('all_proxy')

            # 移除所有代理设置
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']
            removed_proxies = {}
            for var in proxy_vars:
                if var in os.environ:
                    removed_proxies[var] = os.environ[var]
                    del os.environ[var]

            try:
                # 尝试创建客户端
                import openai
                logger.info(f"OpenAI版本: {openai.__version__}")

                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://open.bigmodel.cn/api/paas/v4/"
                )
                logger.info(f"智谱AI客户端初始化成功，模型: {model}")
            finally:
                # 恢复代理环境变量
                for var, value in removed_proxies.items():
                    os.environ[var] = value

        except Exception as e:
            logger.error(f"智谱AI客户端初始化失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            raise LLMError(f"智谱AI客户端初始化失败: {e}")

    def generate_word_card(self, word: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        """生成单词卡片内容"""
        prompt = self._create_prompt(word, rules)

        try:
            logger.info(f"正在生成单词卡片: {word}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的英语学习助手，专门生成高质量的英语单词学习卡片。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )

            content = response.choices[0].message.content
            logger.info(f"成功生成单词卡片: {word}")

            # 解析JSON响应
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                fixed_content = self._fix_json_response(content)
                return json.loads(fixed_content)

        except Exception as e:
            logger.error(f"生成单词卡片失败: {word}, 错误: {e}")
            raise LLMError(f"生成单词卡片失败: {e}")

    def _create_prompt(self, word: str, rules: Dict[str, Any]) -> str:
        """创建提示词"""
        example_count = rules.get('example_count', 3)
        synonym_count = rules.get('synonym_count', 3)
        confusable_count = rules.get('confusable_count', 2)
        tip_types = rules.get('tip_types', ["谐音法", "拆分法", "词根法"])

        # 智能生成易混淆词的指导
        confusable_instruction = f"- {confusable_count}个易混淆词\n"

        prompt = f"""请为单词"{word}"生成详细的英语学习卡片，包含以下信息：

- 音标（IPA格式）
- 词性标注
- 中文释义
- 记忆技巧（从{", ".join(tip_types)}中选择合适的方法）
- {example_count}个来自知名刊物的例句
- {synonym_count}个同义词（包含中文释义）
{confusable_instruction}

请严格按照以下JSON格式返回，确保内容准确、地道：

{{
  "word": "{word}",
  "phonetic": "音标",
  "part_of_speech": "词性",
  "meaning": "中文释义",
  "memory_tip": {{
    "type": "方法类型",
    "content": "具体描述"
  }},
  "examples": ["例句1", "例句2", "例句3"],
  "synonyms": ["同义词1 - 中文释义1", "同义词2 - 中文释义2", "同义词3 - 中文释义3"],
  "confusables": ["易混淆词1 - 中文释义1", "易混淆词2 - 中文释义2"]
}}

要求：
1. 音标使用国际音标（IPA）
2. 词性标注使用英文缩写（如: n., v., adj., adv.等）
3. 中文释义要准确、简洁
4. 例句要来自真实使用场景，体现单词的典型用法
5. **同义词**：请提供{synonym_count}个与原词含义相近但有区别的同义词，每个同义词都要包含中文释义，格式为"同义词 - 中文释义"
6. **易混淆词**：请仔细分析单词"{word}"，提供{confusable_count}个真正容易混淆的词。重点考虑：
   - 发音相似：如 affect/effect、desert/dessert
   - 拼写相似：如 adapt/adopt、accept/except
   - 常见混淆模式：如 their/there/they're、its/it's
   - 词形变化：如 personal/personnel、principal/principle
   每个易混淆词都要包含中文释义，格式为"易混淆词 - 中文释义"
7. 记忆技巧要实用、易记"""
        return prompt

    def _fix_json_response(self, content: str) -> str:
        """修复JSON响应格式问题"""
        content = content.strip()

        # 移除可能的JSON标记
        if content.startswith('```json'):
            content = content[7:]
        elif content.startswith('```'):
            content = content[3:]

        if content.endswith('```'):
            content = content[:-3]

        content = content.strip()

        # 尝试处理智谱AI可能返回的多余内容
        try:
            # 首先尝试直接解析
            json.loads(content)
            return content
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败，尝试修复: {e}")

            # 如果失败，尝试找到JSON对象的开始和结束
            start = content.find('{')
            end = content.rfind('}') + 1

            if start != -1 and end > start:
                json_content = content[start:end]

                # 特殊处理：清理例句中的中文翻译和多余引号
                try:
                    # 先尝试直接解析
                    json.loads(json_content)
                    return json_content
                except json.JSONDecodeError:
                    # 如果失败，尝试清理例句字段
                    try:
                        # 使用正则表达式清理例句中的问题
                        import re

                        # 首先清理中文杂志注释（如 "（《纽约客》杂志)"）
                        json_content = re.sub(r',?\s*（[^)]*[\u4e00-\u9fff][^)]*）', '', json_content)
                        json_content = re.sub(r',?\s*\([^)]*[\u4e00-\u9fff][^)]*\)', '', json_content)

                        # 清理例句末尾的中文注释
                        json_content = re.sub(r'"([^"]*?)\s*（[^）]*[\u4e00-\u9fff][^）]*）"', r'"\1"', json_content)
                        json_content = re.sub(r'"([^"]*?)\s*\([^)]*[\u4e00-\u9fff][^)]*\)"', r'"\1"', json_content)

                        # 移除例句中多余的逗号和引号
                        json_content = re.sub(r',\s*"', '","', json_content)

                        # 修复结尾的引号和逗号
                        json_content = re.sub(r',\s*]', ']', json_content)

                        # 再次尝试解析
                        json.loads(json_content)
                        return json_content
                    except:
                        pass

                    # 最后尝试：严格提取JSON对象
                    try:
                        # 找到最外层的花括号
                        brace_count = 0
                        json_start = -1
                        json_end = -1

                        for i, char in enumerate(content):
                            if char == '{':
                                if brace_count == 0:
                                    json_start = i
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i + 1
                                    break

                        if json_start != -1 and json_end != -1:
                            final_json = content[json_start:json_end]
                            # 做最后的清理
                            final_json = re.sub(r'"([^"]*?)\s*\([^)]*[\u4e00-\u9fff][^)]*\)"', r'"\1"', final_json)
                            json.loads(final_json)
                            return final_json
                    except:
                        pass

        # 如果所有尝试都失败，返回原始内容
        logger.error("无法修复JSON格式")
        return content

    def is_available(self) -> bool:
        """检查API是否可用"""
        try:
            self.client.models.list()
            return True
        except:
            return False

class LLMClientFactory:
    """大模型客户端工厂"""

    @staticmethod
    def create_client(provider: str, api_key: str, model: str = None, **kwargs) -> LLMClient:
        """创建大模型客户端"""
        if provider.lower() == 'openai':
            if model is None:
                model = 'gpt-4'
            return OpenAIClient(api_key, model, **kwargs)
        elif provider.lower() == 'anthropic':
            if model is None:
                model = 'claude-3-sonnet-20240229'
            return AnthropicClient(api_key, model, **kwargs)
        elif provider.lower() in ['zhipuai', '智谱']:
            if model is None:
                model = 'GLM-4'
            return ZhipuAIClient(api_key, model, **kwargs)
        else:
            raise LLMError(f"不支持的模型提供商: {provider}")

    @staticmethod
    def get_supported_providers() -> List[str]:
        """获取支持的提供商列表"""
        return ['openai', 'anthropic', 'zhipuai']