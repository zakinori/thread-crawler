from setuptools import setup, find_packages

setup(
    name="thread-crawler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "scrapy>=2.5.0",
        "python-dotenv>=0.19.0",
        "pytz>=2021.1",
        "beautifulsoup4>=4.9.3",
        "pandas>=1.3.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.22.0",
    ],
    description="スレッドクローラー",
    keywords="crawler, scrapy",
    python_requires=">=3.8",
)