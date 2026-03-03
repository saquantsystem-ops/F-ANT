from setuptools import setup, find_packages

# also change in version.py
VERSION = "1.12.0"
DESCRIPTION = "A trading framework for cryptocurrencies"
with open("requirements.txt", "r", encoding="utf-8") as f:
    REQUIRED_PACKAGES = f.read().splitlines()

with open("README.md", "r", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='F-Antigravity',
    version=VERSION,
    author="Antigravity",
    author_email="antigravity@example.com",
    packages=find_packages(),
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/generic/f-antigravity",
    project_urls={
        'Source': 'https://github.com/generic/f-antigravity',
    },
    install_requires=REQUIRED_PACKAGES,
    entry_points='''
        [console_scripts]
        jesse=jesse.__init__:cli
    ''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    include_package_data=True,
    package_data={
        '': ['*.dll', '*.dylib', '*.so', '*.json'],
    },
)
