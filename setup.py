from setuptools import setup, find_packages

setup(
    name="beeperpurge",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "beeperpurge=beeperpurge.cleaner:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "pytest-mock",
        ],
    },
)