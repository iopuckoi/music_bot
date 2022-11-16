# Standard library imports.
import logging
import os
import sys

# Third party imports.
import discord
import googleapiclient.discovery
from discord.ext import commands

from music_bot.common.classes import CaseInsensitiveDict
from music_bot.common.exceptions import PuckBotClientError


class PuckBotClient(commands.Bot):
    """Subclass commands.Bot class."""

    def __init__(self, *args, **kwargs):
        super(PuckBotClient, self).__init__(*args, **kwargs)

    ####################################################################################
    #                                  Properties                                      #
    ####################################################################################
    @property
    def config(self) -> dict:
        """Bot configuration dictionary.

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
        """Bot logger object.

        Returns:
            logging.Logger: Bot logger object.
        """
        return self.__logger

    @logger.setter
    def logger(self, logger: logging.Logger):
        self.__logger = logger

    ####################################################################################
    @property
    def youtube(self) -> googleapiclient.discovery.Resource:
        """YouTube API Resource object

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
        """Query YouTube for all public playlists for the proided channel ID. Further
        details on response structure are found in the API documentation:
        https://developers.google.com/youtube/v3/docs/playlists/list

        Returns:
            CaseInsensitiveDict: Dict conaining all playlist names and YouTube link.
        """
        done = False
        next_token = ""
        playlists = []
        while not done:
            results = (
                self.youtube.playlists()  # type: ignore
                .list(
                    channelId=self.config["channel_id"],
                    maxResults=10,
                    pageToken=next_token,
                    part="snippet,contentDetails,id,status",
                )
                .execute()
            )
            playlists = playlists + results["items"]
            if "nextPageToken" in results:
                next_token = results["nextPageToken"]
            else:
                done = True

        return CaseInsensitiveDict(
            **{playlist["snippet"]["title"]: playlist["id"] for playlist in playlists}
        )

    ####################################################################################
    def get_playlist_songs(self, playlist: str = "", playlist_id: str = "") -> list:
        """Query YouTube for all songs in a provided public playlist. Further details
        on response structure are found in the API documentation:
        https://developers.google.com/youtube/v3/docs/playlistItems/list

        Args:
            playlist (str, optional): A playlist title. Defaults to "".
            playlist_id (str, optional): A playlist id. Defaults to "".

        Raises:
            Exception: Raised if invalid playlist provided.

        Returns:
            list: List containing information of all retreived songs.
        """
        # If playlist_id was not provided, attempt to get from provided playlist name.
        if not playlist_id:
            if not playlist:
                raise PuckBotClientError("Must provide a playlist title or id.\n")

            try:
                playlists = self.get_playlists()

            except Exception as err:
                raise Exception(f"Error getting songs for playlist: {err}\n") from err

            playlist_id = playlists[playlist]

        done = False
        next_token = ""
        songs = []
        while not done:
            results = (
                self.youtube.playlistItems()  # type: ignore
                .list(
                    maxResults=25,
                    pageToken=next_token,
                    part="snippet,contentDetails,id,status",
                    playlistId=playlist_id,
                )
                .execute()
            )
            songs = songs + results["items"]
            if "nextPageToken" in results:
                next_token = results["nextPageToken"]
            else:
                done = True

        return songs

    ########################################################################################
    def get_song(self, song_url: str = "") -> list:
        """Get a song from a video url.

        Args:
            song_url (str, optional): YouTube video url. Defaults to "".

        Raises:
            PuckBotClientError: Raised if input argument missing.
            PuckBotClientError: Raised if the video id could not be extracted.

        Returns:
            list: A list of one item, the requested song.
        """
        if not song_url:
            raise PuckBotClientError("Must provide a song url.\n")

        result = self.config["video_regex"].search(song_url)
        if result:
            results = (
                self.youtube.videos()  # type: ignore
                .list(
                    part="snippet,contentDetails,id,status",
                    id=result.group("video_id"),
                )
                .execute()
            )

            return results["items"]

        raise PuckBotClientError("Could not extract video id from url.\n")

    ########################################################################################
    async def load_extensions(self, cog_path: str) -> None:
        """Load all cogs into the bot.

        Args:
            cog_path (str): Path to all cogs.
        """
        self.logger.info("Loading extensions:")
        for filename in os.listdir(cog_path):
            if filename == "__init__.py":
                continue

            if filename.endswith(".py"):
                # Cut off the .py from the file name.
                self.logger.info(f"  ...loading cog : {filename}")
                cog_package = cog_path[2:].replace("/", ".")
                await self.load_extension(f"{cog_package}.{filename[:-3]}")

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

        members = "\n\t- ".join([member.name for member in guild.members])
        print(f"Guild Members:\n\t- {members}\n")

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
