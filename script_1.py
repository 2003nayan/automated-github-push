# Generate requirements.txt
requirements_content = """# Core dependencies
watchdog>=3.0.0
PyYAML>=6.0
click>=8.0.0
requests>=2.28.0
GitPython>=3.1.30

# Development dependencies
pytest>=7.0.0
black>=22.0.0
flake8>=5.0.0

# Optional dependencies for enhanced features
colorama>=0.4.6  # Colored terminal output
rich>=13.0.0     # Rich terminal formatting
"""

with open("requirements.txt", "w") as f:
    f.write(requirements_content)

print("✅ Generated requirements.txt")