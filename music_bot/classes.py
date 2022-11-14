# Standard library imports.
import asyncio
from collections import OrderedDict
from collections.abc import Mapping, MutableMapping
import discord
from discord.ext import commands
import logging
import random
import functools
import itertools
import youtube_dl
from music_bot.common.exceptions import YTDLError, VoiceError


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)


########################################################################################
class CaseInsensitiveDict(MutableMapping):
    """A case-insensitive ``dict``-like object.
    Implements all methods and operations of
    ``MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.
    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::
        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True
    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.
    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
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

        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    def __getitem__(self, key):
        if key.lower() in self._store:
            return self._store[key.lower()][1]
        else:
            raise Exception(f"ERROR: key \"{key}\" does not exist.")

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
    def copy(self):
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
class Song():
    def __init__(self, song: dict):
        self.thumbnail = song["snippet"]["thumbnails"]["high"]["url"]
        self.title = song["snippet"]["title"]
        self.video_id = song["snippet"]["resourceId"]["videoId"]

    # def __repr__(self):
        #TODO: get prety-dict from work code for this, create dict of all members
        # return str(dict(self.items()))

    __slots__ = ('source', 'requester', 'thumbnail', 'title', 'video_id')

    # def __init__(self, source: YTDLSource):
    #     self.source = source
    #     self.requester = source.requester

    # def create_embed(self):
    #     embed = (discord.Embed(title='Now playing',
    #                            description='```css\n{0.source.title}\n```'.format(self),
    #                            color=discord.Color.blurple())
    #              .add_field(name='Duration', value=self.source.duration)
    #              .add_field(name='Requested by', value=self.requester.mention)
    #              .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
    #              .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
    #              .set_thumbnail(url=self.source.thumbnail))

    #     return embed


########################################################################################
class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
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

