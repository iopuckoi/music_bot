# Standard library imports.
import logging
import sys
from os.path import dirname

# Third party imports.
import discord
import googleapiclient.discovery
from music_bot.classes import CaseInsensitiveDict, Song, SongQueue

from discord.ext import commands


class PuckBotClient(commands.Bot):
    """Subclass commands.Bot class."""

    def __init__(self, *args, **kwargs):
        super(PuckBotClient, self).__init__(*args, **kwargs)

    ####################################################################################
    #                                  Properties                                      #
    ####################################################################################
    @property
    def config(self) -> dict:
        """Getter and setter for config.

        Returns:
            dict: Bot configuration dict.
        """
        return self.__config

    @config.setter
    def config(self, config: dict):
        self.__config = config

    ####################################################################################
    @property
    def logger(self) -> logging.Logger:
        """Getter and setter for logger.

        Returns:
            logging.Logger: Bot logger object.
        """
        return self.__logger

    @logger.setter
    def logger(self, logger: logging.Logger):
        self.__logger = logger

    ####################################################################################
    @property
    def queue(self) -> SongQueue:
        """Getter and setter for queue.

        Returns:
            SongQueue: Song queue.
        """
        return self.__queue

    @queue.setter
    def queue(self, queue: SongQueue):
        self.__queue = queue

    ####################################################################################
    @property
    def youtube(self) -> googleapiclient.discovery.Resource:
        """Getter and setter for the YouTube API object.

        Returns:
            googleapiclient.discovery.Resource: YouTube API object.
        """
        return self.__youtube

    @youtube.setter
    def youtube(self, youtube: googleapiclient.discovery.Resource):
        self.__youtube = youtube

    ####################################################################################
    #                                   Methods                                        #
    ####################################################################################
    def get_playlists(self) -> CaseInsensitiveDict:
        """Query YouTUbe for all public playlists for the proided channel ID.

        Returns:
            CaseInsensitiveDict: Dict conaining all playlist names and YouTube link.
        """
        results = self.youtube.playlists().list(  # type: ignore
            maxResults=50,
            channelId=self.config["channel_id"],
            part="snippet,contentDetails,id,status",
        ).execute()

        return CaseInsensitiveDict(**{ playlist["snippet"]["title"] : playlist["id"] for playlist in results["items"] })

    ####################################################################################
    def get_playlist_songs(self, playlist: str) -> dict:
        playlists = self.get_playlists()
        if playlist not in playlists:
            raise Exception(f"ERROR: invalid playlist provided: {playlist}\n")

        # Set maxResults to 50.  If playlists are larger than this number, need to
        # check if nextPageToken is set.  If its not empty, need to continue making
        # queries til it is.  Provide in the query as nextPageToke = value.
        return self.youtube.playlistItems().list(  # type: ignore
            maxResults=50,
            part="snippet,contentDetails,id,status",
            playlistId=playlists[playlist],
        ).execute()

    ####################################################################################
    async def load_playlist(self, playlist: str) -> None:
        songs = self.get_playlist_songs(playlist)

        for song in songs["items"]:
            await self.queue.put(Song(song))

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
