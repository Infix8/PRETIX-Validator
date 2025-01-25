import os
from setuptools import setup, find_packages

try:
    with open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()
except:
    long_description = ''

setup(
    name='pretix-rollno-validator',
    version='1.0.0',
    description='Ensures Roll Number uniqueness during ticket purchase in pretix',
    long_description=long_description,
    url='https://github.com/yourusername/pretix-rollno-validator',
    author='Your Name',
    author_email='your.email@example.com',
    license='Apache Software License',
    
    install_requires=[
        'pretix>=4.0.0',  # Minimum pretix version
    ],
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    
    package_data={
        'pretix_rollno_validator': [
            'templates/*/*.html',
            'templates/*/*.txt',
            'locale/*/LC_MESSAGES/*'
        ]
    },
    
    entry_points="""
[pretix.plugin]
pretix_rollno_validator=pretix_rollno_validator:PluginApp
""",
    
    python_requires='>=3.8',  # Match pretix's Python requirement
    
    # Additional metadata
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    
    # Development dependencies
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-django',
            'pytest-cov',
            'coverage',
            'flake8',
            'black',
        ],
    },
) 