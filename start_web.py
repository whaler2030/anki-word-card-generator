#!/usr/bin/env python3
"""
Anki单词卡片生成器Web服务器启动脚本
解决导入问题的统一入口
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入Web应用
from web.app import app, initialize_app

if __name__ == '__main__':
    # 初始化应用
    if initialize_app():
        print("🚀 Web应用启动成功！")
        print("📍 访问地址: http://localhost:5001")
        print("📖 按 Ctrl+C 停止服务器")
        app.run(debug=True, host='0.0.0.0', port=5001)
    else:
        print("❌ Web应用初始化失败，请检查配置")