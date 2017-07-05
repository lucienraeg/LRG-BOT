import asyncio
import discord
import time
from   discord.ext import commands
from cogs import readabletime as ReadableTime

class BotInfo:

	def __init__(self, bot):
		self.bot = bot
		self.startTime = int(time.time())

	@commands.command(pass_context=True)
	async def uptime(self, ctx):
		"""Lists the bot's uptime."""
		currentTime = int(time.time())
		timeString  = ReadableTime.getReadableTimeBetween(self.startTime, currentTime)
		msg = "I've been up for *{}*.".format(timeString)
		await self.bot.say(msg)


class ServerInfo:

	def __init__(self, bot):
		self.bot = bot