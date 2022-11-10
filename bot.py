# Standard library imports.
import asyncio
import logging
import sys

# Third party imports.
import discord
import googleapiclient.discovery
from music_bot.client import PuckBotClient
from music_bot.common.utils import (
    get_config,
    init_argparse,
    load_extensions,
)
from music_bot.formatter import Formatter

# https://medium.com/pythonland/build-a-discord-bot-in-python-that-plays-music-and-send-gifs-856385e605a1


# import requests
# def handler(pd: "pipedream"):
#     token = f'{pd.inputs["youtube_data_api"]["$auth"]["oauth_access_token"]}'
#     authorization = f"Bearer {token}"
#     headers = {"Authorization": authorization}
#     r = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
#     # Export the data for use in future steps
#     return r.json()


# import requests


# def handler(pd: "pipedream"):
#     headers = {"Authorization": f'Bot {pd.inputs["discord_bot"]["$auth"]["bot_token"]}'}
#     r = requests.get("https://discord.com/api/users/@me", headers=headers)
#     # Export the data for use in future steps
#     return r.json()

########################################################################################


########################################################################################
#                                 Script entrypoint.                                   #
########################################################################################
if __name__ == "__main__":
    # Gather command line args.
    argparser = init_argparse()

    # Print the usage statement if no arguments are given.
    if len(sys.argv) <= 1:
        argparser.print_help()
        sys.exit()

    args = argparser.parse_args()

    if not args.config:
        sys.exit("Must provide configuration file.")

    # Get all config and environment variables.
    config = get_config(args)

    # Configure logger for the script.
    logging.getLogger("asyncio").setLevel(logging.ERROR)
    logging.getLogger("googleapicliet.discovery").setLevel(logging.ERROR)
    logging.getLogger("googleapicliet.discovery_cache").setLevel(logging.ERROR)
    logger = logging.getLogger()
    logger.setLevel(config["log_level"])
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(config["log_level"])
    streamHandler.setFormatter(Formatter())
    logger.addHandler(streamHandler)

    # Initialize intents for Discord.
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    intents.presences = True

    # Create the bot client and initialize members.
    bot = PuckBotClient(
        command_prefix=config["command_prefix"],
        description="A music bot for you dumb chuds.",
        intents=intents,
    )
    bot.config = config
    bot.logger = logger
    bot.youtube = googleapiclient.discovery.build(
        bot.config["api_service_name"],
        bot.config["api_version"],
        developerKey=config["developer_key"],
    )

    # https://googleapis.github.io/google-api-python-client/docs/epy/index.html
    async def main():
        """Main bot entrypoint."""
        async with bot:
            # bot.loop.create_task(background_task())
            await load_extensions(bot, "./music_bot/cogs")

            for cog_name in bot.cogs:
                logger.info(f"Cog - {cog_name}")
                cog = bot.get_cog(cog_name)
                if cog:
                    commands = cog.get_commands()
                    print([c.name for c in commands])
                else:
                    sys.exit(f"ERROR: Unable to get cog {cog_name} from bot.")

            await bot.start(config["token"])

    # Run the bot.
    asyncio.run(main())
