from setuptools import setup, find_packages

# Read the contents of your README file (optional)
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="matsolver_db_api",  # Replace with your project's name
    version="0.1.0a",  # Replace with your project's version
    author="Andrey Geondzhiam",  # Replace with your name
    author_email="a.geondzhian@gmail.com",  # Replace with your email
    description="API client for matsolver database",  # Short description
    long_description=long_description,  # Long description from README
    long_description_content_type="text/markdown",  # Type of long description
    url="https://github.com/github.com/geonda/matsolver_db_api",  # Replace with your project's URL
    packages=find_packages(),  # Automatically find packages in the project
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Adjust license as necessary
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',  # Specify the minimum Python version required
    install_requires=[
        "requests",  # List your project's dependencies here
        "numpy",
        'jsonpickle'
        "simplejson",

        # Add other dependencies as needed
    ],
    # entry_points={
    #     'console_scripts': [
    #         'your_command=module:function',  # Replace with your command and function
    #     ],
    # },
)
