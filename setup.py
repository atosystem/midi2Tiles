import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name='midi2Tiles',
    version='1.0.1',
    description='Create synthesia-like piano tiles effect from midi files.',
    long_description=README,
    long_description_content_type="text/markdown",
    author='atosystem',
    author_email='yjshih23@gmail.com',
    url='https://github.com/atosystem/midi2Tiles',
    keywords=['synthesia', 'midi','music','video','animation','matplotlib'],
    install_requires=[
        # Restriction that urllib3's version is less than 1.25 needed to avoid
        # requests dependency problem.
        'urllib3 >= 1.21.1, < 1.25',
        'requests',
        'tqdm',
        'matplotlib',
        'miditoolkit'

    ],
    packages=find_packages(),
    license="MIT")