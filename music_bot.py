# Standard library imports.
import json
import logging
import os
import sys
from os.path import dirname

# Third party imports.
import discord
import googleapiclient.discovery
import youtube_dl
from discord.ext import commands
from dotenv import load_dotenv

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
#                                  Custom Classes.                                     #
########################################################################################
class PuckBotClient(commands.Bot):
    """Subclass commands.Bot clas."""

    def __init__(self, *args, **kwargs):
        super(PuckBotClient, self).__init__(*args, **kwargs)

    async def on_ready(self) -> None:
        """Override discord.Client on_ready method.  Called when the client is done
        preparing the data received from Discord. Usually after login is successful
        and the Client.guilds and co. are filled up.
        """
        guild = discord.utils.get(self.guilds, name=config["guild"])
        print(
            f"{self.user} is connected to the following guild:\n"
            f"{guild.name}(id: {guild.id})"
        )

        members = "\n - ".join([member.name for member in guild.members])
        print(f"Guild Members:\n - {members}")

    # async def on_member_join(member):
    #     await member.create_dm()
    #     await member.dm_channel.send(f"Hi {member.name}, you greasy Boglim!")

    async def on_message(self, message: discord.Message) -> None:
        """Override discord.Client on_message method.  Called when a Message is received.

        Args:
            message (discord.Message): The current message.
        """
        if message.author == self.user:
            return

        if message.content == "test":
            await message.channel.send(f"Shut up {message.author}, you greasy Boglim!")


########################################################################################
class PuckCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}
        self.youtube = googleapiclient.discovery.build(
            config["api_service_name"],
            config["api_version"],
            developerKey=config["developer_key"],
        )

    @commands.command(name="play_song", help="To play song")
    async def play(self, ctx: commands.Context, url):
        try:
            server = ctx.message.guild
            voice_channel = server.voice_client

            async with ctx.typing():
                filename = await YTDLSource.from_url(url, loop=bot.loop)
                voice_channel.play(
                    discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename)
                )
            await ctx.send("**Now playing:** {}".format(filename))
        except:
            await ctx.send("The bot is not connected to a voice channel.")

    @commands.command(name="pause", help="This command pauses the song")
    async def pause(self, ctx: commands.Context):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.pause()
        else:
            await ctx.send("The bot is not playing anything at the moment.")

    @commands.command(name="resume", help="Resumes the song")
    async def resume(self, ctx: commands.Context):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_paused():
            await voice_client.resume()
        else:
            await ctx.send(
                "The bot was not playing anything before this. Use play_song command"
            )

    @commands.command(name="stop", help="Stops the song")
    async def stop(self, ctx: commands.Context):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.stop()
        else:
            await ctx.send("The bot is not playing anything at the moment.")


########################################################################################
#                              Function definitions.                                   #
########################################################################################
def get_config() -> dict:
    # Load all environment variables from local .env file.
    load_dotenv()
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
        # Environment variables.
        "developer_key": developer_key,
        "guild": guild,
        "token": token,
        # YouTube API information.
        "api_service_name": "youtube",
        "api_version": "v3",
        # Get and store all playlsits.
        "playlists": get_playlists(),
    }


########################################################################################
def get_playlists() -> dict:
    with open(
        file=f"{dirname(__file__)}/playlists.json",
        mode="r",
        encoding="utf-8",
    ) as playlists:
        try:
            return json.loads(playlists.read())

        except Exception as err:
            logger.error("   Error loading playlist file as json:")
            logger.error(f"    {err}")

            sys.exit("Aborting bot!!!")


########################################################################################
#                                 Script entrypoint.                                   #
########################################################################################
if __name__ == "__main__":
    # Configure logger for the script.
    logger = logging.getLogger()

    # Get all config and environment variables.
    config = get_config()

    # Initialize intents for Discord.
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    intents.presences = True

    # Create and run the Discord client.
    bot = PuckBotClient(intents=intents, command_prefix=config["command_prefix"])
    # TODO : place after all commands
    bot.run(config["token"])

    # youtube = googleapiclient.discovery.build(
    #     config["api_service_name"],
    #     config["api_version"],
    #     developerKey=config["developer_key"],
    # )

    # 'request' variable is the only thing you must change
    # depending on the resource and method you need to use
    # in your query
    # playlist_response = youtube.playlistItems().list(
    #     part="snippet,contentDetails,id,status", playlistId=str(os.getenv("GAME_NIGHT"))
    # )

    # Query execution
    # response = playlist_response.execute()
    # Print the results
    # Standard library imports.
    # import pprint

    # pprint.pprint(response)
