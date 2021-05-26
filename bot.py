import os
import discord
from discord.ext import commands
import psycopg2

TOKEN = os.environ['DISCORD_TOKEN']
GUILD = os.environ['DISCORD_GUILD']
COMMAND_PREFIX = '!'
BOT_NAME = 'QuoteBot'

HOST=os.environ['HOST']
DATABASE=os.environ['DATABASE']
USERNAME=os.environ['USERNAME']
PASSWORD=os.environ['PASSWORD']

DB_TABLE = 'quotes'
DB_COL_AUTHOR = 'author'
DB_COL_QUOTE = 'quote_said'

intents = discord.Intents.default()
intents.guild_messages = True
intents.messages = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX,intents=intents)

@bot.event
async def on_message(message):
    if message.channel.name != 'quotes':
        return
    if message.author.name == BOT_NAME:
        return
    if message.content.startswith(COMMAND_PREFIX):
        await bot.process_commands(message)
    else:
        quote = validateQuoteFormat(message.content)
        if(quote == None):
            return
        insertQuote(quote[0],quote[1])
    

@bot.command(name='quote', help='Responds with a random quote from any user')
async def quote(ctx):
    row = selectAnyQuote()
    if row != None:
        author = row[0]
        quote = row[1]
        formattedResponse = '"' + quote + '"' + " - " + author
        await ctx.send(formattedResponse)
    else:
        await ctx.send("No quotes have been added yet.")
 
        

@bot.command(name='quotefrom', help='Responds with a random quote from the specified user')
async def quote(ctx,quote_author):
    if checkPersonHasQuote(quote_author.lower()):
        row = selectPersonQuote(quote_author.lower())
        author = row[0]
        quote = row[1]
        formattedResponse = '"' + quote + '"' + " - " + author
        await ctx.send(formattedResponse)
    else:
        await ctx.send("No quotes have been added for this person yet.")


@bot.command(name='addhistory',help="Adds quotes from the message history of this channel. If used multiple times, the same quotes will be readded")
@commands.has_role('OG Loser Bois')
async def addHistoricalQuotes(ctx):
    messages = await ctx.channel.history(limit=1000).flatten()
    for message in messages:
        quote = validateQuoteFormat(message.content)
        if(quote != None):
            insertQuote(quote[0],quote[1])
    await message.channel.send("Quotes successfully added!")

def validateQuoteFormat(message):
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
    return (quote,author)

def establishDBConnection():
    return  psycopg2.connect(
    host=HOST,
    database=DATABASE,
    user=USERNAME,
    password=PASSWORD)

def insertQuote(quote,author):
    conn = establishDBConnection()
    cur = conn.cursor()
    cur.execute(f"INSERT INTO {DB_TABLE}({DB_COL_AUTHOR}, {DB_COL_QUOTE}) VALUES  (\'{author}\', \'{quote}\');")
    conn.commit()
    conn.close()

def selectAnyQuote():
    conn = establishDBConnection()
    cur = conn.cursor()
    cur.execute(f"SELECT {DB_COL_AUTHOR},{DB_COL_QUOTE} FROM {DB_TABLE} ORDER BY random() LIMIT 1;")
    row = cur.fetchone()
    conn.close()
    return row

def checkPersonHasQuote(author):
    conn = establishDBConnection()
    cur = conn.cursor()
    cur.execute(f"SELECT EXISTS(SELECT 1 FROM {DB_TABLE} WHERE {DB_COL_AUTHOR} = \'{author}\')")
    row = cur.fetchone()
    print(row)
    conn.close()
    return row

def selectPersonQuote(author):
    conn = establishDBConnection()
    cur = conn.cursor()
    cur.execute(f"SELECT {DB_COL_AUTHOR},{DB_COL_QUOTE} FROM {DB_TABLE} WHERE {DB_COL_AUTHOR} = \'{author}\' ORDER BY random() LIMIT 1;")
    row = cur.fetchone()
    conn.close()
    return row


bot.run(TOKEN)