import asyncio
import discord
import time
from   discord.ext import commands
from cogs import readabletime as ReadableTime
from cogs import style as Style

class BotInfo:

	def __init__(self, bot):
		self.bot = bot
		self.startTime = int(time.time())

	@commands.command(pass_context=True)
	async def uptime(self, ctx):
		"""Displays the bot's uptime."""
		currentTime = int(time.time())
		timeString  = ReadableTime.getReadableTimeBetween(self.startTime, currentTime)
		msg = "I've been up for *{}*.".format(timeString)
		await self.bot.say(msg)


class ServerInfo:

	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def serverinfo(self, ctx):
		"""Displays server information."""
		server = ctx.message.server
		embed = discord.Embed(title = server.name, color=Style.Colors.blue)

		# general
		embed.add_field(name="General", value="Owner: {}\nMembers: {}\nRegion: {}\nChannels: {}\nAFK Timeout: {}\nLarge: {}\nVerification Level: {}\nDefault Role: {}".format(server.owner.name, server.member_count, str(server.region).title(), len(server.channels), server.afk_timeout, server.large, str(server.verification_level).title(), server.default_role), inline=False)

		# roles
		roles = []
		for role in server.role_hierarchy:
			role_entry = role.name
			if role.hoist:
				role_entry = role_entry + "*"
			if role.permissions.administrator:
				role_entry = role_entry + " (Admin)"
			roles.append(role_entry)

		roles_display = '\n'.join(roles)

		embed.add_field(name="Roles", value="{}".format(roles_display), inline=False)

		# emoji
		emojis = []
		for emoji in server.emojis:
			emoji_entry = "{}".format(emoji.name)

			emojis.append(emoji_entry)

		emojis_display = '\n'.join(emojis)

		embed.add_field(name="Emojis", value="{}".format(emojis_display), inline=False)

		
		# # extra
		embed.set_footer(text="Server ID: {}".format(server.id))

		await self.bot.say(embed=embed)