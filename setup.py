from setuptools import setup, find_packages
import os

# Read the requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read the README.md for long description
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='AI_Talking',
    version='0.3.1',
    description='A chat application for AI discussions and debates',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='NONEAD Corporation',
    author_email='',
    url='',
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'ai_talking = chat_gui:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.12',
)
