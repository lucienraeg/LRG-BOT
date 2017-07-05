import asyncio
import discord
from discord.ext import commands

class Main:

	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True, no_pm=True)
	async def ping(self, ctx):
		"""Replies with Pong! (For testing purposes)"""
		await self.bot.say("Pong!")