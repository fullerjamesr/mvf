from setuptools import setup
from glob import glob

setup(
    name='mvf',
    version='0.1',
    packages=['mvf_app'],
    scripts=glob('scripts/*'),
    include_package_data=True,
    url='https://github.com/fullerjamesr/mvf',
    license='AGPL-3.0',
    author='James',
    author_email='fullerjamesr@gmail.com',
    description='A Relion ver3.1 preprocessing loop and web server display',
    install_requires=['dash', 'plotly', 'cryoemtools', 'pillow', 'mrcfile']
)
