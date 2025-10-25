# Anki 单词卡片生成器 - 项目结构说明

## 📁 项目概览

这是一个基于大模型API的智能英语学习卡片生成工具，支持批量生成高质量Anki单词卡片。项目采用模块化设计，便于维护和扩展。

## 🏗️ 项目架构

```
anki-word-card-generator/
├── 📋 核心配置文件
│   ├── config.yaml              # 主配置文件（包含API密钥、生成规则等）
│   ├── requirements.txt         # Python依赖包列表
│   ├── setup.py                # 项目安装脚本
│   └── README.md               # 项目说明文档
│
├── 🚀 快速启动脚本
│   ├── start.py                # 命令行快速启动脚本
│   ├── start_web.py            # Web界面启动脚本
│   └── demo.py                 # 功能演示脚本
│
├── 🧠 核心功能模块 (core/)
│   ├── llm_client.py          # 大模型API客户端（支持OpenAI、Anthropic、智谱AI）
│   ├── word_generator.py      # 单词卡片生成器
│   ├── audio_generator.py     # 音频生成器基类
│   ├── audio_generator_simple.py  # 简化音频生成器
│   ├── audio_generator_online.py  # 在线音频生成器
│   └── data_validator.py      # 数据验证器
│
├── 📊 数据管理模块 (data/)
│   ├── models.py              # 数据模型定义（使用Pydantic）
│   ├── builtin_dict.py        # 内置词库（按难度和分类组织）
│   └── word_importer.py      # 外部词库导入器（支持TXT/CSV/JSON）
│
├── 📤 导出功能模块 (export/)
│   └── anki_exporter.py       # Anki APKG导出器（支持HTML美化卡片）
│
├── ⚙️ 配置管理模块 (config/)
│   └── config_parser.py       # YAML配置文件解析器
│
├── 🔧 工具模块 (utils/)
│   ├── logger.py              # 日志管理工具
│   └── exceptions.py          # 自定义异常定义
│
├── 🌐 Web界面模块 (web/)
│   ├── app.py                 # Flask应用主文件
│   └── templates/            # HTML模板文件
│       ├── index.html        # 主页面
│       ├── result.html       # 结果页面
│       └── static/           # 静态资源文件
│
├── 💻 命令行界面 (cli/)
│   └── main.py               # CLI主入口文件
│
├── 📁 数据和输出目录
│   ├── data/                  # 数据文件目录
│   │   ├── builtin_words.json # 内置词库数据
│   │   └── imported_words/   # 导入的词库文件
│   ├── output/                # 生成的卡片输出目录
│   │   ├── cards.csv         # CSV格式卡片
│   │   ├── cards.apkg        # Anki牌组文件
│   │   └── study_guide.html  # 学习指南
│   └── logs/                  # 日志文件目录
│
└── 🧪 测试模块 (tests/)
    ├── test_llm_client.py     # LLM客户端测试
    ├── test_word_generator.py # 单词生成器测试
    ├── test_data_models.py    # 数据模型测试
    └── test_anki_exporter.py  # 导出功能测试
```

## 🔧 核心功能说明

### 1. 大模型集成 (core/llm_client.py)
- **支持的模型提供商**: OpenAI (GPT-4)、Anthropic (Claude-3)、智谱AI (GLM-4)
- **智能错误处理**: 自动重试、降级策略、模拟模式
- **配置灵活性**: 支持自定义模型参数、API端点、超时设置

### 2. 单词卡片生成 (core/word_generator.py)
- **完整数据结构**: 音标、词性、释义、记忆技巧、例句、同义词、易混淆词
- **智能缓存**: 避免重复生成相同单词
- **批量处理**: 支持并发生成多个单词
- **数据验证**: 严格的内容验证和错误处理

### 3. 音频生成 (core/audio_generator_*.py)
- **多引擎支持**: 在线TTS、Google TTS、Edge TTS
- **智能音频**: 单词发音、例句发音
- **格式支持**: MP3、WAV
- **自动清理**: 临时文件管理

### 4. Anki导出 (export/anki_exporter.py)
- **多格式支持**: CSV、APKG、学习指南HTML
- **美化卡片**: 现代化渐变设计、颜色区分、响应式布局
- **音频集成**: 自动嵌入音频文件
- **兼容性**: 完全兼容Anki桌面版和移动版

### 5. 词库管理 (data/)
- **内置词库**: 2000+常用单词，按难度和分类组织
- **多格式导入**: TXT、CSV、JSON文件支持
- **词库统计**: 详细的单词分布和使用统计

## 🎨 特色功能

### 1. 智能易混淆词生成
- **实时分析**: 基于LLM的实时语言分析
- **多维度识别**: 发音相似、拼写相似、常见混淆模式
- **准确释义**: 每个易混淆词都包含中文释义

### 2. 现代化卡片设计
- **渐变背景**: 精美的多色渐变设计
- **颜色编码**: 不同字段类型使用不同颜色
- **响应式布局**: 适配手机和电脑
- **动画效果**: 背景元素浮动动画

### 3. 在线音频集成
- **高质量发音**: 集成多个在线TTS服务
- **无需下载**: 音频流式播放，不占用本地空间
- **多语言支持**: 英语、中文发音
- **自动重试**: 智能错误处理和重试机制

### 4. Web界面
- **拖拽上传**: 支持文件拖拽上传
- **实时进度**: 生成进度实时显示
- **响应式设计**: 适配各种设备
- **用户友好**: 直观的操作界面

## 📋 配置说明

### 主要配置项 (config.yaml)
- **LLM配置**: 模型提供商、API密钥、模型参数
- **音频设置**: TTS引擎、语言、音频格式
- **生成规则**: 例句数量、同义词数量、易混淆词数量
- **导出设置**: 输出格式、牌组名称、编码设置
- **批处理**: 并发数量、重试策略、速率限制

### 环境要求
- **Python**: 3.8+
- **依赖**: 见requirements.txt
- **网络**: 需要访问大模型API和音频服务
- **Anki**: 用于导入生成的卡片（可选）

## 🚀 使用方式

### 1. 命令行使用
```bash
# 生成指定单词
python start.py generate apple banana orange

# 使用内置词库
python start.py builtin --random --count 10

# 启动Web界面
python start_web.py
```

### 2. Web界面使用
1. 访问 http://localhost:5000
2. 选择词库或上传单词列表
3. 配置生成选项
4. 点击生成并下载结果

### 3. 编程接口
```python
from core.word_generator import WordGenerator
from core.llm_client import LLMClientFactory

# 创建LLM客户端
client = LLMClientFactory.create_client(
    provider="zhipuai",
    api_key="your-api-key"
)

# 生成单词卡片
generator = WordGenerator(client)
card = generator.generate_word_card("apple")
```

## 🔄 工作流程

1. **初始化**: 加载配置文件、初始化LLM客户端
2. **词库准备**: 选择内置词库或导入外部词库
3. **单词生成**: 调用LLM生成单词卡片内容
4. **音频生成**: 为单词和例句生成音频（可选）
5. **数据验证**: 验证生成内容的完整性和准确性
6. **格式导出**: 生成CSV、APKG或其他格式的输出文件
7. **结果输出**: 保存到输出目录并提供下载

## 🎯 项目特点

- **模块化设计**: 清晰的模块划分，便于维护和扩展
- **错误处理**: 完整的异常处理和日志记录
- **性能优化**: 批量处理、并发生成、智能缓存
- **用户体验**: 直观的界面、详细的文档、友好的错误提示
- **扩展性**: 支持新的模型提供商、音频引擎、导出格式

## 📊 技术栈

- **后端**: Python + Flask + Pydantic
- **AI集成**: OpenAI API + Anthropic API + 智谱AI API
- **音频处理**: 在线TTS服务
- **前端**: HTML + CSS + JavaScript
- **数据处理**: YAML + JSON + CSV
- **导出格式**: Anki APKG + CSV + HTML

---

**项目状态**: ✅ 开发完成，功能稳定，可用于生产环境
**最后更新**: 2025年10月
**维护状态**: 🔄 持续维护中