# Third party imports.
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
    @commands.Cog.listener()
    async def on_ready(self):
        """Method called once the bot is ready."""
        print("Bot is now online!\n")

    ####################################################################################
    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """A special method that acts as a cog local pre-invoke hook.

        Args:
            ctx (commands.Context): The cog context.
        """
        self.audio_state = AudioState(self.bot, ctx)

    ####################################################################################
    async def cog_unload(self):
        """A special method that is called when the cog gets removed."""
        self.bot.loop.create_task(self.audio_state.stop())

    ####################################################################################
    @commands.command(name="join", invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        destination = ctx.author.voice.channel
        if self.audio_state.voice:
            await self.audio_state.voice.move_to(destination)
            return

        self.audio_state.voice = await destination.connect()

    ####################################################################################
    @commands.command(name="leave", aliases=["disconnect"])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not self.audio_state.voice:
            return await ctx.send("Not connected to any voice channel.")

        await self.audio_state.stop()

    ####################################################################################
    @commands.command(name="play")
    async def _play(self, ctx: commands.Context):
        """Plays a song.  If there are songs in the queue, this will be queued until the
        other songs finished playing.
        """

        if not self.audio_state.voice:
            await ctx.invoke(self._join)

        self.audio_state.play()

    ####################################################################################
    @commands.command(name="queue")
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("Empty queue.")

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ""
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += "`{0}.` [**{1.source.title}**]({1.source.url})\n".format(
                i + 1, song
            )

        embed = discord.Embed(
            description="**{} tracks:**\n\n{}".format(len(ctx.voice_state.songs), queue)
        ).set_footer(text="Viewing page {}/{}".format(page, pages))
        await ctx.send(embed=embed)

    ####################################################################################
    # @commands.command(name="pause")
    # @commands.has_permissions(manage_guild=True)
    # async def _pause(self, ctx: commands.Context):
    #     """Pauses the currently playing song."""

    #     if not self.voice_state.is_playing and ctx.voice_state.voice.is_playing():
    #         ctx.voice_state.voice.pause()
    #         await ctx.message.add_reaction("⏯")

    # ####################################################################################
    # @commands.command(name="resume")
    # @commands.has_permissions(manage_guild=True)
    # async def _resume(self, ctx: commands.Context):
    #     """Resumes a currently paused song."""

    #     if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
    #         ctx.voice_state.voice.resume()
    #         await ctx.message.add_reaction("⏯")

    ####################################################################################
    @_join.before_invoke
    @_play.before_invoke
    async def ensure_audio_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("You are not connected to any voice channel.")

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError("Bot is already in a voice channel.")

    ####################################################################################
    # @commands.command(name="play_song", help="To play song")
    # async def play(self, ctx: commands.Context, url):
    #     try:
    #         server = ctx.message.guild
    #         voice_channel = server.voice_client

    #         async with ctx.typing():
    #             filename = await YTDLSource.from_url(url, loop=bot.loop)
    #             voice_channel.play(
    #                 discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename)
    #             )
    #         await ctx.send("**Now playing:** {}".format(filename))
    #     except:
    #         await ctx.send("The bot is not connected to a voice channel.")

    ####################################################################################
    @commands.command(name="clear", help="Clear all songs in the queue.")
    async def clear(self, ctx: commands.Context) -> None:
        """Clear all songs in the queue.

        Args:
            ctx (commands.Context): The cog context.
        """
        self.bot.queue.clear()
        # TODO: add some check to make sure queue properly cleared.
        await ctx.send("Queue cleared.")

    # TODO:
    # add to queue
    # inject into cue
    # skip
    # back
    # pause
    # resume
    # stop

    ####################################################################################
    @commands.command(name="list", help="List all songs in a given playlist.")
    async def list(self, ctx: commands.Context, playlist: str) -> None:
        """List all songs in a given playlist.

        Args:
            ctx (commands.Context): The cog context.
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
            playlist (str): Title of the playlist.
        """
        songs = self.bot.get_playlist_songs(playlist)

        cnt = 0
        for song in songs:
            await self.audio_state.queue.put(Song(song))
            cnt += 1

        await ctx.send(f"Loaded {cnt} songs into the queue.")

    ####################################################################################
    @commands.command(name="playlists", help="List all available playlists.")
    async def playlists(self, ctx: commands.Context) -> None:
        """Lists all available playlists.

        Args:
            ctx (commands.Context): The cog context.
        """
        out = "\n\t".join(sorted(self.bot.get_playlists().keys()))

        await ctx.send(f"Available playlists:\n\t{out}\n")

    # @commands.command(name="pause", help="This command pauses the song")
    # async def pause(self, ctx: commands.Context):
    #     voice_client = ctx.message.guild.voice_client
    #     if voice_client.is_playing():
    #         await voice_client.pause()
    #     else:Greetings
    #         await ctx.send("The bot is not playing anything at the moment.")

    # @commands.command(name="resume", help="Resumes the song")
    # async def resume(self, ctx: commands.Context):
    #     voice_client = ctx.message.guild.voice_client
    #     if voice_client.is_paused():
    #         await voice_client.resume()
    #     else:
    #         await ctx.send(
    #             "The bot was not playing anything before this. Use play_song command"
    #         )

    # @commands.command(name="stop", help="Stops the song")
    # async def stop(self, ctx: commands.Context):
    #     voice_client = ctx.message.guild.voice_client
    #     if voice_client.is_playing():
    #         await voice_client.stop()
    #     else:
    #         await ctx.send("The bot is not playing anything at the moment.")


########################################################################################
async def setup(bot: PuckBotClient) -> None:
    """Add the cog to the bot.

    Args:
        bot (PuckBotClient): The Discord bot.
    """
    bot.logger.info("Finishing PuckCog setup...")
    await bot.add_cog(PuckCog(bot))
