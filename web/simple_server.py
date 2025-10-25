#!/usr/bin/env python3
"""
简化版Web服务器 - 演示用途
"""

import os
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import mimetypes

class AnkiCardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/' or self.path == '/index.html':
            self.send_html_response('''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anki单词卡片生成器 - Web界面演示</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; }
        .navbar { box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card { border: none; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 1rem; }
        .btn-primary { background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%); border: none; }
        .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 4rem 0; }
        .hero h1 { font-size: 3rem; font-weight: bold; }
        .hero p { font-size: 1.25rem; opacity: 0.9; }
        .feature-icon { font-size: 3rem; color: #0d6efd; }
        .word-item { display: inline-block; background: #0d6efd; color: white; padding: 0.25rem 0.75rem; margin: 0.25rem; border-radius: 20px; }
        .upload-area { border: 2px dashed #dee2e6; border-radius: 8px; padding: 2rem; text-align: center; }
        .upload-area:hover { border-color: #0d6efd; background-color: rgba(13, 110, 253, 0.05); }
        .progress { background: #e9ecef; border-radius: 8px; overflow: hidden; }
        .progress-bar { background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%); }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="bi bi-mortarboard-fill"></i> Anki单词卡片生成器
            </a>
            <span class="navbar-text ms-auto">Web界面演示</span>
        </div>
    </nav>

    <!-- Hero Section -->
    <div class="hero text-center">
        <div class="container">
            <h1 class="mb-4">🎉 Anki单词卡片生成器</h1>
            <p class="lead mb-0">基于大模型API的智能英语学习卡片生成工具</p>
        </div>
    </div>

    <!-- Main Content -->
    <div class="container mt-4">
        <div class="row">
            <div class="col-lg-8">
                <!-- Features -->
                <div class="card mb-4">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0"><i class="bi bi-stars"></i> 主要功能</h5>
                    </div>
                    <div class="card-body">
                        <div class="row g-4">
                            <div class="col-6 text-center">
                                <i class="bi bi-cpu feature-icon d-block mb-2"></i>
                                <h6>智能生成</h6>
                                <p class="text-muted small mb-0">基于大模型API生成详细单词卡片</p>
                            </div>
                            <div class="col-6 text-center">
                                <i class="bi bi-book feature-icon d-block mb-2"></i>
                                <h6>多词库支持</h6>
                                <p class="text-muted small mb-0">内置词库 + 外部文件导入</p>
                            </div>
                            <div class="col-6 text-center">
                                <i class="bi bi-file-earmark-arrow-down feature-icon d-block mb-2"></i>
                                <h6>多格式导出</h6>
                                <p class="text-muted small mb-0">CSV、APKG、学习指南格式</p>
                            </div>
                            <div class="col-6 text-center">
                                <i class="bi bi-gear feature-icon d-block mb-2"></i>
                                <h6>灵活配置</h6>
                                <p class="text-muted small mb-0">支持多种大模型和参数调整</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- How to Use -->
                <div class="card mb-4">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0"><i class="bi bi-play-circle"></i> 使用步骤</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <div class="d-flex align-items-start">
                                    <span class="badge bg-primary rounded-pill me-2" style="width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">1</span>
                                    <div>
                                        <h6 class="mb-1">安装依赖</h6>
                                        <p class="text-muted mb-0">pip install -r requirements.txt</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <div class="d-flex align-items-start">
                                    <span class="badge bg-primary rounded-pill me-2" style="width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">2</span>
                                    <div>
                                        <h6 class="mb-1">配置API密钥</h6>
                                        <p class="text-muted mb-0">编辑 config.yaml 文件设置API密钥</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <div class="d-flex align-items-start">
                                    <span class="badge bg-primary rounded-pill me-2" style="width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">3</span>
                                    <div>
                                        <h6 class="mb-1">启动Web应用</h6>
                                        <p class="text-muted mb-0">python web/app.py (完整版) 或 python demo.py (CLI版)</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <div class="d-flex align-items-start">
                                    <span class="badge bg-primary rounded-pill me-2" style="width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">4</span>
                                    <div>
                                        <h6 class="mb-1">开始使用</h6>
                                        <p class="text-muted mb-0">在浏览器中访问 http://localhost:5000</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Demo -->
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5 class="mb-0"><i class="bi bi-eye"></i> 功能演示</h5>
                    </div>
                    <div class="card-body text-center">
                        <div class="upload-area mb-3">
                            <i class="bi bi-cloud-upload fs-1 text-muted"></i>
                            <p class="text-muted mt-2 mb-3">拖拽文件到此处或点击选择</p>
                            <button class="btn btn-outline-primary">
                                <i class="bi bi-folder2-open"></i> 浏览文件
                            </button>
                        </div>
                        <button class="btn btn-primary btn-lg w-100 mb-3">
                            <i class="bi bi-play-circle"></i> 模拟生成演示
                        </button>
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle"></i>
                            <strong>注意:</strong> 这是简化演示版本。完整功能请使用命令行界面或完整的Web应用。
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-lg-4">
                <!-- Stats -->
                <div class="card mb-4">
                    <div class="card-header bg-warning text-white">
                        <h5 class="mb-0"><i class="bi bi-graph-up"></i> 项目统计</h5>
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-6 border-end">
                                <small class="text-muted">Python文件</small>
                                <div class="fw-bold">15+</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">功能模块</small>
                                <div class="fw-bold">6+</div>
                            </div>
                        </div>
                        <hr>
                        <div class="row text-center">
                            <div class="col-6 border-end">
                                <small class="text-muted">支持格式</small>
                                <div class="fw-bold">3</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">大模型</small>
                                <div class="fw-bold">2+</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Card Structure -->
                <div class="card mb-4">
                    <div class="card-header bg-secondary text-white">
                        <h5 class="mb-0"><i class="bi bi-card-text"></i> 卡片结构</h5>
                    </div>
                    <div class="card-body">
                        <div class="list-group list-group-flush">
                            <div class="list-group-item">
                                <i class="bi bi-spellcheck text-primary me-2"></i>
                                单词拼写 + 音标
                            </div>
                            <div class="list-group-item">
                                <i class="bi bi-tag text-info me-2"></i>
                                词性标注
                            </div>
                            <div class="list-group-item">
                                <i class="bi bi-translate text-success me-2"></i>
                                中文释义
                            </div>
                            <div class="list-group-item">
                                <i class="bi bi-lightbulb text-warning me-2"></i>
                                记忆技巧
                            </div>
                            <div class="list-group-item">
                                <i class="bi bi-chat-quote text-danger me-2"></i>
                                例句(3个)
                            </div>
                            <div class="list-group-item">
                                <i class="bi bi-arrows-angle-expand text-secondary me-2"></i>
                                同义词(3个)
                            </div>
                            <div class="list-group-item">
                                <i class="bi bi-exclamation-triangle text-dark me-2"></i>
                                易混淆词(2个)
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Links -->
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="bi bi-box-arrow-right"></i> 快速链接</h6>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <a href="https://github.com" class="btn btn-outline-primary btn-sm">
                                <i class="bi bi-github"></i> GitHub
                            </a>
                            <a href="#" class="btn btn-outline-success btn-sm">
                                <i class="bi bi-file-text"></i> 使用说明
                            </a>
                            <a href="#" class="btn btn-outline-info btn-sm">
                                <i class="bi bi-question-circle"></i> 帮助
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-light text-center py-3 mt-5">
        <div class="container">
            <p class="text-muted mb-0">
                <i class="bi bi-heart-fill text-danger"></i> Anki单词卡片生成器 v1.0 - Web界面演示
            </p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
            ''')
        elif self.path.startswith('/static/'):
            # 处理静态文件
            file_path = self.path[1:]  # 移除/
            if file_path.endswith('.css'):
                self.send_css_response('/* Demo CSS */')
            elif file_path.endswith('.js'):
                self.send_js_response('// Demo JavaScript')
            else:
                self.send_json_response({'message': 'Demo file not found'})
        else:
            self.send_html_response('''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>页面未找到</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="bi bi-emoji-frown text-danger" style="font-size: 4rem;"></i>
                        <h4 class="mt-3">404 - 页面未找到</h4>
                        <a href="/" class="btn btn-primary mt-3">
                            <i class="bi bi-house-door"></i> 返回首页
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
            ''', 404)

    def do_POST(self):
        """处理POST请求（简化版，只是演示）"""
        if self.path == '/api/generate':
            # 解析表单数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')

            # 模拟生成响应
            response_data = {
                'success': True,
                'message': '演示：模拟生成成功',
                'data': {
                    'generated_cards': 3,
                    'words_processed': ['apple', 'banana', 'orange']
                }
            }

            self.send_json_response(response_data)
        else:
            self.send_json_response({'success': False, 'error': '未知的API路径'}, 404)

    def send_html_response(self, content, status_code=200):
        """发送HTML响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def send_css_response(self, content):
        """发送CSS响应"""
        self.send_response(200)
        self.send_header('Content-type', 'text/css; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def send_js_response(self, content):
        """发送JavaScript响应"""
        self.send_response(200)
        self.send_header('Content-type', 'application/javascript; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))

    def log_message(self, format, *args):
        """日志消息"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_server():
    """启动HTTP服务器"""
    port = 8000
    server = HTTPServer(('localhost', port), AnkiCardHandler)

    print("🚀 Anki单词卡片生成器 - Web界面演示")
    print(f"📍 访问地址: http://localhost:{port}")
    print("📖 按 Ctrl+C 停止服务器")
    print("🎯 这是简化演示版本，完整功能请使用命令行界面")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        server.server_close()

if __name__ == '__main__':
    run_server()