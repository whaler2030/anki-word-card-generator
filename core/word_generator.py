"""
单词卡片生成器
"""

import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from utils.exceptions import LLMError, DataValidationError
from utils.logger import get_logger
from core.llm_client import LLMClientFactory
from data.models import WordCard, GenerationRequest, GenerationResult, BatchGenerationResult
from datetime import datetime

logger = get_logger(__name__)

class WordCardGenerator:
    """单词卡片生成器"""

    def __init__(self, llm_config: Dict[str, Any], batch_config: Dict[str, Any]):
        self.llm_config = llm_config
        self.batch_config = batch_config
        self.llm_client = None
        self._setup_llm_client()

    def _setup_llm_client(self):
        """设置大模型客户端"""
        try:
            provider = self.llm_config.get('provider')
            api_key = self.llm_config.get('api_key')
            model = self.llm_config.get('model')

            # 过滤配置参数 - 只传递LLM客户端支持的参数
            supported_kwargs = {
                'max_tokens': self.llm_config.get('max_tokens', 2000),
                'temperature': self.llm_config.get('temperature', 0.7),
                'timeout': self.llm_config.get('timeout', 30),
                'base_url': self.llm_config.get('base_url')
            }

            # 移除None值
            kwargs = {k: v for k, v in supported_kwargs.items() if v is not None}

            self.llm_client = LLMClientFactory.create_client(provider, api_key, model, **kwargs)

            # 检查API可用性
            if not self.llm_client.is_available():
                raise LLMError(f"大模型API不可用: {provider}")

            logger.info(f"大模型客户端初始化成功: {provider}")

        except Exception as e:
            logger.error(f"大模型客户端初始化失败: {e}")
            raise LLMError(f"大模型客户端初始化失败: {e}")

    def generate_single_card(self, word: str, rules: Dict[str, Any]) -> GenerationResult:
        """生成单个单词卡片"""
        max_retries = self.batch_config.get('retry_count', 3)
        retry_delay = self.batch_config.get('retry_delay', 1)

        for attempt in range(max_retries):
            try:
                logger.info(f"开始生成单词卡片: {word} (尝试 {attempt + 1}/{max_retries})")

                # 调用大模型API生成内容
                raw_data = self.llm_client.generate_word_card(word, rules)

                # 创建单词卡片对象
                word_card = WordCard(
                    word=raw_data.get('word', word),
                    phonetic=raw_data.get('phonetic', ''),
                    part_of_speech=raw_data.get('part_of_speech', ''),
                    meaning=raw_data.get('meaning', ''),
                    memory_tip=raw_data.get('memory_tip', {'type': '', 'content': ''}),
                    examples=raw_data.get('examples', []),
                    synonyms=raw_data.get('synonyms', []),
                    confusables=raw_data.get('confusables', [])
                )

                logger.info(f"成功生成单词卡片: {word}")

                return GenerationResult(
                    word=word,
                    success=True,
                    card_data=word_card,
                    generated_at=datetime.now()
                )

            except Exception as e:
                logger.warning(f"生成单词卡片失败: {word}, 尝试 {attempt + 1}/{max_retries}, 错误: {e}")

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error(f"生成单词卡片最终失败: {word}, 错误: {e}")
                    return GenerationResult(
                        word=word,
                        success=False,
                        error_message=str(e),
                        generated_at=datetime.now()
                    )

    def generate_batch_cards(self, words: List[str], rules: Dict[str, Any] = None) -> BatchGenerationResult:
        """批量生成单词卡片"""
        if rules is None:
            rules = {}

        total_words = len(words)
        started_at = datetime.now()
        results = []
        success_count = 0
        failed_count = 0

        logger.info(f"开始批量生成 {total_words} 个单词卡片")

        # 获取批处理配置
        batch_size = self.batch_config.get('batch_size', 5)
        rate_limit = self.batch_config.get('rate_limit', 10)  # requests per minute

        # 如果启用了多线程
        if batch_size > 1:
            results = self._generate_parallel(words, rules, batch_size, rate_limit)
        else:
            results = self._generate_sequential(words, rules)

        # 统计结果
        success_count = sum(1 for result in results if result.success)
        failed_count = total_words - success_count

        logger.info(f"批量生成完成: 成功 {success_count}, 失败 {failed_count}")

        return BatchGenerationResult(
            total_words=total_words,
            success_count=success_count,
            failed_count=failed_count,
            results=results,
            started_at=started_at,
            completed_at=datetime.now()
        )

    def _generate_sequential(self, words: List[str], rules: Dict[str, Any]) -> List[GenerationResult]:
        """顺序生成单词卡片"""
        results = []

        for word in tqdm(words, desc="生成单词卡片"):
            result = self.generate_single_card(word, rules)
            results.append(result)

            # 简单的速率限制
            time.sleep(0.1)  # 每个单词间隔0.1秒

        return results

    def _generate_parallel(self, words: List[str], rules: Dict[str, Any],
                          batch_size: int, rate_limit: int) -> List[GenerationResult]:
        """并行生成单词卡片"""
        results = []
        min_delay = 60.0 / rate_limit  # 计算最小延迟

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # 提交所有任务
            future_to_word = {
                executor.submit(self._generate_with_delay, word, rules, min_delay): word
                for word in words
            }

            # 使用进度条跟踪进度
            with tqdm(total=len(words), desc="生成单词卡片") as pbar:
                for future in as_completed(future_to_word):
                    result = future.result()
                    results.append(result)
                    pbar.update(1)

        return results

    def _generate_with_delay(self, word: str, rules: Dict[str, Any], delay: float) -> GenerationResult:
        """带延迟的单词卡片生成（用于速率限制）"""
        start_time = time.time()

        result = self.generate_single_card(word, rules)

        # 确保至少延迟指定时间
        elapsed = time.time() - start_time
        if elapsed < delay:
            time.sleep(delay - elapsed)

        return result

    def generate_from_request(self, request: GenerationRequest) -> BatchGenerationResult:
        """从请求对象生成单词卡片"""
        logger.info(f"处理生成请求: {request.words}")

        return self.generate_batch_cards(request.words, request.rules)

    def get_generation_statistics(self, results: List[GenerationResult]) -> Dict[str, Any]:
        """获取生成统计信息"""
        total = len(results)
        success = sum(1 for result in results if result.success)
        failed = total - success

        # 计算平均生成时间
        generation_times = []
        for result in results:
            if result.success:
                time_diff = (result.generated_at - results[0].generated_at).total_seconds()
                generation_times.append(time_diff)

        avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0

        # 收集错误信息
        errors = {}
        for result in results:
            if not result.success and result.error_message:
                error_type = result.error_message.split(':')[0] if ':' in result.error_message else result.error_message
                errors[error_type] = errors.get(error_type, 0) + 1

        return {
            'total_cards': total,
            'success_count': success,
            'failed_count': failed,
            'success_rate': (success / total) * 100 if total > 0 else 0,
            'average_generation_time': avg_generation_time,
            'error_distribution': errors
        }

    def validate_word_list(self, words: List[str]) -> List[str]:
        """验证单词列表"""
        valid_words = []

        for word in words:
            # 基本验证
            if (isinstance(word, str) and
                word.strip() and
                word.isalpha() and
                len(word) > 1):

                valid_words.append(word.lower().strip())
            else:
                logger.warning(f"无效单词，跳过: {word}")

        logger.info(f"单词列表验证完成: {len(valid_words)}/{len(words)} 个单词有效")
        return valid_words

    def preview_generation(self, sample_words: List[str], rules: Dict[str, Any] = None) -> Dict[str, Any]:
        """预览生成效果"""
        if not sample_words:
            return {'error': '没有提供示例单词'}

        if rules is None:
            rules = {}

        # 只生成前3个单词作为预览
        preview_words = sample_words[:3]

        logger.info(f"开始预览生成: {preview_words}")

        results = []
        for word in preview_words:
            try:
                result = self.generate_single_card(word, rules)
                results.append({
                    'word': word,
                    'success': result.success,
                    'preview': result.card_data.dict() if result.success else None,
                    'error': result.error_message
                })
            except Exception as e:
                results.append({
                    'word': word,
                    'success': False,
                    'preview': None,
                    'error': str(e)
                })

        return {
            'preview_words': preview_words,
            'results': results,
            'success_count': sum(1 for r in results if r['success']),
            'total_previewed': len(results)
        }