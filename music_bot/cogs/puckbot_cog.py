# Third party imports.
import googleapiclient.discovery
from discord.ext import commands
from music_bot.client import PuckBotClient


########################################################################################
class PuckCog(commands.Cog):
    def __init__(self, bot: PuckBotClient):
        self.bot = bot
        self.voice_states = {}
        self.youtube = googleapiclient.discovery.build(
            self.bot.config["api_service_name"],
            self.bot.config["api_version"],
            developerKey=self.bot.config["developer_key"],
        )

        self.bot.logger.debug("Finished initializing PuckCog:")
        self.bot.logger.debug(self.fart.__dict__)

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

    @commands.command(name="fart", help="This command farts")
    async def fart(self, ctx: commands.Context):
        self.bot.logger.info("Sending fart command!")
        await ctx.send(f"Available playlists - {self.bot.config['playlists'].keys()}")

    # @commands.command(name="pause", help="This command pauses the song")
    # async def pause(self, ctx: commands.Context):
    #     voice_client = ctx.message.guild.voice_client
    #     if voice_client.is_playing():
    #         await voice_client.pause()
    #     else:
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


async def setup(bot: PuckBotClient):
    bot.logger.info("Finishing PuckCog setup...")
    await bot.add_cog(PuckCog(bot))
