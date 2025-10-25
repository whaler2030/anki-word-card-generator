"""
自定义异常类定义
"""

class AnkiCardGeneratorError(Exception):
    """基础异常类"""
    pass

class ConfigError(AnkiCardGeneratorError):
    """配置文件相关错误"""
    pass

class LLMError(AnkiCardGeneratorError):
    """大模型API相关错误"""
    pass

class DataValidationError(AnkiCardGeneratorError):
    """数据验证错误"""
    pass

class ImportError(AnkiCardGeneratorError):
    """导入相关错误"""
    pass

class ExportError(AnkiCardGeneratorError):
    """导出相关错误"""
    pass