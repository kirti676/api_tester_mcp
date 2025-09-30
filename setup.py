from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="api-tester-mcp",
    version="1.2.1",
    author="API Tester MCP",
    author_email="api-tester@example.com",
    description="Multi-language MCP server for API testing with TypeScript/Playwright, JavaScript/Jest, Python/pytest support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/kirti676/api_tester_mcp",
    project_urls={
        "Repository": "https://github.com/kirti676/api_tester_mcp.git",
        "Issues": "https://github.com/kirti676/api_tester_mcp/issues",
        "Changelog": "https://github.com/kirti676/api_tester_mcp/blob/main/CHANGELOG.md",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=0.2.0",
        "pydantic>=2.0.0",
        "jsonschema>=4.0.0",
        "pyyaml>=6.0",
        "jinja2>=3.1.0",
        "aiohttp>=3.8.0",
        "faker>=19.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "api-tester-mcp=api_tester_mcp.server:main",
            "api-tester-mcp-server=api_tester_mcp.server:main",
        ],
    },
    keywords="mcp api-testing swagger openapi postman qa sdet testing model-context-protocol typescript playwright jest pytest multi-language test-generation",
    include_package_data=True,
    package_data={
        "api_tester_mcp": ["*.py"],
    },
)
