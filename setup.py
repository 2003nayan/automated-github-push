#!/usr/bin/env python3
"""
Setup script for Code Backup Daemon
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "Automatically backup your code to GitHub"

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, "r") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = [
        "watchdog>=3.0.0",
        "PyYAML>=6.0",
        "click>=8.0.0",
        "requests>=2.28.0",
        "GitPython>=3.1.30",
        "colorama>=0.4.6",
        "rich>=13.0.0"
    ]

setup(
    name="code-backup-daemon",
    version="1.0.0",
    author="Code Backup Daemon",
    author_email="dev@example.com",
    description="Automatically backup your code to GitHub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/code-backup-daemon",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
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
    entry_points={
        "console_scripts": [
            "code-backup=code_backup_daemon.cli:cli",
            "code-backup-daemon=code_backup_daemon.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "code_backup_daemon": [
            "config/*.yaml",
            "config/*.service",
        ],
    },
    zip_safe=False,
)
