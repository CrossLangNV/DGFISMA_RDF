from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

with open('docker/requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='RDF for DGFISMA',
    version='0.1',
    description='Module for exporting reporting obligations and glossary to RDF.',
    # license="MIT",
    long_description=long_description,
    author='Laurens Meeus',
    author_email='laurens.meeus@crosslang.com',
    url="http://www.crosslang.com/",
    packages=[], #'dgfisma_rdf', ],  # 'concepts', 'reporting_obligations'],  # same as name
    install_requires=required,  # external packages as dependencies
    # scripts=[
    #          'scripts/cool',
    #          'scripts/skype',
    #         ]
)
