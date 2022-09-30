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
    "discord.py==2.01",
    "google-api-python-client==2.63.0",
    "python-dotenv==0.21.0",
]

setup(
    name="music-bot",
    description="Music bot for Discord.",
    packages=find_packages(),
    install_packages=requirements,
    version=find_version("__version__.py"),
)
