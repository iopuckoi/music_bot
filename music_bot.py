# Standard library imports.
import os
import pprint

# Third party imports.
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

pprint.pprint(TOKEN)
pprint.pprint(GUILD)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, name=GUILD)
    print(
        f"{client.user} is connected to the following guild:\n"
        f"{guild.name}(id: {guild.id})"
    )

    members = "\n - ".join([member.name for member in guild.members])
    print(f"Guild Members:\n - {members}")


# @client.event
# async def on_member_join(member):
#     await member.create_dm()
#     await member.dm_channel.send(f"Hi {member.name}, you greasy Boglim!")
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == "test":
        await message.channel.send(f"Shut up {message.author}, you greasy Boglim!")


client.run(TOKEN)


# client.run(TOKEN)


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


# class CustomClient(discord.Client):
#     async def on_ready(self):
#         print(f'{self.user} has connected to Discord!')

# client = CustomClient()
