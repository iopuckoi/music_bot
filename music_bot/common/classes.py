# Standard library imports.
from __future__ import annotations

import asyncio
import functools
import itertools
import logging
import random
from collections import OrderedDict
from collections.abc import Mapping, MutableMapping
from typing import Union

# Third party imports.
import discord
import youtube_dl
from async_timeout import timeout
from discord.ext import commands

from music_bot.common.exceptions import CaseInsensitiveDictError, VoiceError, YTDLError


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        "format": "bestaudio/best",
        "extractaudio": True,
        "audioformat": "mp3",
        "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",
    }

    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(
        self,
        ctx: commands.Context,
        source: discord.FFmpegPCMAudio,
        *,
        data: dict,
        volume: float = 0.5,
    ):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get("uploader")
        self.uploader_url = data.get("uploader_url")
        date = data.get("upload_date")
        self.upload_date = date[6:8] + "." + date[4:6] + "." + date[0:4]
        self.title = data.get("title")
        self.thumbnail = data.get("thumbnail")
        self.description = data.get("description")
        self.duration = self.parse_duration(int(data.get("duration")))
        self.tags = data.get("tags")
        self.url = data.get("webpage_url")
        self.views = data.get("view_count")
        self.likes = data.get("like_count")
        self.dislikes = data.get("dislike_count")
        self.stream_url = data.get("url")

    def __str__(self):
        return "**{0.title}** by **{0.uploader}**".format(self)

    @classmethod
    async def create_source(
        cls, ctx: commands.Context, url: str, loop: asyncio.AbstractEventLoop = None
    ):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError(f"Couldn't fetch url {url}.")

        if "entries" not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info["entries"].pop(0)
                except IndexError:
                    raise YTDLError(f"Couldn't retrieve any matches for {url}:")

        return cls(
            ctx, discord.FFmpegPCMAudio(info["url"], **cls.FFMPEG_OPTIONS), data=info
        )

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append("{} days".format(days))
        if hours > 0:
            duration.append("{} hours".format(hours))
        if minutes > 0:
            duration.append("{} minutes".format(minutes))
        if seconds > 0:
            duration.append("{} seconds".format(seconds))

        return ", ".join(duration)


########################################################################################
class AudioState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self.ctx = ctx

        self.audio_player = None
        self.current = None
        self.next = asyncio.Event()
        self.queue = SongQueue()
        self.voice = None

        self._loop = False
        self._volume = 0.5

    def __del__(self):
        if self.audio_player is not None:
            self.audio_player.cancel()

    ####################################################################################
    #                                  Properties                                      #
    ####################################################################################
    @property
    def audio_player(self) -> Union[asyncio.Task, None]:
        return self._audio_player

    @audio_player.setter
    def audio_player(self, audio_player: Union[asyncio.Task, None]):
        self._audio_player = audio_player

    ####################################################################################
    @property
    def current(self) -> Union[Song, None]:
        return self._current

    @current.setter
    def current(self, current: Union[Song, None]):
        self._current = current

    ####################################################################################
    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    ####################################################################################
    @property
    def queue(self) -> SongQueue:
        """Asynchronous song queue.

        Returns:
            SongQueue: Song queue.
        """
        return self.__queue

    @queue.setter
    def queue(self, queue: SongQueue):
        self.__queue = queue

    ####################################################################################
    @property
    def voice(self) -> Union[discord.VoiceClient, None]:
        """Discord voice channel client.

        Returns:
            Union[discord.VoiceClient, None]: "Discord voice channel client.
        """
        return self._voice

    @voice.setter
    def voice(self, voice: Union[discord.VoiceClient, None]):
        self._voice = voice

    ####################################################################################
    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, volume: float):
        self._volume = volume

    ####################################################################################
    # @property
    # def is_playing(self) -> bool:
    #     return self.voice and self.current

    ####################################################################################
    async def audio_player_task(self):
        while True:
            self.next.clear()

            # Make sure the queue is not empty.
            if self.queue.empty():
                self.bot.loop.create_task(self.stop())

                return

            if not self.loop:
                # Try to get the next song within 3 minutes. If no song will be added to
                # the queue in time, the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.queue.get()

                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())

                    return

            # Make sure we have a song ready to play.
            if self.current is None:
                self.bot.loop.create_task(self.stop())

                return

            # Try and create a download source for the song.
            async with self.ctx.typing():
                try:
                    source = await YTDLSource.create_source(
                        self.ctx, self.current.url, loop=self.bot.loop
                    )
                except YTDLError as err:
                    await self.ctx.send(
                        f"An error occurred while processing this request: {err}"
                    )
                else:
                    self.current.source = source

            # self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            # Await the next song to get queued.
            await self.next.wait()

    ####################################################################################
    def play(self):
        if self.audio_player is None:
            self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    ####################################################################################
    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    # ####################################################################################
    # def skip(self):
    #     if self.is_playing:
    #         self.voice.stop()

    ####################################################################################
    async def stop(self):
        self.queue.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


########################################################################################
class CaseInsensitiveDict(MutableMapping):
    """This class was liberally borrowed and expanded upon the requests library:
    https://github.com/psf/requests/blob/main/requests/structures.py

    A case-insensitive dict-like object.  Implements all methods and operations of
    MutableMapping as well as dict's copy. Also provides lower_items.  All keys are
    expected to be strings. The structure remembers the case of the last key to be set,
    and iter(instance), keys(), items(), iterkeys(), and iteritems() will contain
    case-sensitive keys. However, querying and contains testing is case insensitive:

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, headers['content-encoding'] will return the value of a Content-Encoding
    response header, regardless of how the header name was originally stored. If the
    constructor, .update, or equality comparison operations are given keys that have
    equal .lower()s, the behavior is undefined.
    """

    def __init__(self, data=None, **kwargs):
        self._store = OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __eq__(self, other):
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented

        # Compare insensitively.
        return dict(self.lower_items()) == dict(other.lower_items())

    def __getitem__(self, key):
        if key.lower() in self._store:
            return self._store[key.lower()][1]

        raise CaseInsensitiveDictError(f'ERROR: key "{key}" does not exist in dict.')

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def __repr__(self):
        return str(dict(self.items()))

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    # Copy is required
    def copy(self) -> CaseInsensitiveDict:
        return CaseInsensitiveDict(self._store.values())

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())


########################################################################################
class Formatter(logging.Formatter):
    """Subclass Formatter to custom format logging messages."""

    def format(self, record):
        # ANSI escape codes for colors:
        # black = "\x1b[30;20m"
        # blue = "\x1b[34;20m"
        # cyan = "\x1b[36;20m"
        # dark_grey = "\x1b[30;1m"
        # grey = "\x1b[38;20m"
        # green = "\x1b[32;20m"
        # light_blue = "\x1b[34;1m"
        # light_cyan = "\x1b[36;1m"
        # light_green = "\x1b[32;1m"
        # light_grey = "\x1b[37;20m"
        # light_red = "\x1b[31;1m"
        # light_purple = "\x1b[35;1m"
        # orange = "\x1b[33;20m"
        # purple = "\x1b[35;20m"
        red = "\x1b[31;20m"
        reset = "\x1b[0m"
        # white = "\x1b[;20m"
        yellow = "\x1b[33;20m"
        if record.levelno == logging.INFO:
            self._style._fmt = "%(message)s"
        elif record.levelno == logging.ERROR:
            self._style._fmt = f"({red}%(levelname)s{reset}) [%(asctime)s]: %(message)s"
        else:
            self._style._fmt = (
                f"({yellow}%(levelname)s{reset}) [%(asctime)s]: %(message)s"
            )

        return super().format(record)


########################################################################################
class Song:
    """Object to hold metadata related to a song."""

    def __init__(self, song: dict):
        self.thumbnail = song["snippet"]["thumbnails"]["high"]["url"]
        self.title = song["snippet"]["title"]
        self.video_id = song["snippet"]["resourceId"]["videoId"]
        self.url = f"https://youtu.be/{self.video_id}"

    # def __repr__(self):
    # TODO: get prety-dict from work code for this, create dict of all members
    # return str(dict(self.items()))

    # __slots__ = ("source", "requester", "thumbnail", "title", "video_id")

    # def __init__(self, source: YTDLSource):
    #     self.source = source
    #     self.requester = source.requester

    ####################################################################################
    #                                  Properties                                      #
    ####################################################################################
    @property
    def source(self) -> YTDLSource:
        """YouTube downloader source object.

        Returns:
            YTDLSource: YouTube downloader source object.
        """
        return self.__source

    @source.setter
    def source(self, source: YTDLSource):
        self.__source = source

    ####################################################################################
    @property
    def thumbnail(self) -> str:
        """URL of the video thumbnail.

        Returns:
            str: URL of the video thumbnail.
        """
        return self.__thumbnail

    @thumbnail.setter
    def thumbnail(self, thumbnail: str):
        self.__thumbnail = thumbnail

    ####################################################################################
    @property
    def title(self) -> str:
        """Title of the song.

        Returns:
            str: Title of the song.
        """
        return self.__title

    @title.setter
    def title(self, title: str):
        self.__title = title

    ####################################################################################
    @property
    def video_id(self) -> str:
        """YouTube ID of the video.

        Returns:
            str: YouTube ID of the video.
        """
        return self.__video_id

    @video_id.setter
    def video_id(self, video_id: str):
        self.__video_id = video_id

    ####################################################################################
    @property
    def url(self) -> str:
        """URL of the video.

        Returns:
            str: URL of the video.
        """
        return self.__url

    @url.setter
    def url(self, url: str):
        self.__url = url

    ####################################################################################
    def create_embed(self) -> discord.Embed:
        """Embed track information into Discord.

        Returns:
            discord.Embed: Discord Embed object.
        """
        return (
            discord.Embed(
                title="Now playing",
                description="```css\n" + self.title + "\n```",
                color=discord.Color.blurple(),
            )
            .add_field(name="Duration", value=self.source.duration)
            # .add_field(name="Requested by", value=self.requester.mention)
            .add_field(
                name="Uploader",
                value=f"[{self.source.uploader}]({self.source.uploader_url})",
            )
            .add_field(name="URL", value=f"[Click]({self.source.url})")
            .set_thumbnail(url=self.thumbnail)
        )


########################################################################################
class SongQueue(asyncio.Queue):
    """Subclass of asyncio queue to create a song queue for the bot."""

    def __getitem__(self, item) -> list:
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))

        return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def remove(self, index: int):
        del self._queue[index]

    def shuffle(self):
        random.shuffle(self._queue)
