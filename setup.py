from setuptools import setup, find_packages
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='naming',
    version='1.0.0',
    description='Naming conventions library',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://gitlab.com/arcanepipeline/naming-conventions',
    author='Cesar Saez, Chris Granados- Xian',
    author_email='info@chrisgranados.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7'
    ],
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',
    extras_require={
        'dev': ['pytest', 'pytest-cov', 'pytest-datafiles', 'flake8']
    }
)