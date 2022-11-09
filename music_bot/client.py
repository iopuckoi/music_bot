# Standard library imports.
import json
import logging
import sys
from os.path import dirname

# Third party imports.
import discord

# import googleapiclient.discovery
# import youtube_dl
from discord.ext import commands


class PuckBotClient(commands.Bot):
    """Subclass commands.Bot clas."""

    def __init__(self, *args, **kwargs):
        super(PuckBotClient, self).__init__(*args, **kwargs)

    ####################################################################################
    #                                  Properties                                      #
    ####################################################################################
    @property
    def config(self) -> dict:
        return self.__config

    @config.setter
    def config(self, config: dict):
        self.__config = config

    @property
    def logger(self) -> logging.Logger:
        return self.__logger

    @logger.setter
    def logger(self, logger: logging.Logger):
        self.__logger = logger

    ####################################################################################
    #                                   Methods                                        #
    ####################################################################################
    def get_playlists(self) -> dict:
        with open(
            file=f"{dirname(__file__)}/playlists.json",
            mode="r",
            encoding="utf-8",
        ) as playlists:
            try:
                return json.loads(playlists.read())

            except Exception as err:
                self.logger.error("   Error loading playlist file as json:")
                self.logger.error(f"    {err}")

                sys.exit("Aborting bot!!!")

    ####################################################################################
    async def on_ready(self) -> None:
        """Override discord.Client on_ready method.  Called when the client is done
        preparing the data received from Discord. Usually after login is successful
        and the Client.guilds and co. are filled up.
        """
        guild = discord.utils.get(self.guilds, name=self.config["guild"])
        if not guild:
            sys.exit(f"Could not connect to guild {self.config['guild']}")

        print(
            f"{self.user} is connected to the following guild:\n"
            f"{guild.name}(id: {guild.id})"
        )

        members = "\n - ".join([member.name for member in guild.members])
        print(f"Guild Members:\n - {members}")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="to you fat chuds talk!"
            )
        )

    # async def on_member_join(member):
    #     await member.create_dm()
    #     await member.dm_channel.send(f"Hi {member.name}, you greasy Boglim!")

    ####################################################################################
    async def on_message(self, message: discord.Message) -> None:
        """Override discord.Client on_message method.  Called when a Message is received.

        Args:
            message (discord.Message): The current message.
        """
        if message.author == self.user:
            return

        if message.content == "test":
            await message.channel.send(f"Shut up {message.author}, you greasy Boglim!")

        # This only needs to be here because we are overriding the default on_message.
        # Otherwise, the new method will block all other commands.
        await self.process_commands(message)
