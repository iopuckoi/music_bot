# Standard library imports.
import os
import sys

# Third party imports.
import discord
from discord.ext import commands
from dotenv import load_dotenv
import googleapiclient.discovery


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
        guild = discord.utils.get(client.guilds, name=GUILD)
        print(
            f"{client.user} is connected to the following guild:\n"
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
        if message.author == client.user:
            return

        if message.content == "test":
            await message.channel.send(f"Shut up {message.author}, you greasy Boglim!")


########################################################################################
#                                 Script entrypoint.                                   #
########################################################################################
if __name__ == "__main__":
    load_dotenv()
    TOKEN = str(os.getenv("DISCORD_TOKEN"))
    GUILD = str(os.getenv("DISCORD_GUILD"))
    DEVELOPER_KEY = str(os.getenv("GOOGLE_API_TOKEN"))

    if not TOKEN:
        sys.exit("DISCORD_TOKEN missing from .env file.")

    if not GUILD:
        sys.exit("DISCORD_GUILD missing from .env file.")

    if not DEVELOPER_KEY:
        sys.exit("GOOGLE_API_TOKEN missing from .env file.")

    # YouTube API information.
    api_service_name = "youtube"
    api_version = "v3"

    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    intents.presences = True

    # client = PuckBotClient(intents=intents, command_prefix="/")
    # client.run(TOKEN)

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

    # 'request' variable is the only thing you must change
    # depending on the resource and method you need to use
    # in your query
    playlist_response = youtube.playlistItems().list(
        part="snippet,contentDetails,id,status",
        playlistId=str(os.getenv("GAME_NIGHT"))
    )
    
    # Query execution
    response = playlist_response.execute()
    # Print the results
    import pprint
    pprint.pprint(response)
