"""
Setup script for Anki Word Card Generator
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="anki-word-card-generator",
    version="1.0.0",
    author="Anki Card Generator Team",
    author_email="your-email@example.com",
    description="基于大模型的Anki单词卡片批量生成工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/anki-word-card-generator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Education",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "anki-gen=cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt", "*.md"],
    },
    keywords="anki vocabulary english learning ai generator",
    project_urls={
        "Bug Reports": "https://github.com/your-username/anki-word-card-generator/issues",
        "Source": "https://github.com/your-username/anki-word-card-generator",
        "Documentation": "https://github.com/your-username/anki-word-card-generator#readme",
    },
)