"""
配置文件解析器
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from utils.exceptions import ConfigError
from utils.logger import get_logger

logger = get_logger(__name__)

class ConfigParser:
    """配置文件解析器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = {}
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                raise ConfigError(f"配置文件不存在: {self.config_path}")

            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)

            if not self.config:
                raise ConfigError("配置文件为空")

            logger.info(f"成功加载配置文件: {self.config_path}")
            self._validate_config()

        except yaml.YAMLError as e:
            raise ConfigError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ConfigError(f"加载配置文件失败: {e}")

    def _validate_config(self):
        """验证配置文件格式"""
        required_sections = ['llm_config', 'dict_settings', 'export_settings']

        for section in required_sections:
            if section not in self.config:
                raise ConfigError(f"配置文件缺少必要部分: {section}")

        # 验证LLM配置
        llm_config = self.config['llm_config']
        required_llm_fields = ['provider', 'api_key', 'model']
        for field in required_llm_fields:
            if field not in llm_config:
                raise ConfigError(f"LLM配置缺少必要字段: {field}")

        # 验证导出配置
        export_config = self.config['export_settings']
        if 'default_format' not in export_config:
            export_config['default_format'] = 'csv'

    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self.config.get('llm_config', {})

    def get_dict_settings(self) -> Dict[str, Any]:
        """获取词库设置"""
        return self.config.get('dict_settings', {})

    def get_export_settings(self) -> Dict[str, Any]:
        """获取导出设置"""
        return self.config.get('export_settings', {})

    def get_generation_rules(self) -> Dict[str, Any]:
        """获取生成规则"""
        return self.config.get('generation_rules', {})

    def get_batch_settings(self) -> Dict[str, Any]:
        """获取批处理设置"""
        return self.config.get('batch_settings', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.config.get('logging', {})

    def get_audio_settings(self) -> Dict[str, Any]:
        """获取音频设置"""
        return self.config.get('audio_settings', {})

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def update_config(self, key: str, value: Any):
        """更新配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置已保存到: {self.config_path}")
        except Exception as e:
            raise ConfigError(f"保存配置文件失败: {e}")

    def get_config_path(self) -> Path:
        """获取配置文件路径"""
        return self.config_path