import os
import discord
from discord.ext import commands
import psycopg2

TOKEN = os.environ['DISCORD_TOKEN']
GUILD = os.environ['DISCORD_GUILD']
COMMAND_PREFIX = '!'
BOT_NAME = 'QuoteBot'

HOST=os.environ['DATABASE_URL']
DATABASE=os.environ['DATABASE']
USERNAME=os.environ['USERNAME']
PASSWORD=os.environ['PASSWORD']

DB_TABLE = 'quotes'
DB_COL_QID = 'quote_id'
DB_COL_AUTHOR = 'author'
DB_COL_QUOTE = 'quote_said'

intents = discord.Intents.default()
intents.guild_messages = True
intents.messages = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX,intents=intents)

@bot.event
async def on_message(message):
    if message.channel.name != 'quotes' and message.channel.name != 'quotes-pull':
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
        formattedResponse = formatQuote(row)
        await ctx.send(formattedResponse)
    else:
        await ctx.send("No quotes have been added yet.")

@bot.command(name='quotefrom', help='Responds with a random quote from the specified user')
async def quote(ctx,quote_author):
    if checkPersonHasQuote(quote_author.lower()):
        row = selectPersonQuote(quote_author.lower())
        formattedResponse = formatQuote(row)
        await ctx.send(formattedResponse)
    else:
        await ctx.send("No quotes have been added for this person yet.")

@bot.command(name="delete", help="Deletes a quote with the given id")
async def delete_quote(ctx, quote_id : int):
    if(selectQuoteByID(quote_id) == None):
        ctx.send("A quote with the given id could not be found.")
    else:
        deleteQuoteByID(quote_id)
        ctx.send("The quote was successfully deleted!")

@bot.event
async def on_message_edit(before, after):
    prevQuote = validateQuoteFormat(before.content)
    if(prevQuote != None):
        deleteQuoteByQuoteAndAuthor(prevQuote[0],prevQuote[1])
    newQuote = validateQuoteFormat(after.content)
    if(newQuote != None):
        insertQuote(newQuote[0],newQuote[1])

@bot.event
async def on_message_delete(message):
    prevQuote = validateQuoteFormat(message.content)
    if(prevQuote != None):
        deleteQuoteByQuoteAndAuthor(prevQuote[0],prevQuote[1])

# @bot.command(name='addhistory',help="Adds quotes from the message history of this channel. If used multiple times, the same quotes will be readded")
# @commands.has_role('OG Loser Bois')
async def addHistoricalQuotes(ctx):
    messages = await ctx.channel.history(limit=2000).flatten()
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


def formatQuote(row):
    quote_id = row[0]
    author = row[1]
    quote = row[2]
    return f"({quote_id}) \"{quote}\" - {author}"
    
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

def selectQuoteByID(quote_id : int):
    conn = establishDBConnection()
    cur = conn.cursor()
    cur.execute(f"SELECT {DB_COL_QID},{DB_COL_AUTHOR},{DB_COL_QUOTE} FROM {DB_TABLE} WHERE {DB_COL_QID} = {quote_id};")
    row = cur.fetchone()
    conn.close()
    return row

def selectAnyQuote():
    conn = establishDBConnection()
    cur = conn.cursor()
    cur.execute(f"SELECT {DB_COL_QID},{DB_COL_AUTHOR},{DB_COL_QUOTE} FROM {DB_TABLE} ORDER BY random() LIMIT 1;")
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
    cur.execute(f"SELECT {DB_COL_QID},{DB_COL_AUTHOR},{DB_COL_QUOTE} FROM {DB_TABLE} WHERE {DB_COL_AUTHOR} = \'{author}\' ORDER BY random() LIMIT 1;")
    row = cur.fetchone()
    conn.close()
    return row

def deleteQuoteByQuoteAndAuthor(quote,author):
    conn = establishDBConnection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {DB_TABLE} WHERE {DB_COL_QUOTE} = \'{quote}\' AND {DB_COL_AUTHOR} = \'{author}\';")
    conn.commit()
    conn.close()

def deleteQuoteByID(quote_id):
    conn = establishDBConnection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {DB_TABLE} WHERE {DB_COL_QID} = {quote_id};")
    conn.commit()
    conn.close()



bot.run(TOKEN)