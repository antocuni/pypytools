#   Copyright 2015 Antonio Cuni anto.cuni@gmail.com

from setuptools import setup

desc = "A collection of useful tools to use PyPy-specific features, with CPython fallbacks"


setup(
    name="pypytools",
    version="0.3.3",
    author="Antonio Cuni",
    author_email="anto.cuni@gmail.com",
    url="http://bitbucket.org/antocuni/pypytools/",
    license="MIT X11 style",
    description=desc,
    packages=["pypytools"],
    long_description=desc,
    install_requires=["py"],
)
