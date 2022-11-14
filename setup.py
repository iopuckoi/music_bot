# Standard library imports.
import re

# Third party imports.
from setuptools import (
    find_packages,
    setup,
)


def find_version(version_file: str) -> str:
    """Attempt to locate package version.

    Args:
        version_file (str): Path to version file.

    Raises:
        RuntimeError: Raised if unable to find version string.

    Returns:
        str: Package version.
    """
    regex = r"^__version__ = ['\"]([^'\"]*)['\"]"
    with open(
        file=version_file,
        mode="rt",
        encoding="utf-8",
    ) as ver_file:
        version_line = ver_file.read()
        match_object = re.search(regex, version_line, re.M)

        if not match_object:
            raise RuntimeError(f"Unable to find version string in {version_file}")

        return match_object.group(1)


requirements = [
    "discord.py==2.0.1",
    "google-api-python-client==2.63.0",
    "google-auth-oauthlib==0.5.3",
    "google-auth-httplib2==0.1.0",
    "python-dotenv==0.21.0",
    "PyNaCl==1.5.0",
    "youtube_dl==2021.12.17",
]

setup(
    name="music-bot",
    description="Music bot for Discord.",
    packages=find_packages(),
    install_requires=requirements,
    setup_requires=requirements,
    version=find_version("__version__.py"),
)
