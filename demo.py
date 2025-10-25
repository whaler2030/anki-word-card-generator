#!/usr/bin/env python3
"""
Anki单词卡片生成器 - 演示版本
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

def demo_usage():
    """演示工具使用"""
    print("🎉 Anki单词卡片生成器演示")
    print("=" * 50)

    print("\n📋 项目结构:")
    print("""
anki-word-card-generator/
├── config.yaml              # 配置文件（需要设置API密钥）
├── cli/main.py             # 命令行界面
├── core/                  # 核心功能
├── data/                  # 数据模块
├── export/                # 导出功能
├── utils/                 # 工具模块
└── README.md              # 详细说明文档
    """)

    print("\n🚀 使用步骤:")
    print("\n1️⃣ 安装依赖:")
    print("   pip install -r requirements.txt")

    print("\n2️⃣ 配置API密钥:")
    print("   编辑 config.yaml 文件")
    print("   将 'sk-your-real-api-key-here' 替换为您的真实API密钥")

    print("\n3️⃣ 主要命令:")
    print("   # 初始化系统")
    print("   python cli/main.py init")
    print("   ")
    print("   # 使用内置词库生成")
    print("   python cli/main.py builtin --random --count 5")
    print("   ")
    print("   # 生成指定单词")
    print("   python cli/main.py generate apple banana orange")
    print("   ")
    print("   # 查看帮助")
    print("   python cli/main.py --help")

    print("\n📤 导出格式:")
    print("   • CSV格式 - Anki标准格式")
    print("   • APKG格式 - Anki牌组文件")
    print("   • 学习指南格式 - 适合学习使用")

    print("\n📊 支持的词库格式:")
    print("   • TXT - 每行一个单词")
    print("   • CSV - 表格格式")
    print("   • JSON - 结构化数据")
    print("   • 内置词库 - 常用英语单词")

    print("\n💡 生成内容包含:")
    print("   ✅ 单词拼写")
    print("   ✅ 音标（IPA格式）")
    print("   ✅ 词性标注")
    print("   ✅ 中文释义")
    print("   ✅ 记忆技巧（谐音法/拆分法/词根法）")
    print("   ✅ 3个来自知名刊物的例句")
    print("   ✅ 3个同义词")
    print("   ✅ 2个易混淆词")

def check_setup():
    """检查设置"""
    print("\n🔍 检查项目设置...")

    # 检查配置文件
    config_file = Path("config.yaml")
    if config_file.exists():
        print("✅ 配置文件存在")

        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            import yaml
            config = yaml.safe_load(f)

        api_key = config.get('llm_config', {}).get('api_key', '')
        if api_key and 'your-api-key' not in api_key:
            print("✅ API密钥已配置")
        else:
            print("⚠️  请在config.yaml中设置您的API密钥")
    else:
        print("❌ 配置文件不存在")

    # 检查数据目录
    data_dir = Path("data")
    if data_dir.exists():
        print("✅ 数据目录存在")
    else:
        print("❌ 数据目录不存在")

    # 检查输出目录
    output_dir = Path("output")
    if output_dir.exists():
        print("✅ 输出目录存在")
    else:
        print("❌ 输出目录不存在，将自动创建")

if __name__ == "__main__":
    try:
        import yaml
        demo_usage()
        check_setup()

        print("\n🎯 下一步:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 设置API密钥: 编辑config.yaml")
        print("3. 开始使用: python cli/main.py init")

        print("\n📖 详细使用说明请查看 README.md")

    except ImportError as e:
        print(f"\n❌ 缺少依赖包: {e}")
        print("请运行: pip install -r requirements.txt")

    print("\n" + "=" * 50)