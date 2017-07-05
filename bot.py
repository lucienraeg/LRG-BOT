import asyncio
import discord
from discord.ext import commands
import logging

# importing cogs
from cogs import main as Main
from cogs import music as Music
from cogs import meta as Meta

# getting opus (for voice)
if not discord.opus.is_loaded():
	print("Loading Opus...")
    discord.opus.load_opus('opus')

# logging config
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)

# file handler for ALL logs
log_full = logging.FileHandler('log_full.log', encoding='utf-8', mode='w')
log_full.setLevel(logging.DEBUG)

# file handler for ERROR and CRITICAL level logs
log_critical = logging.FileHandler('log_critical.log', encoding='utf-8', mode='w')
log_critical.setLevel(logging.INFO)

# console logger
log = logging.StreamHandler()
log.setLevel(logging.DEBUG) 

# create format
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
log_full.setFormatter(formatter)
log_critical.setFormatter(formatter)
log.setFormatter(formatter)

# add the handlers to logger
logger.addHandler(log_full)
logger.addHandler(log_critical)
logger.addHandler(log)

# configure bot
bot_prefix = "$"
bot = commands.Bot(command_prefix=bot_prefix)

# process cogs
cogList = []

cogList.append(Main.Main(bot))
cogList.append(Music.Music(bot))
cogList.append(Meta.BotInfo(bot))
cogList.append(Meta.ServerInfo(bot))

# add all cogs to bot object
for cog in cogList:
	print('Cog Added: {}'.format(cog))
	bot.add_cog(cog)

# ***** EVENTS *****

@bot.event
async def on_ready():
    print("Bot online!")
    print("Name: {}".format(bot.user.name))
    print("ID: {}".format(bot.user.id))
    await bot.change_presence(game=discord.Game(name="tell Luci if I stuff up".format(bot_prefix)))

@bot.event
async def on_member_join(member):
	server = member.server
	fmt = "Welcome {0.mention} to our lovely community!"
	await bot.send_message(server, fmt.format(member))

@bot.event
async def on_reaction_add(reaction, user):
	if reaction.emoji.name == "AbbyLouise":
		server = reaction.message.server
		await bot.send_message(server, "Hey that's me!")


# run
token = "MzAzNDg4MzQ4OTU2MTMxMzI4.DDu92w.K7M7-st4w2YAKEatji8KVOhMJwk"
bot.run(token)