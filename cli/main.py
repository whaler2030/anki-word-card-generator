"""
命令行界面主入口
"""

import click
import sys
from pathlib import Path
from typing import List, Optional
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent))

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

logger = get_logger(__name__)

class AnkiCardGeneratorCLI:
    """Anki单词卡片生成器CLI"""

    def __init__(self):
        self.config = None
        self.builtin_dict = None
        self.word_generator = None
        self.data_validator = None
        self.word_importer = None
        self.csv_exporter = None
        self.anki_exporter = None

    def initialize(self, config_path: str = "config.yaml"):
        """初始化系统"""
        try:
            click.echo(f"{Fore.CYAN}正在初始化Anki单词卡片生成器...{Style.RESET_ALL}")

            # 加载配置
            self.config = ConfigParser(config_path)

            # 初始化日志
            logging_config = self.config.get_logging_config()
            logger.setup_logger(
                level=logging_config.get('level', 'INFO'),
                log_file=logging_config.get('file')
            )

            # 初始化组件
            self.builtin_dict = BuiltinDictionary(self.config.get('dict_settings.builtin_dict_path'))
            self.word_generator = WordCardGenerator(
                self.config.get_llm_config(),
                self.config.get_batch_settings()
            )
            self.data_validator = DataValidator()
            self.word_importer = WordImporter()

            click.echo(f"{Fore.GREEN}✓ 系统初始化完成{Style.RESET_ALL}")

        except Exception as e:
            click.echo(f"{Fore.RED}✗ 系统初始化失败: {e}{Style.RESET_ALL}")
            sys.exit(1)

    def display_banner(self):
        """显示欢迎横幅"""
        banner = f"""
{Fore.CYAN}
╔══════════════════════════════════════════════════════════════╗
║                   Anki 单词卡片生成器                         ║
║                Anki Word Card Generator                       ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
        """
        click.echo(banner)

    def display_word_sources(self):
        """显示单词来源信息"""
        builtin_stats = self.builtin_dict.get_statistics()
        click.echo(f"\n{Fore.YELLOW}📚 词库信息:{Style.RESET_ALL}")
        click.echo(f"  内置词库: {builtin_stats['total_words']} 个单词")
        click.echo(f"  支持的格式: TXT, CSV, JSON")
        click.echo(f"  词库路径: {self.config.get('dict_settings.builtin_dict_path')}")

    def display_config_info(self):
        """显示配置信息"""
        llm_config = self.config.get_llm_config()
        click.echo(f"\n{Fore.YELLOW}⚙️ 配置信息:{Style.RESET_ALL}")
        click.echo(f"  LLM提供商: {llm_config.get('provider', '未知')}")
        click.echo(f"  模型: {llm_config.get('model', '未知')}")
        click.echo(f"  批处理大小: {self.config.get('batch_settings.batch_size', 5)}")
        click.echo(f"  重试次数: {self.config.get('batch_settings.retry_count', 3)}")

@click.group()
@click.option('--config', '-c', default='config.yaml', help='配置文件路径')
@click.pass_context
def cli(ctx, config):
    """Anki单词卡片生成器 - 基于大模型的智能英语学习卡片工具"""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config

@cli.command()
@click.pass_context
def init(ctx):
    """初始化系统并显示欢迎信息"""
    app = AnkiCardGeneratorCLI()
    app.initialize(ctx.obj['config_path'])
    app.display_banner()
    app.display_word_sources()
    app.display_config_info()

@cli.command()
@click.option('--count', '-n', default=10, help='选择的单词数量')
@click.option('--category', '-c', help='按分类选择')
@click.option('--difficulty', '-d', help='按难度选择 (easy/medium/hard)')
@click.option('--random', '-r', is_flag=True, help='随机选择')
@click.pass_context
def builtin(ctx, count, category, difficulty, random):
    """使用内置词库生成单词卡片"""
    app = AnkiCardGeneratorCLI()
    app.initialize(ctx.obj['config_path'])

    try:
        # 获取单词列表
        if category:
            words = app.builtin_dict.get_words_by_category(category)
        elif difficulty:
            words = app.builtin_dict.get_words_by_difficulty(difficulty)
        elif random:
            words = app.builtin_dict.get_random_words(count)
        else:
            words = app.builtin_dict.get_all_words()[:count]

        if not words:
            click.echo(f"{Fore.RED}✗ 没有找到符合条件的单词{Style.RESET_ALL}")
            return

        words = words[:count]
        click.echo(f"{Fore.GREEN}📝 选择了 {len(words)} 个单词{Style.RESET_ALL}")

        # 生成单词卡片
        click.echo(f"\n{Fore.CYAN}🚀 开始生成单词卡片...{Style.RESET_ALL}")
        rules = app.config.get_generation_rules()
        result = app.word_generator.generate_batch_cards(words, rules)

        # 显示生成结果
        click.echo(f"\n{Fore.GREEN}✓ 生成完成:{Style.RESET_ALL}")
        click.echo(f"  总计: {result.total_words} 个单词")
        click.echo(f"  成功: {result.success_count} 个")
        click.echo(f"  失败: {result.failed_count} 个")

        if result.failed_count > 0:
            click.echo(f"\n{Fore.YELLOW}⚠️ 失败的单词:{Style.RESET_ALL}")
            for r in result.results:
                if not r.success:
                    click.echo(f"  {r.word}: {r.error_message}")

        # 导出结果
        if result.success_count > 0:
            export_format = click.confirm(f"\n{Fore.YELLOW}是否导出生成的单词卡片?{Style.RESET_ALL}")
            if export_format:
                export_cards(app, [r.card_data for r in result.results if r.success])

    except Exception as e:
        click.echo(f"{Fore.RED}✗ 生成失败: {e}{Style.RESET_ALL}")

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--format', '-f', help='文件格式 (txt/csv/json)')
@click.pass_context
def import_words(ctx, file_path, format):
    """导入外部词库文件"""
    app = AnkiCardGeneratorCLI()
    app.initialize(ctx.obj['config_path'])

    try:
        # 导入词库
        click.echo(f"\n{Fore.CYAN}📂 正在导入词库文件...{Style.RESET_ALL}")
        word_source = app.word_importer.import_words(file_path, format)
        click.echo(f"{Fore.GREEN}✓ 导入成功: {word_source.word_count} 个单词{Style.RESET_ALL}")

        # 询问是否生成卡片
        if click.confirm(f"\n{Fore.YELLOW}是否生成这些单词的卡片?{Style.RESET_ALL}"):
            # 这里可以复用生成逻辑
            pass

    except Exception as e:
        click.echo(f"{Fore.RED}✗ 导入失败: {e}{Style.RESET_ALL}")

@cli.command()
@click.argument('words', nargs=-1, required=True)
@click.pass_context
def generate(ctx, words):
    """生成指定单词的卡片"""
    app = AnkiCardGeneratorCLI()
    app.initialize(ctx.obj['config_path'])

    try:
        words = list(words)
        click.echo(f"{Fore.GREEN}📝 将生成 {len(words)} 个单词的卡片{Style.RESET_ALL}")

        # 生成单词卡片
        click.echo(f"\n{Fore.CYAN}🚀 开始生成单词卡片...{Style.RESET_ALL}")
        rules = app.config.get_generation_rules()
        result = app.word_generator.generate_batch_cards(words, rules)

        # 显示生成结果
        click.echo(f"\n{Fore.GREEN}✓ 生成完成:{Style.RESET_ALL}")
        click.echo(f"  总计: {result.total_words} 个单词")
        click.echo(f"  成功: {result.success_count} 个")
        click.echo(f"  失败: {result.failed_count} 个")

        # 导出结果
        if result.success_count > 0:
            export_cards(app, [r.card_data for r in result.results if r.success])

    except Exception as e:
        click.echo(f"{Fore.RED}✗ 生成失败: {e}{Style.RESET_ALL}")

def export_cards(app: AnkiCardGeneratorCLI, cards: List):
    """导出单词卡片"""
    if not cards:
        return

    # 选择导出格式
    click.echo(f"\n{Fore.YELLOW}📤 选择导出格式:{Style.RESET_ALL}")
    click.echo("  1. CSV格式 (Anki标准)")
    click.echo("  2. CSV格式 (简化)")
    click.echo("  3. APKG格式 (Anki牌组)")
    click.echo("  4. 学习指南")

    choice = click.prompt("请选择", type=int, default=1)

    export_settings = ExportSettings(
        format="csv",
        deck_name=app.config.get('export_settings.deck_name'),
        deck_description=app.config.get('export_settings.deck_description'),
        csv_delimiter=app.config.get('export_settings.csv_delimiter', ',')
    )

    try:
        if choice == 1:
            app.csv_exporter = CSVExporter(export_settings)
            output_path = app.csv_exporter.export_cards(cards)
            click.echo(f"{Fore.GREEN}✓ CSV文件已导出: {output_path}{Style.RESET_ALL}")
        elif choice == 2:
            app.csv_exporter = CSVExporter(export_settings)
            output_path = app.csv_exporter.export_simple_format(cards)
            click.echo(f"{Fore.GREEN}✓ 简化CSV文件已导出: {output_path}{Style.RESET_ALL}")
        elif choice == 3:
            app.anki_exporter = AnkiExporter(export_settings)
            output_path = app.anki_exporter.export_cards(cards)
            click.echo(f"{Fore.GREEN}✓ APKG文件已导出: {output_path}{Style.RESET_ALL}")
        elif choice == 4:
            app.csv_exporter = CSVExporter(export_settings)
            output_path = app.csv_exporter.export_study_guide(cards)
            click.echo(f"{Fore.GREEN}✓ 学习指南已导出: {output_path}{Style.RESET_ALL}")

    except Exception as e:
        click.echo(f"{Fore.RED}✗ 导出失败: {e}{Style.RESET_ALL}")

@cli.command()
@click.pass_context
def stats(ctx):
    """显示统计信息"""
    app = AnkiCardGeneratorCLI()
    app.initialize(ctx.obj['config_path'])

    try:
        # 显示内置词库统计
        builtin_stats = app.builtin_dict.get_statistics()
        click.echo(f"\n{Fore.YELLOW}📊 内置词库统计:{Style.RESET_ALL}")
        click.echo(f"  总单词数: {builtin_stats['total_words']}")
        click.echo(f"  分类数: {len(builtin_stats['categories'])}")

        click.echo(f"\n{Fore.CYAN}难度分布:{Style.RESET_ALL}")
        for difficulty, count in builtin_stats['difficulty_distribution'].items():
            click.echo(f"  {difficulty}: {count}")

        click.echo(f"\n{Fore.CYAN}分类分布:{Style.RESET_ALL}")
        for category, count in builtin_stats['category_distribution'].items():
            click.echo(f"  {category}: {count}")

    except Exception as e:
        click.echo(f"{Fore.RED}✗ 获取统计信息失败: {e}{Style.RESET_ALL}")

@cli.command()
@click.pass_context
def config_info(ctx):
    """显示配置信息"""
    app = AnkiCardGeneratorCLI()
    app.initialize(ctx.obj['config_path'])

    app.display_config_info()

if __name__ == '__main__':
    cli()