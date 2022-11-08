# Standard library imports.
import os
import sys
from os.path import dirname

# Third party imports.
from dotenv import load_dotenv
from music_bot.client import PuckBotClient


########################################################################################
#                              Function definitions.                                   #
########################################################################################
def get_config(env_file: str) -> dict:
    # Load all environment variables from local .env file.
    load_dotenv(env_file)
    token = str(os.getenv("DISCORD_TOKEN"))
    guild = str(os.getenv("DISCORD_GUILD"))
    developer_key = str(os.getenv("GOOGLE_API_TOKEN"))

    # Validate all necessary variables are present.
    if not token:
        sys.exit("DISCORD_TOKEN missing from .env file.")

    if not guild:
        sys.exit("DISCORD_GUILD missing from .env file.")

    if not developer_key:
        sys.exit("GOOGLE_API_TOKEN missing from .env file.")

    return {
        "command_prefix": "/",
        "log_level": "DEBUG",
        # Environment variables.
        "developer_key": developer_key,
        "guild": guild,
        "token": token,
        # YouTube API information.
        "api_service_name": "youtube",
        "api_version": "v3",
    }


########################################################################################
async def load_extensions(bot: PuckBotClient, cog_path: str) -> None:
    bot.logger.info("Loading extensions:")
    for filename in os.listdir(cog_path):
        if filename == "__init__.py":
            continue

        if filename.endswith(".py"):
            # cut off the .py from the file name
            bot.logger.info(f"  ...loading cog : {filename}")
            cog_package = cog_path[2:].replace("/", ".")
            await bot.load_extension(f"{cog_package}.{filename[:-3]}")
