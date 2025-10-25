#!/usr/bin/env python3
"""
Anki单词卡片生成器启动脚本
解决导入问题的统一入口
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入CLI主模块
from cli.main import cli

if __name__ == '__main__':
    cli()