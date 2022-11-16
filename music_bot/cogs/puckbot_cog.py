# Third party imports.
import random
from os.path import dirname

from discord.ext import commands

from music_bot.client import PuckBotClient
from music_bot.common.classes import AudioState, Song


########################################################################################
class PuckCog(commands.Cog):
    """Cog containing commands for the Puck Discord bot."""

    def __init__(self, bot: PuckBotClient):
        self.bot = bot

        self.bot.logger.debug("Finished initializing PuckCog.\n")

    ####################################################################################
    #                                  Properties                                      #
    ####################################################################################
    @property
    def audio_state(self) -> AudioState:
        """Current state of the playlist.

        Returns:
            AudioState: Current state of the playlist.
        """
        return self.__audio_state

    @audio_state.setter
    def audio_state(self, audio_state: AudioState):
        self.__audio_state = audio_state

    ####################################################################################
    @property
    def bot(self) -> PuckBotClient:
        """The discord bot client.

        Returns:
            PuckBotClient: The discord bot client.
        """
        return self.__bot

    @bot.setter
    def bot(self, bot: PuckBotClient):
        self.__bot = bot

    ####################################################################################
    #                             Special Cog Methods                                  #
    #       More info about Cogs and their special methods can be found here:          #
    #     https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#cog         #
    ####################################################################################
    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """A special method that acts as a cog local pre-invoke hook.

        Args:
            ctx (commands.Context): The cog context.
        """
        self.audio_state = AudioState(self.bot, ctx)

    ####################################################################################
    async def cog_unload(self) -> None:
        """A special method that is called when the cog gets removed."""
        self.bot.loop.create_task(self.audio_state.stop())

    ####################################################################################
    #                                 Cog Listeners                                    #
    ####################################################################################
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Method called once the bot is ready."""
        print("Bot is now online!\n")

    ####################################################################################
    #                                 Bot Commands                                     #
    ####################################################################################
    # @commands.command(name="queue")
    # async def _queue(self, ctx: commands.Context, *, page: int = 1):
    #     """Shows the player's queue.
    #     You can optionally specify the page to show. Each page contains 10 elements.
    #     """

    #     if len(ctx.voice_state.songs) == 0:
    #         return await ctx.send("Empty queue.")

    #     items_per_page = 10
    #     pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

    #     start = (page - 1) * items_per_page
    #     end = start + items_per_page

    #     queue = ""
    #     for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
    #         queue += "`{0}.` [**{1.source.title}**]({1.source.url})\n".format(
    #             i + 1, song
    #         )

    #     embed = discord.Embed(
    #         description="**{} tracks:**\n\n{}".format(len(ctx.voice_state.songs), queue)
    #     ).set_footer(text="Viewing page {}/{}".format(page, pages))
    #     await ctx.send(embed=embed)
    ####################################################################################
    @commands.command(name="add", help="Add a song or a playlist to the queue.")
    async def add(self, ctx: commands.Context, url: str) -> None:
        """Add a song or a playlist to the queue.

        Args:
            ctx (commands.Context): The command context.
            url (str): Url to load into the queue.
        """
        result = self.bot.config["playlist_regex"].search(url)
        # Process as a playlist.
        if result:
            cnt = await self._load(playlist_id=result.group("playlist_id"))

        # Process as a song.
        else:
            cnt = await self._load(song_url=url)

        await ctx.send(f"Loaded {cnt} songs into the queue.")
        await ctx.invoke(self.play)

    ####################################################################################
    @commands.command(name="clear", help="Clear all songs in the queue.")
    async def clear(self, ctx: commands.Context) -> None:
        """Clear all songs in the queue.

        Args:
            ctx (commands.Context): The cog context.
        """
        self.audio_state.queue.clear()

        await ctx.send("Queue cleared.")

    ####################################################################################
    # def inject

    ####################################################################################
    @commands.command(name="jerk", help="Shut up, jerk.")
    async def jerk(self, ctx: commands.Context) -> None:
        """Act like a stupid jerk.

        Args:
            ctx (commands.Context): The command context.
        """
        lines = []
        with open(
            file=f"{dirname(__file__)}/../files/jerk_city.txt",
            mode="r",
            encoding="utf-8",
        ) as jrk:
            for line in jrk:
                lines.append(line)

        await ctx.send(random.choice(lines), tts=True)

    ####################################################################################
    @commands.command(name="join", invoke_without_subcommand=True)
    async def join(self, ctx: commands.Context) -> None:
        """Joins a voice channel."""
        destination = ctx.author.voice.channel
        if self.audio_state.voice:
            await self.audio_state.voice.move_to(destination)
            return

        self.audio_state.voice = await destination.connect()

    ####################################################################################
    @commands.command(name="leave", aliases=["disconnect"])
    @commands.has_permissions(manage_guild=True)
    async def leave(self, ctx: commands.Context) -> None:
        """Clears the queue and leaves the voice channel.

        Args:
            ctx (commands.Context): The command context.
        """
        if not self.audio_state.voice:
            await ctx.send("Not connected to any voice channel.")
            return

        await self.audio_state.stop()

    ####################################################################################
    @commands.command(name="list", help="List all songs in a given playlist.")
    async def list(self, ctx: commands.Context, playlist: str) -> None:
        """List all songs in a given playlist.

        Args:
            ctx (commands.Context): The command context.
            plist (str): Playlist for which to list all songs.
        """
        try:
            songs = self.bot.get_playlist_songs(playlist)
            await ctx.send("\n - ".join([song["snippet"]["title"] for song in songs]))

        except Exception as err:
            await ctx.send(
                f"Error encountered getting songs for playlist {playlist} : {err}"
            )

    ####################################################################################
    @commands.command(
        name="load", help="Load all songs in a given playlist at the end of the queue."
    )
    async def load(self, ctx: commands.Context, playlist: str) -> None:
        """Load a given playlist into the queue.

        Args:
            ctx (commands.Context): The command context.
            playlist (str): Title of the playlist.
        """
        cnt = await self._load(playlist=playlist)
        await ctx.send(f"Loaded {cnt} songs into the queue.")

    ####################################################################################
    async def _load(self, **kwargs) -> int:
        """Load songs into the queue by playlist name, playlist id, or song url.

        Returns:
            int: Number of songs added to the queue.
        """
        cnt = 0
        if "song_url" in kwargs:
            songs = self.bot.get_song(**kwargs)
        else:
            songs = self.bot.get_playlist_songs(**kwargs)

        for song in songs:
            await self.audio_state.queue.put(Song(song))
            cnt += 1

        return cnt

    ####################################################################################
    @commands.command(name="pause", help="Pause the current song.")
    @commands.has_permissions(manage_guild=True)
    async def pause(self, ctx: commands.Context) -> None:
        """Pauses the currently playing song.

        Args:
            ctx (commands.Context): The command context.
        """
        if not self.audio_state.is_playing and self.audio_state.voice.is_playing():
            self.audio_state.voice.pause()  # type: ignore
            await ctx.message.add_reaction("⏯")

    ####################################################################################
    @commands.command(name="play", help="Play songs in the queue.")
    async def play(self, ctx: commands.Context) -> None:
        """Plays a song.  If there are songs in the queue, this will be queued until the
        other songs finished playing.
        """

        if not self.audio_state.voice:
            await ctx.invoke(self.join)

        self.audio_state.play()

    ####################################################################################
    @commands.command(name="playlists", help="List all available playlists.")
    async def playlists(self, ctx: commands.Context) -> None:
        """Lists all available playlists.

        Args:
            ctx (commands.Context): The command context.
        """
        out = "\n\t".join(sorted(self.bot.get_playlists().keys()))

        await ctx.send(f"Available playlists:\n\t{out}\n")

    ####################################################################################
    @commands.command(name="resume", help="Resume the playlist.")
    @commands.has_permissions(manage_guild=True)
    async def resume(self, ctx: commands.Context) -> None:
        """Resume playing a paused playlist.

        Args:
            ctx (commands.Context): The command context.
        """
        if not self.audio_state.is_playing and self.audio_state.voice.is_paused():  # type: ignore
            self.audio_state.voice.resume()  # type: ignore
            await ctx.message.add_reaction("⏯")

    ####################################################################################
    @commands.command(name="skip", help="Skip the current song.")
    @commands.has_permissions(manage_guild=True)
    async def skip(self, ctx: commands.Context) -> None:
        """Skip the currently queued song.

        Args:
            ctx (commands.Context): The command context.
        """
        if self.audio_state.is_playing:
            self.audio_state.voice.stop()  # type: ignore
            await ctx.send(f"Skipping {self.audio_state.current.title}")  # type: ignore

    ####################################################################################
    # @commands.command(name="stop", help="Stops the song")
    # async def stop(self, ctx: commands.Context):
    #     voice_client = ctx.message.guild.voice_client
    #     if voice_client.is_playing():
    #         await voice_client.stop()
    #     else:
    #         await ctx.send("The bot is not playing anything at the moment.")

    ####################################################################################
    #                             Instance Methods                                     #
    ####################################################################################
    @join.before_invoke
    @play.before_invoke
    async def ensure_audio_state(self, ctx: commands.Context) -> None:
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("You are not connected to any voice channel.")

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError("Bot is already in a voice channel.")


########################################################################################
async def setup(bot: PuckBotClient) -> None:
    """Add the cog to the bot.

    Args:
        bot (PuckBotClient): The Discord bot client.
    """
    bot.logger.info("Finishing PuckCog setup...")
    await bot.add_cog(PuckCog(bot))
