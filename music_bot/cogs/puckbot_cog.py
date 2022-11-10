# Third party imports.
from discord.ext import commands
from music_bot.client import PuckBotClient


########################################################################################
class PuckCog(commands.Cog):
    def __init__(self, bot: PuckBotClient):
        self.bot = bot
        self.voice_states = {}

        self.bot.logger.debug("Finished initializing PuckCog.\n")

    @commands.Cog.listener()
    async def on_ready(self):
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
    @commands.command(name="list", help="List all songs in a given playlist.")
    async def list(self, ctx: commands.Context, plist: str) -> None:
        """List all songs in a given playlist.

        Args:
            ctx (commands.Context): The command context.
            plist (str): Playlist for which to list all songs.
        """
        playlist = plist.lower()
        if playlist not in self.bot.config["playlists"]:
            await ctx.send(f"ERROR: invalid playlist provided: {playlist}\n")

        # Set maxResults to 50.  If playlists are larger than this number, need to
        # check if nextPageToken is set.  If its not empty, need to continue making
        # queries til it is.  Provide in the query as nextPageToke = value.
        query = self.bot.youtube.playlistItems().list(
            maxResults=50,
            part="snippet,contentDetails,id,status",
            playlistId=self.bot.config["playlists"][playlist],
        )
        results = query.execute()

        # Further details on response structure are found in the API documentation:
        # https://developers.google.com/youtube/v3/docs/playlistItems/list
        songs = list()
        for song in results["items"]:
            songs.append(song["snippet"]["title"])

        await ctx.send("\n".join(songs))

    ####################################################################################
    @commands.command(name="playlists", help="List all available playlists.")
    async def playlists(self, ctx: commands.Context) -> None:
        """Lists all available playlists.

        Args:
            ctx (commands.Context): The command context.
        """
        out = "\n\t".join(self.bot.config["playlists"].keys())
        await ctx.send(f"Available playlists:{out}\n")

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
async def setup(bot: PuckBotClient):
    bot.logger.info("Finishing PuckCog setup...")
    await bot.add_cog(PuckCog(bot))
