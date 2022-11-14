# Third party imports.
from discord.ext import commands
from music_bot.client import PuckBotClient


########################################################################################
class PuckCog(commands.Cog):
    """Cog containing commands for the Puck Discord bot."""

    def __init__(self, bot: PuckBotClient):
        self.bot = bot
        self.voice_states = {}

        self.bot.logger.debug("Finished initializing PuckCog.\n")

    @commands.Cog.listener()
    async def on_ready(self):
        """Method called once the bot is ready."""
        print("Bot is now online!\n")

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
        self.bot.queue.clear()
        #TODO: add some check to make sure queue properly cleared.
        await ctx.send("Queue cleared.")
    #TODO:
    #add to queue
    #inject into cue
    #skip
    #back
    #pause
    #resume
    #stop

    ####################################################################################
    @commands.command(name="list", help="List all songs in a given playlist.")
    async def list(self, ctx: commands.Context, playlist: str) -> None:
        """List all songs in a given playlist.

        Args:
            ctx (commands.Context): The command context.
            plist (str): Playlist for which to list all songs.
        """
        playlists = self.bot.get_playlists()
        if playlist not in playlists:
            await ctx.send(f"ERROR: invalid playlist provided: {playlist}\n")

        results = self.bot.get_playlist_songs(playlist)

        # Further details on response structure are found in the API documentation:
        # https://developers.google.com/youtube/v3/docs/playlistItems/list
        songs = list()
        for song in results["items"]:
            songs.append(song["snippet"]["title"])

        await ctx.send("\n - ".join(songs))

    ####################################################################################
    @commands.command(name="playlists", help="List all available playlists.")
    async def playlists(self, ctx: commands.Context) -> None:
        """Lists all available playlists.

        Args:
            ctx (commands.Context): The command context.
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
