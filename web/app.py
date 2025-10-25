"""
Flask Web应用 - Anki单词卡片生成器
"""

import os
import json
import time
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# 添加项目根目录到系统路径
import sys
sys.path.append(str(Path(__file__).parent.parent))

# 使用绝对导入
try:
    from config.config_parser import ConfigParser
    from data.builtin_dict import BuiltinDictionary
    from data.word_importer import WordImporter
    from core.word_generator import WordCardGenerator
    from core.data_validator import DataValidator
    from export.csv_exporter import CSVExporter
    from export.anki_exporter import AnkiExporter
    from data.models import ExportSettings
    from utils.logger import get_logger
    from utils.exceptions import AnkiCardGeneratorError, ImportError, LLMError, ExportError
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保项目结构正确，并已安装所需依赖")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# 全局变量
config = None
builtin_dict = None
word_generator = None
data_validator = None
word_importer = None
csv_exporter = None
anki_exporter = None
generation_progress = {}

# 配置文件上传
UPLOAD_FOLDER = 'web/static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'json'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

logger = get_logger(__name__)

def initialize_app():
    """初始化应用"""
    global config, builtin_dict, word_generator, data_validator, word_importer, csv_exporter, anki_exporter

    try:
        # 加载配置
        config = ConfigParser('config.yaml')

        # 初始化日志
        logging_config = config.get_logging_config()
        logger.setup_logger(
            level=logging_config.get('level', 'INFO'),
            log_file=logging_config.get('file')
        )

        # 初始化组件
        builtin_dict = BuiltinDictionary(config.get('dict_settings.builtin_dict_path'))
        word_generator = WordCardGenerator(
            config.get_llm_config(),
            config.get_batch_settings()
        )
        data_validator = DataValidator()
        word_importer = WordImporter()

        logger.info("Web应用初始化成功")
        return True

    except Exception as e:
        logger.error(f"Web应用初始化失败: {e}")
        return False

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """主页"""
    try:
        # 获取内置词库统计
        builtin_stats = builtin_dict.get_statistics()
        return render_template('index.html', stats=builtin_stats)
    except Exception as e:
        logger.error(f"主页加载失败: {e}")
        return render_template('index.html', error=str(e))

@app.route('/api/stats')
def api_stats():
    """获取统计信息"""
    try:
        builtin_stats = builtin_dict.get_statistics()
        return jsonify({
            'success': True,
            'data': builtin_stats
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/words/builtin')
def api_builtin_words():
    """获取内置词库单词"""
    try:
        category = request.args.get('category')
        difficulty = request.args.get('difficulty')
        count = int(request.args.get('count', 10))
        random_selection = request.args.get('random', 'false').lower() == 'true'

        if random_selection:
            words = builtin_dict.get_random_words(count)
        elif category:
            words = builtin_dict.get_words_by_category(category)[:count]
        elif difficulty:
            words = builtin_dict.get_words_by_difficulty(difficulty)[:count]
        else:
            words = builtin_dict.get_all_words()[:count]

        return jsonify({
            'success': True,
            'data': {
                'words': words,
                'total': len(words)
            }
        })
    except Exception as e:
        logger.error(f"获取内置词库失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/words/generate', methods=['POST'])
def api_generate_words():
    """生成单词卡片"""
    try:
        data = request.get_json()
        words = data.get('words', [])
        preview = data.get('preview', False)

        if not words:
            return jsonify({
                'success': False,
                'error': '没有提供单词'
            })

        # 验证单词列表
        words = word_generator.validate_word_list(words)

        if preview:
            # 预览生成
            rules = config.get_generation_rules()
            preview_result = word_generator.preview_generation(words[:3], rules)
            return jsonify({
                'success': True,
                'preview': True,
                'data': preview_result
            })
        else:
            # 实际生成
            return jsonify({
                'success': True,
                'preview': False,
                'task_id': str(int(time.time())),
                'message': '生成任务已开始'
            })

    except Exception as e:
        logger.error(f"生成单词卡片失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/progress/<task_id>')
def api_progress(task_id):
    """获取生成进度"""
    try:
        progress = generation_progress.get(task_id, {
            'current': 0,
            'total': 0,
            'status': 'pending'
        })
        return jsonify({
            'success': True,
            'data': progress
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/upload', methods=['POST'])
def api_upload_file():
    """上传词库文件"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有文件'
            })

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            })

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = Path(app.config['UPLOAD_FOLDER']) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            file.save(str(filepath))

            # 预览文件内容
            preview_data = word_importer.preview_file(str(filepath))
            return jsonify({
                'success': True,
                'data': {
                    'filename': filename,
                    'filepath': str(filepath),
                    'preview': preview_data
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': '不支持的文件格式'
            })

    except RequestEntityTooLarge:
        return jsonify({
            'success': False,
            'error': '文件太大，请选择小于16MB的文件'
        })
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/export/<export_format>', methods=['POST'])
def api_export(export_format):
    """导出单词卡片"""
    try:
        data = request.get_json()
        cards_data = data.get('cards', [])

        # 验证卡片数据
        validated_cards = []
        for card_data in cards_data:
            try:
                card = data_validator.validate_word_card(card_data, strict=False)
                if card:
                    validated_cards.append(card)
            except Exception as e:
                logger.warning(f"卡片数据验证失败: {e}")

        if not validated_cards:
            return jsonify({
                'success': False,
                'error': '没有有效的卡片数据'
            })

        # 创建导出设置
        export_settings = ExportSettings(
            format=export_format,
            deck_name=config.get('export_settings.deck_name'),
            deck_description=config.get('export_settings.deck_description'),
            csv_delimiter=config.get('export_settings.csv_delimiter', ',')
        )

        # 生成时间戳文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        if export_format == 'csv':
            csv_exporter = CSVExporter(export_settings)
            output_path = csv_exporter.export_cards(validated_cards)
            return send_file(output_path, as_attachment=True, download_name=f'anki_cards_{timestamp}.csv')
        elif export_format == 'apkg':
            anki_exporter = AnkiExporter(export_settings)
            output_path = anki_exporter.export_cards(validated_cards)
            return send_file(output_path, as_attachment=True, download_name=f'anki_deck_{timestamp}.apkg')
        elif export_format == 'study':
            csv_exporter = CSVExporter(export_settings)
            output_path = csv_exporter.export_study_guide(validated_cards)
            return send_file(output_path, as_attachment=True, download_name=f'study_guide_{timestamp}.csv')
        else:
            return jsonify({
                'success': False,
                'error': '不支持的导出格式'
            })

    except Exception as e:
        logger.error(f"导出失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/config')
def api_config():
    """获取配置信息"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'llm_config': {
                    'provider': config.get('llm_config.provider'),
                    'model': config.get('llm_config.model'),
                    'available_providers': ['openai', 'anthropic']
                },
                'generation_rules': config.get_generation_rules(),
                'supported_formats': ['csv', 'apkg', 'study']
            }
        })
    except Exception as e:
        logger.error(f"获取配置信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"内部服务器错误: {error}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    # 初始化应用
    if initialize_app():
        print("🚀 Web应用启动成功！")
        print("📍 访问地址: http://localhost:5000")
        print("📖 按 Ctrl+C 停止服务器")

        # 创建必要的目录
        Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(exist_ok=True)

        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Web应用初始化失败，请检查配置")