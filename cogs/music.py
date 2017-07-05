import asyncio
import discord
from discord.ext import commands
from cogs import readabletime as ReadableTime
from cogs import style as Style


class VoiceEntry:

    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        fmt = '```css\n{0.title}```Uploaded by {0.uploader}\nRequested by {1.mention}'
        duration = self.player.duration
        if duration:
            fmt = fmt + '\nLength: {0[0]}m {0[1]}s'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)


class VoiceState:

    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set() # a set of user_ids that voted
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            embed = discord.Embed(title = "Now playing:", description = str(self.current), color = Style.Colors.green)
            await self.bot.send_message(self.current.channel, embed=embed)
            self.current.player.start()
            await self.play_next_song.wait()

class Music:

    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}
        self.votes_needed = 3

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx, *, channel : discord.Channel):
        """Summons the bot to a specific voice channel."""
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await self.bot.say('Already in a voice channel.')
        except discord.InvalidArgument:
            await self.bot.say('This is not a voice channel.')
        else:
            await self.bot.say('Ready to play audio in ' + channel.name)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to your voice channel."""
        summoned_channel = ctx.message.author.voice_channel
        author = ctx.message.author
        if summoned_channel is None:
            await self.bot.say('Sorry {0.mention}, you need to be in a voice channel for that command.\nYou can use "join <channel name>" to send me somewhere.'.format(author))
            return False

        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)

        return True

    @commands.command(pass_context=True, no_pm=True)
    async def play(self, ctx, *, song : str):
        """Plays a song. Can be a YouTube URL or search."""
        await self.bot.say('`Request submitted!`'.format(song))

        state = self.get_voice_state(ctx.message.server)
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        try:
            player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```Please let Luci know if this is a major problem.'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = 0.5
            entry = VoiceEntry(ctx.message, player)
            embed = discord.Embed(title = "Queued:", description = str(entry), color = Style.Colors.orange)
            await self.bot.say(embed=embed)
            await state.songs.put(entry)

    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value : int):
        """Sets the volume."""

        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.volume = value / 100
            await self.bot.say('The volume is now set to: {:.0%}'.format(player.volume))

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()
            await self.bot.say('Paused...')

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()
            await self.bot.say('Resumed...')

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):

        """Stops the current song and clears queue."""
        server = ctx.message.server
        state = self.get_voice_state(server)

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator

        if isAdmin:
            if state.is_playing():
                player = state.player
                player.stop()
                await self.bot.say('Song stopped and queue cleared.')

            try:
                state.audio_player.cancel()
                del self.voice_states[server.id]
                await state.voice.disconnect()
                await self.bot.say('Leaving voice channel...')
            except:
                pass

        if not isAdmin:
            await self.bot.say('Sorry! You need to be an admin to use that command.')

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song."""
        state = self.get_voice_state(ctx.message.server)

        if not state.is_playing():
            await self.bot.say('Leaving voice channel...')
            player = state.player
            player.stop()
            state.audio_player.cancel()
            del self.voice_states[ctx.message.server.id]
            await state.voice.disconnect()
        else:
            await self.bot.say('Skipping song...')
            state.skip()

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """Displays the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not currently playing anything.')
        else:
            skip_count = len(state.skip_votes)
            embed = discord.Embed(title = "Currently Playing:", description = '{}\nSkips: {}/{}'.format(state.current, skip_count, self.votes_needed), color = Style.Colors.green)
            await self.bot.say(embed=embed)

    # @commands.command(pass_context=True, no_pm=True)
    # async def setvotesneeded(self, ctx, votes_needed : int):
    #     """Set votes needed to skip a song. (Admin only)"""
    #     isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator

    #     if isAdmin:
    #     	self.votes_needed = votes_needed
    #     	await self.bot.say('Votes needed to skip is now: {}'.format(votes_needed))

    #     if not isAdmin:
    #     	await self.bot.say('Sorry! You need to be an admin to use that command.')