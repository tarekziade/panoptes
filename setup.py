import sys
from setuptools import setup, find_packages


install_requires = ["async_generator", "scipy", "matplotlib", "pyqt5"]
description = ""

setup(
    name="panoptes",
    version="0.1.",
    packages=find_packages(),
    author="Tarek Ziade",
    author_email="tarek@ziade.org",
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
)
