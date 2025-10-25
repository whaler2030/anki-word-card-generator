"""
数据模型定义
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class MemoryTip(BaseModel):
    """记忆技巧模型"""
    type: Optional[str] = Field(None, description="记忆技巧类型（可选）")
    content: str = Field(..., description="记忆技巧描述")

class WordCard(BaseModel):
    """单词卡片模型"""
    word: str = Field(..., description="单词拼写")
    phonetic: str = Field(..., description="音标")
    part_of_speech: str = Field(..., description="词性")
    meaning: str = Field(..., description="中文释义")
    memory_tip: MemoryTip = Field(..., description="记忆技巧")
    examples: List[str] = Field(..., description="例句列表")
    synonyms: List[str] = Field(..., description="同义词列表")
    confusables: List[str] = Field(..., description="易混淆词列表")
    word_audio: Optional[str] = Field(None, description="单词发音文件路径或URL")
    example_audios: Optional[List[str]] = Field(None, description="例句发音文件路径列表")
    word_audio_url: Optional[str] = Field(None, description="单词发音URL")
    word_audio_html: Optional[str] = Field(None, description="单词发音HTML代码")
    example_audio_urls: Optional[List[str]] = Field(None, description="例句发音URL列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    @validator('examples')
    def validate_examples(cls, v):
        if len(v) < 1 or len(v) > 5:
            raise ValueError("例句数量必须在1-5之间")
        return v

    @validator('synonyms')
    def validate_synonyms(cls, v):
        if len(v) < 0 or len(v) > 10:
            raise ValueError("同义词数量必须在0-10之间")
        return v

    @validator('confusables')
    def validate_confusables(cls, v):
        if len(v) < 0 or len(v) > 5:
            raise ValueError("易混淆词数量必须在0-5之间")
        return v

    @validator('word')
    def validate_word(cls, v):
        if not v.isalpha():
            raise ValueError("单词必须只包含字母")
        return v.lower()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class GenerationRequest(BaseModel):
    """生成请求模型"""
    words: List[str] = Field(..., description="要生成的单词列表")
    rules: Dict[str, Any] = Field(default_factory=dict, description="生成规则")
    source: str = Field(default="builtin", description="词库来源")

class GenerationResult(BaseModel):
    """生成结果模型"""
    word: str = Field(..., description="单词")
    success: bool = Field(..., description="是否成功")
    card_data: Optional[WordCard] = Field(None, description="生成的卡片数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")

class BatchGenerationResult(BaseModel):
    """批量生成结果模型"""
    total_words: int = Field(..., description="总单词数")
    success_count: int = Field(..., description="成功生成数")
    failed_count: int = Field(..., description="失败生成数")
    results: List[GenerationResult] = Field(..., description="生成结果列表")
    started_at: datetime = Field(..., description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

class ExportSettings(BaseModel):
    """导出设置模型"""
    format: str = Field(..., description="导出格式: csv/apkg")
    deck_name: str = Field(..., description="牌组名称")
    deck_description: str = Field(..., description="牌组描述")
    csv_delimiter: str = Field(default=",", description="CSV分隔符")
    include_media: bool = Field(default=False, description="是否包含媒体文件")

class WordSource(BaseModel):
    """词库来源模型"""
    source_type: str = Field(..., description="词库类型: builtin/user")
    source_path: str = Field(..., description="词库路径")
    word_count: int = Field(..., description="单词数量")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")