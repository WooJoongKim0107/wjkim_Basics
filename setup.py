from setuptools import setup, find_packages

setup(
    name = 'wjkim',  # pip list, conda list 시 보이는 이름
    packages = find_packages(),
    python_requires='>=3.9',
    install_requires=[
        'more-itertools',
        'omegaconf',
    ],
)