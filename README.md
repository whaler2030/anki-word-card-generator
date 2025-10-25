# Anki 单词卡片生成器

基于大模型API的智能英语学习卡片生成工具，支持批量生成高质量Anki单词卡片。

## ✨ 主要特性

- 🤖 **智能生成**: 基于大模型API（OpenAI、Anthropic、智谱AI）生成详细的单词卡片内容
- 📚 **多词库支持**: 内置词库 + 用户导入词库（TXT/CSV/JSON）
- 🎯 **完整数据结构**: 包含音标、词性、释义、记忆技巧、例句、同义词、易混淆词
- 📤 **多格式导出**: 支持CSV和APKG格式，可直接导入Anki
- 🎨 **美化卡片**: 现代化渐变设计，颜色区分不同字段类型
- 🔊 **在线音频**: 集成在线音频生成器，支持高质量发音
- 🌐 **Web界面**: 响应式Web界面，支持拖拽上传和实时进度
- 🚀 **批量处理**: 支持批量生成和并行处理
- 🔍 **数据验证**: 严格的数据验证和错误处理
- 📊 **统计信息**: 详细的生成统计和词库统计

## 📋 系统要求

- Python 3.8+
- 大模型API密钥（OpenAI、Anthropic、智谱AI等）
- Anki（用于导入生成的卡片）
- 网络连接（用于音频生成和API调用）

## 🚀 快速开始

### 1. 安装依赖

```bash
cd anki-word-card-generator
pip install -r requirements.txt
```

### 2. 配置API密钥

编辑 `config.yaml` 文件，设置您的大模型API密钥：

```yaml
llm_config:
  provider: "openai"  # 可选: openai, anthropic, zhipuai
  api_key: "your-api-key-here"
  model: "gpt-4"       # 可选: gpt-4, gpt-3.5-turbo, claude-3-sonnet, glm-4等
```

### 3. 初始化系统

```bash
python start.py init
```

### 4. 生成单词卡片

#### 使用内置词库

```bash
# 生成10个随机单词的卡片
python start.py builtin --random --count 10

# 按分类生成
python start.py builtin --category "情感" --count 5

# 按难度生成
python start.py builtin --difficulty "easy" --count 5

# 预览生成效果
python start.py builtin --random --count 3 --preview
```

#### 导入外部词库

```bash
# 预览导入文件
python start.py import-words words.txt --preview

# 导入并生成
python start.py import-words words.txt
```

#### 生成指定单词

```bash
# 生成指定单词的卡片
python start.py generate apple banana orange

# 预览生成效果
python start.py generate apple banana orange --preview

#### 启用音频功能

```bash
# 生成带音频的卡片
python start.py generate apple banana orange --enable-audio

# 使用内置词库生成带音频的卡片
python start.py builtin --random --count 5 --enable-audio --output-format apkg
```

#### 启动Web界面

```bash
# 启动Web服务器
python start_web.py

# 访问 http://localhost:5000
```
```

## 📁 项目结构

```
anki-word-card-generator/
├── config.yaml              # 主配置文件
├── requirements.txt         # 依赖包列表
├── setup.py                # 安装脚本
├── README.md               # 项目说明
├── demo.py                 # 演示脚本
├── start.py                # 快速启动脚本
├── start_web.py            # Web界面启动脚本
├── cli/                    # 命令行界面
│   └── main.py            # 主入口文件
├── core/                  # 核心功能模块
│   ├── llm_client.py      # 大模型API客户端
│   ├── audio_generator.py      # 音频生成器基类
│   ├── audio_generator_simple.py  # 简化音频生成器
│   ├── audio_generator_online.py # 在线音频生成器
│   ├── word_generator.py  # 单词卡片生成器
│   └── data_validator.py  # 数据验证器
├── data/                  # 数据模块
│   ├── models.py          # 数据模型定义
│   ├── builtin_dict.py    # 内置词库
│   └── word_importer.py   # 词库导入器
├── export/                # 导出模块
│   └── anki_exporter.py   # Anki APKG导出器
├── config/                # 配置模块
│   └── config_parser.py   # 配置解析器
├── utils/                 # 工具模块
│   ├── logger.py          # 日志工具
│   └── exceptions.py      # 异常定义
├── web/                   # Web界面模块
│   ├── app.py             # Flask应用主文件
│   └── templates/        # HTML模板
├── tests/                 # 测试模块
├── output/                # 输出目录
└── logs/                  # 日志目录
```

## ⚙️ 配置说明

### LLM配置

```yaml
llm_config:
  provider: "openai"                    # 模型提供商
  api_key: "your-api-key"              # API密钥
  model: "gpt-4"                       # 模型名称
  base_url: "https://api.openai.com/v1" # API基础URL
  max_tokens: 2000                     # 最大token数
  temperature: 0.7                     # 创造性参数
  timeout: 30                          # 请求超时时间
```

### 导出设置

```yaml
export_settings:
  default_format: "csv"                # 默认导出格式
  csv_delimiter: ","                  # CSV分隔符
  deck_name: "英语单词卡片"             # 牌组名称
  deck_description: "由AI生成的英语学习卡片" # 牌组描述
  include_media: false                # 是否包含媒体文件

audio_settings:
  enable_audio: true                  # 是否启用音频生成
  tts_engine: "gtts"                  # gTTS, edge
  voice_language: "en"                # en, zh
  voice_gender: "female"              # male, female
  generate_word_audio: true           # 是否生成单词发音
  generate_example_audio: false       # 是否生成例句发音
  audio_format: "mp3"                 # mp3, wav
  cleanup_temp: true                  # 是否清理临时文件
```

### 生成规则

```yaml
generation_rules:
  example_count: 3                     # 例句数量
  synonym_count: 3                     # 同义词数量
  confusable_count: 2                  # 易混淆词数量
  tip_types: ["谐音法", "拆分法", "词根法"] # 记忆技巧类型
```

## 📤 导出格式

### 1. CSV格式（Anki标准）

支持直接导入Anki，包含完整的HTML格式化内容。

### 2. CSV格式（简化）

适合查看和编辑的简化格式。

### 3. APKG格式（Anki牌组）

可直接导入Anki的完整牌组文件。

### 4. 学习指南格式

专门为学习设计的格式，包含学习建议。

## 🔊 音频功能

### 在线音频生成

系统集成了在线音频生成器，支持高质量英文发音：

- ✅ 集成多个在线TTS服务（Google TTS、Edge TTS等）
- ✅ 自动生成音频链接，嵌入APKG文件
- ✅ 支持多种语言和声音选择
- ✅ 智能重试和错误处理
- ✅ 无需本地音频文件管理

### 音频配置

在 `config.yaml` 中配置音频设置：

```yaml
audio_settings:
  enable_audio: true                  # 启用音频生成
  tts_engine: "online"               # online, gtts, edge
  voice_language: "en"               # en, zh
  voice_gender: "female"             # male, female
  generate_word_audio: true          # 生成单词发音
  generate_example_audio: false       # 生成例句发音
  cleanup_temp: true                  # 清理临时文件
```

### 使用音频

1. 在APKG卡片中会显示音频播放器
2. 点击即可播放单词发音
3. 支持在线音频流，无需下载大文件

## 🎨 卡片美化

### 现代化设计

卡片采用现代化设计语言：

- 🌈 **渐变背景**: 精美的渐变色背景
- 🎭 **浮动动画**: 背景元素柔和浮动
- 🎨 **颜色区分**: 不同字段使用不同颜色
- 📱 **响应式设计**: 适配手机和电脑

### 颜色方案

| 字段类型 | 颜色 | 用途 |
|---------|------|------|
| **词性** | 蓝色渐变 | 快速识别词性 |
| **释义** | 橙色渐变 | 突出单词含义 |
| **记忆技巧** | 青色渐变 | 帮助记忆重点 |
| **例句** | 绿色渐变 | 示例句子展示 |
| **同义词** | 粉色渐变 | 词汇扩展区域 |
| **易混淆词** | 浅色渐变 | 警示区分要点 |

### 交互特性

- 音频按钮悬停效果
- 卡片圆角和阴影
- 清晰的文字层级
- 优化的移动端体验

## 📊 统计信息

查看词库和生成统计：

```bash
python cli/main.py stats
```

显示：
- 内置词库单词总数
- 按难度分布
- 按分类分布
- 生成成功率
- 错误统计

## 🔧 高级用法

### 1. 自定义配置文件

```bash
python cli/main.py --config custom-config.yaml init
```

### 2. 批处理设置

```yaml
batch_settings:
  batch_size: 5           # 并发处理数量
  retry_count: 3          # 重试次数
  retry_delay: 1          # 重试延迟（秒）
  rate_limit: 10         # 速率限制（请求/分钟）
```

### 3. 错误处理

系统包含完整的错误处理机制：
- 网络错误自动重试
- 数据验证失败处理
- 详细的错误日志
- 生成失败单词的统计

### 4. 日志配置

```yaml
logging:
  level: "INFO"           # 日志级别
  file: "logs/app.log"    # 日志文件路径
  max_size: "10MB"        # 最大文件大小
  backup_count: 5         # 备份文件数量
```

## 🛠️ 开发指南

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-cov

# 运行测试
pytest tests/

# 生成覆盖率报告
pytest --cov=anki_word_card_generator tests/
```

### 代码格式化

```bash
# 安装格式化工具
pip install black flake8 mypy

# 格式化代码
black .

# 代码检查
flake8 .

# 类型检查
mypy .
```

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `config.yaml` 中的 `api_key` 设置
   - 确认API密钥有效且有足够余额

2. **网络连接问题**
   - 检查网络连接
   - 如需代理，设置 `base_url` 参数

3. **导入Anki失败**
   - 确保字符编码为UTF-8
   - 检查CSV文件格式
   - 在Anki中正确选择字段映射

4. **生成内容质量差**
   - 调整 `temperature` 参数
   - 尝试不同的模型
   - 修改提示词模板

### 获取帮助

- 查看 [Issues](https://github.com/your-username/anki-word-card-generator/issues)
- 阅读 [Wiki](https://github.com/your-username/anki-word-card-generator/wiki)
- 联系开发团队

## 🎯 路线图

- [x] ✅ 支持多种大模型提供商（OpenAI、Anthropic、智谱AI）
- [x] ✅ 集成在线音频生成功能
- [x] ✅ 美化卡片样式（渐变设计）
- [x] ✅ 开发Web界面（响应式设计）
- [x] ✅ 优化易混淆词生成（基于LLM实时分析）
- [x] ✅ 改进同义词和易混淆词显示格式
- [ ] 集成例句翻译功能
- [ ] 添加学习进度保存和恢复
- [ ] 支持多语言用户界面
- [ ] 智能复习计划集成
- [ ] 集成在线词典API（剑桥、牛津等）
- [ ] 支持更多TTS引擎和服务商
- [ ] 智能缓存和性能优化
- [ ] 移动端App开发
- [ ] 用户账户和学习数据同步

---

**Happy Learning! 🎉**