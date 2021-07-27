import os
import discord
from discord.ext import commands
from discord.utils import get
import botdb.quotebotdb as botdb
from domain.quoteinfo import QuoteInfo
from domain.validatedquote import ValidatedQuote
import configparser

TOKEN = os.environ['DISCORD_TOKEN']
GUILD = os.environ['DISCORD_GUILD']

config = configparser.ConfigParser()
config.read('config.ini')
COMMAND_PREFIX = config['BotInfo']['CommandPrefix']
BOT_NAME = config['BotInfo']['BotName']
QUOTE_CHANNEL = config['BotInfo']['QuoteChannel']
QUOTES_PULL_CHANNEL = config['BotInfo']['QuotePullChannel']

LEADERBOARD_NUM_QUOTES = int(config['BotInfo']['leaderboardQuoteAmount'])
LIKE_EMOTE=config['BotInfo']['likeEmote']
INTERESTING_EMOTE=config['BotInfo']['interestingEmote']

def botSetup():
    intents = discord.Intents.default()
    intents.members = True
    intents.guild_messages = True
    intents.messages = True
    return commands.Bot(command_prefix=COMMAND_PREFIX,intents=intents)

bot = botSetup()

@bot.event
async def on_message(message):
    if message.author.name == BOT_NAME:
        return
    if message.channel.name == QUOTE_CHANNEL:
        if message.content == (COMMAND_PREFIX + "addhistory"):
            await bot.process_commands(message)
        else:
            validQuote = validate_quote_format(message.content)
            if(validQuote == None):
                return
            botdb.add_new_quote(validQuote.author,validQuote.quote)
    if message.channel.name == QUOTES_PULL_CHANNEL:    
        if message.content.startswith(COMMAND_PREFIX):
            await bot.process_commands(message)

@bot.command(name='quote', help='Responds with a random quote from any user')
async def quote(ctx):
    quoteInfo = botdb.select_any_quote()
    if quoteInfo != None:
        message = await ctx.send(repr(quoteInfo))
        await message.add_reaction(LIKE_EMOTE)
        await message.add_reaction(INTERESTING_EMOTE)
    else:
        await ctx.send("No quotes have been added yet.")

@bot.command(name='quotefrom', help='Responds with a random quote from the specified user')
async def quote_from(ctx,quote_author):
    if botdb.check_person_has_quote(quote_author.lower()):
        quoteInfo = botdb.select_person_quote(quote_author.lower())
        message = await ctx.send(repr(quoteInfo))
        await message.add_reaction(LIKE_EMOTE)
        await message.add_reaction(INTERESTING_EMOTE)
    else:
        await ctx.send("No quotes have been added for this person yet.")

@bot.command(name="delete", help="Deletes a quote with the given id")
async def delete_quote(ctx, quote_id : int):
    if(botdb.select_quote_by_id(quote_id) == None):
        await ctx.send("A quote with the given id could not be found.")
    else:
        botdb.delete_quote_by_id(quote_id)
        await ctx.send("The quote was successfully deleted!")

@bot.command(name='leaderboard', help='Returns the top 10 liked quotes')
async def leaderboard(ctx):
    leaderboard = ""
    top_quotes = botdb.get_top_liked_quotes(LEADERBOARD_NUM_QUOTES)
    place_on_leaderboard = 1
    for quote in top_quotes:
        quote_format = QuoteInfo(quote).like_leaderboard_format()
        leaderboard += f"#{place_on_leaderboard} {quote_format}\n"
        place_on_leaderboard += 1
    await ctx.send(leaderboard)

@bot.command(name='interesting', help='Returns the top 10 interesting quotes')
async def interesting_leaderboard(ctx):
    leaderboard = ""
    top_quotes = botdb.get_top_interesting_quotes(LEADERBOARD_NUM_QUOTES)
    place_on_leaderboard = 1
    for quote in top_quotes:
        quote_format = QuoteInfo(quote).interesting_leaderboard_format()
        leaderboard += f"#{place_on_leaderboard} {quote_format}\n"
        place_on_leaderboard += 1
    await ctx.send(leaderboard)


@bot.event
async def on_message_edit(before, after):
    prevQuote = validate_quote_format(before.content)
    if(prevQuote != None):
        botdb.delete_quote_by_quote_and_author(prevQuote.quote,prevQuote.author)
    newQuote = validate_quote_format(after.content)
    if(newQuote != None):
        botdb.add_new_quote(newQuote.quote,newQuote.author)

@bot.event
async def on_message_delete(message):
    prevQuote = validate_quote_format(message.content)
    if(prevQuote != None):
        botdb.delete_quote_by_quote_and_author(prevQuote.quote,prevQuote.author)

async def get_discord_message(channel_id,message_id):
    channel = bot.get_channel(channel_id)
    message = await channel.fetch_message(message_id)
    if not message:
        return
    if message.author.name != BOT_NAME:
        return
    return message;

def get_reaction_count(message,emoji):
    reaction = get(message.reactions, emoji=emoji)
    if not reaction:
        return
    return reaction.count-1

def get_id_of_quote(quote):
    quote_id = quote.split(':')[-1].split(')')[0].strip()
    if not quote_id.isnumeric():
        return
    return int(quote_id)

def get_quote_by_id(quote_id):
    if(not quote_id):
        return
    if not botdb.check_quote_exists_by_id(quote_id):
        return
    return botdb.select_quote_by_id(quote_id)

def get_quote_and_reaction_count(message,emoji):
    current_count = get_reaction_count(message,emoji)
    quote_id = get_id_of_quote(message.content)
    if(not current_count or not quote_id):
        return
    quote = get_quote_by_id(quote_id)
    if(not quote):
        return
    return current_count,quote

async def like_reaction_add(channel_id,message_id,emoji):
    message = get_discord_message(channel_id,message_id)
    count_and_quote = get_quote_and_reaction_count(message,emoji)
    if(not count_and_quote):
        return
    current_count,quote = count_and_quote
    if(current_count > quote.like):
        botdb.update_like_score_of_quote(quote.quote_id,current_count)
        quote.like = current_count
        new_message = repr(quote)
        await message.edit(content=new_message)

async def interesting_reaction_add(channel_id,message_id,emoji):
    message = get_discord_message(channel_id,message_id)
    count_and_quote = get_quote_and_reaction_count(message,emoji)
    if(not count_and_quote):
        return
    current_count,quote = count_and_quote
    if(current_count > quote.interesting):
        botdb.update_interesting_score_of_quote(quote.quote_id,current_count)
        quote.interesting = current_count
        new_message = repr(quote)
        await message.edit(content=new_message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.name == BOT_NAME:
        return
    channel_id = payload.channel_id
    message_id = payload.message_id
    emoji = payload.emoji.name
    if payload.emoji.name == LIKE_EMOTE:
        like_reaction_add(channel_id,message_id,emoji)
    if payload.emoji.name == INTERESTING_EMOTE:
        interesting_reaction_add(channel_id,message_id,emoji)
   
# @bot.command(name='addhistory',help="Adds quotes from the message history of this channel")
async def add_historical_quotes(ctx):
    messages = await ctx.channel.history(limit=2000).flatten()
    for message in messages:
        if message.author.name == BOT_NAME:
            continue
        validQuote = validate_quote_format(message.content)
        if(validQuote != None):
            botdb.add_new_quote(validQuote.quote,validQuote.author)
    await message.channel.send("Quotes successfully added!")

def validate_quote_format(message: str) -> 'ValidatedQuote':
    if ";" in message:
        return
    if not message.startswith('"'):
        return None
    if len(message.split('"')) != 3:
        return None
    quote = message.split('"')[1]
    if len(message.split('-')) != 2:
        return None
    author = message.split('-')[1].strip().lower()
    if len(author.split()) != 1:
        return None
    quote = quote.replace("'","''")
    author = author.replace("'","''")
    return ValidatedQuote(quote,author)

        
bot.run(TOKEN)