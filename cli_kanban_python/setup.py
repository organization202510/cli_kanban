"""Setup configuration for CLI Kanban."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cli-kanban",
    version="1.0.0",
    author="CLI Kanban Contributors",
    description="A terminal-based Kanban board management tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/happytaoer/cli_kanban",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cli_kanban=main:main",
        ],
    },
)
