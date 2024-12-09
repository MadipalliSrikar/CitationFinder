# Description: This file is used to install the shared package. It is a simple package that contains the shared models and database connection.
from setuptools import setup, find_packages

setup(
    name="shared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=1.4.41",
        "pydantic>=2.5.2"
    ],
)