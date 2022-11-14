# Standard library imports.
import argparse
import json
import logging
import os
import re
import sys
from os.path import dirname
from typing import Union

# Third party imports.
from dotenv import load_dotenv
from music_bot.client import PuckBotClient


########################################################################################
#                              Function definitions.                                   #
########################################################################################
def add_logging_level(
    level_name: str, level_num: int, method_name: Union[str, None] = None
) -> None:
    """
    This method was "borrowed" from a stack overflow answer:
    https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/35804945#35804945

    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    Args:
        level_name (str): Custom logging level name.
        level_num (int): Custom logging level value.
        method_name (Union[str, None], optional): Name of the method to invoke to use
            the custom level. Defaults to None.

    Raises:
        AttributeError: Raised if logging module already has the provided level name.
        AttributeError: Raised if logging module already has the provided method name.
        AttributeError: Raised if logger class module already has the provided method name.
    """
    if not method_name:
        method_name = level_name.lower()

    if hasattr(logging, level_name):
        raise AttributeError(f"{level_name} already defined in logging module")
    if hasattr(logging, method_name):
        raise AttributeError(f"{method_name} already defined in logging module")
    if hasattr(logging.getLoggerClass(), method_name):
        raise AttributeError(f"{method_name} already defined in logger class")

    def log_for_level(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    def log_to_root(message, *args, **kwargs):
        logging.log(level_num, message, *args, **kwargs)

    logging.addLevelName(level_num, level_name)
    setattr(logging, level_name, level_num)
    setattr(logging.getLoggerClass(), method_name, log_for_level)
    setattr(logging, method_name, log_to_root)


########################################################################################
def get_config(args: argparse.Namespace) -> dict:
    """Generate the configuration for the bot.

    Args:
        args (argparse.Namespace): Script arguments object.

    Returns:
        dict: Bot config dict.
    """
    with open(
        file=args.config,
        mode="r",
        encoding="utf-8",
    ) as cfg:
        try:
            config = json.loads(cfg.read())

        except Exception as err:
            sys.exit(f"ERROR: Problem loading config file as json : {err}")

    # Validate all required items are present in the config file.
    for item in ("api_service_name", "api_version", "command_prefix", "log_level"):
        if item not in config:
            sys.exit(f'ERROR: Configuration key "{item}" missing from config file!!')

    # Load all environment variables from local .env file.
    load_dotenv(args.env)
    channel_id = str(os.getenv("CHANNEL_ID"))
    developer_key = str(os.getenv("GOOGLE_API_TOKEN"))
    guild = str(os.getenv("DISCORD_GUILD"))
    token = str(os.getenv("DISCORD_TOKEN"))

    # Validate all necessary variables are present in the .env file.
    if channel_id is None:
        sys.exit("ERROR: CHANNEL_ID missing from .env file.")

    if developer_key is None:
        sys.exit("ERROR: GOOGLE_API_TOKEN missing from .env file.")

    if guild is None:
        sys.exit("ERROR: DISCORD_GUILD missing from .env file.")

    if token is None:
        sys.exit("ERROR: DISCORD_TOKEN missing from .env file.")

    return {
        **config,
        "channel_id": channel_id,
        "developer_key": developer_key,
        "guild": guild,
        "token": token,
    }


########################################################################################
def init_argparse() -> argparse.ArgumentParser:
    """Initialize arg parser.

    Returns:
        argparse.ArgumentParser: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] [FILE]...",
        description="Puck's magical Discord music bot.",
    )

    # Default all file args to ones in root directory of project.
    parser.add_argument(
        "-c",
        "--config",
        default=f"{dirname(__file__)}/../../config.json",
        help="Script configuration JSON file.",
    )

    parser.add_argument(
        "-e",
        "--env",
        default=f"{dirname(__file__)}/../../.env",
        help="Script dotenv file.",
    )

    parser.add_argument(
        "-l",
        "--log_level",
        default="info",
        help="Set logging level for the script.",
        type=validate_log_level,
    )

    return parser


########################################################################################
async def load_extensions(bot: PuckBotClient, cog_path: str) -> None:
    """Load all cogs into the bot.

    Args:
        bot (PuckBotClient): Bot client.
        cog_path (str): Path to all cogs.
    """
    bot.logger.info("Loading extensions:")
    for filename in os.listdir(cog_path):
        if filename == "__init__.py":
            continue

        if filename.endswith(".py"):
            # cut off the .py from the file name
            bot.logger.info(f"  ...loading cog : {filename}")
            cog_package = cog_path[2:].replace("/", ".")
            await bot.load_extension(f"{cog_package}.{filename[:-3]}")


########################################################################################
def pretty_dict(ugly_dict: str) -> str:
    """Format a dict nicely for logging purposes.

    Args:
        ugly_dict (str): The ugly dict.

    Returns:
        str: The pretty dict.
    """
    try:
        value = json.dumps(json.loads(ugly_dict), indent=4, sort_keys=True)
    except Exception:
        value = ugly_dict

    return value


########################################################################################
def validate_log_level(value: str) -> int:
    """Validate the provided log level.

    Args:
        value (str): Log level in string format.

    Raises:
        argparse.ArgumentTypeError: Raised when invalid level provided.

    Returns:
        int: Log level integer value.
    """
    levels = {
        "critical": logging.CRITICAL,
        "debug": logging.DEBUG,
        "error": logging.ERROR,
        "info": logging.INFO,
        "warn": logging.WARNING,
    }

    if not re.match("^(critical|debug|error|info|warn)$", value, re.IGNORECASE):
        raise argparse.ArgumentTypeError(
            "log_level be one of the following: critical|debug|error|info|warn"
        )

    return levels[value.lower()]
