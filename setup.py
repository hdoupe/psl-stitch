import setuptools
import os

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="psl-stitch",
    version=os.environ.get("VERSION", "0.0.0"),
    author="Hank Doupe",
    author_email="henrymdoupe@gmail.com",
    description=("Connect apps on Compute STudio"),
    long_description="",
    long_description_content_type="text/markdown",
    url="https://github.com/hdoupe/psl-stitch",
    packages=setuptools.find_packages(),
    install_requires=[
        "paramtools",
        "httpx",
        "fastapi[uvicorn]",
        "pydantic",
        "cs-kit @ git+ssh://git@github.com/compute-tooling/compute-studio-kit@async#egg=psl_stitch",
    ],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
