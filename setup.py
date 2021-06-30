import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

with open("docker/requirements.txt") as f:
    required = f.read().splitlines()

setuptools.setup(
    name="RDF for DGFISMA",
    version="0.0.1",
    description="Module for exporting reporting obligations and glossary to RDF.",
    # license="MIT",
    long_description=long_description,
    author="Laurens Meeus",
    author_email="laurens.meeus@crosslang.com",
    url="https://github.com/CrossLangNV/DGFISMA_RDF/",
    # packages=['dgfisma_rdf'],  # 'concepts', 'reporting_obligations'],  # same as name
    packages=setuptools.find_packages(),
    install_requires=required,  # external packages as dependencies
    # scripts=[
    #          'scripts/cool',
    #          'scripts/skype',
    #         ]
)
