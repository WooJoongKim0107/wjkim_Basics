from setuptools import setup, find_packages

setup(
    author='WooJoong Kim',
    author_email='henrik@unist.ac.kr',
    url='https://github.com/WooJoongKim0107/wjkim_Basics',

    name='wjkim',  # pip list, conda list 시 보이는 이름
    version='0.7',
    python_requires='>=3.9',
    packages=find_packages(),
    install_requires=[
        'more-itertools',
        'omegaconf',
        'numpy',
        'matplotlib',
    ],
)
