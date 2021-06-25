import os
import discord
from discord.ext import commands
from discord.utils import get
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
DB_COL_QID = 'quote_id'
DB_COL_AUTHOR = 'author'
DB_COL_QUOTE = 'quote_said'
DB_COL_LIKE_SCORE = 'like_score'
DB_COL_INTERESTING_SCORE = 'interesting_score'

LEADERBOARD_NUM_QUOTES = 10
LIKE_EMOTE='👍'
INTERESTING_EMOTE='👀'

intents = discord.Intents.default()
intents.members = True
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
        validQuote = validate_quote_format(message.content)
        if(validQuote == None):
            return
        add_new_quote(validQuote.author,validQuote.quote)
    

@bot.command(name='quote', help='Responds with a random quote from any user')
async def quote(ctx):
    quoteInfo = select_any_quote()
    if quoteInfo != None:
        message = await ctx.send(repr(quoteInfo))
        await message.add_reaction(LIKE_EMOTE)
        await message.add_reaction(INTERESTING_EMOTE)
    else:
        await ctx.send("No quotes have been added yet.")

@bot.command(name='quotefrom', help='Responds with a random quote from the specified user')
async def quote_from(ctx,quote_author):
    if check_person_has_quote(quote_author.lower()):
        quoteInfo = select_person_quote(quote_author.lower())
        message = await ctx.send(repr(quoteInfo))
        message.add_reaction(LIKE_EMOTE)
        message.add_reaction(INTERESTING_EMOTE)
    else:
        await ctx.send("No quotes have been added for this person yet.")

@bot.command(name="delete", help="Deletes a quote with the given id")
async def delete_quote(ctx, quote_id : int):
    if(select_quote_by_id(quote_id) == None):
        await ctx.send("A quote with the given id could not be found.")
    else:
        delete_quote_by_id(quote_id)
        await ctx.send("The quote was successfully deleted!")

@bot.command(name='leaderboard', help='Returns the top 10 liked quotes')
async def leaderboard(ctx):
    leaderboard = ""
    top_quotes = get_top_liked_quotes(LEADERBOARD_NUM_QUOTES)
    place_on_leaderboard = 1
    for quote in top_quotes:
        quote_format = QuoteInfo(quote).like_leaderboard_format()
        leaderboard += f"#{place_on_leaderboard} {quote_format}\n"
        place_on_leaderboard += 1
    await ctx.send(leaderboard)

@bot.command(name='interesting', help='Returns the top 10 interesting quotes')
async def interesting_leaderboard(ctx):
    leaderboard = ""
    top_quotes = get_top_liked_quotes(LEADERBOARD_NUM_QUOTES)
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
        delete_quote_by_quote_and_author(prevQuote.quote,prevQuote.author)
    newQuote = validate_quote_format(after.content)
    if(newQuote != None):
        add_new_quote(newQuote.quote,newQuote.author)

@bot.event
async def on_message_delete(message):
    prevQuote = validate_quote_format(message.content)
    if(prevQuote != None):
        delete_quote_by_quote_and_author(prevQuote.quote,prevQuote.author)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.name == BOT_NAME:
        return
    if payload.emoji.name == LIKE_EMOTE:
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if not message:
            return
        if message.author.name != BOT_NAME:
            return
        reaction = get(message.reactions, emoji=payload.emoji.name)
        if reaction:
            current_count = reaction.count-1
            quote_id_str = message.content.split()[0][1:-1]
            if not quote_id_str.isnumeric():
                return
            quote_id = int(quote_id_str)
            if not check_quote_exists_by_id(quote_id):
                return
            quote = select_quote_by_id(quote_id)
            if(current_count > quote.like):
                update_like_score_of_quote(quote_id,current_count)
            new_message = f"{message.content[0:-1]}{current_count}"
        await message.edit(content=new_message)
    if payload.emoji.name == INTERESTING_EMOTE:
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if not message:
            return
        if message.author.name != BOT_NAME:
            return
        reaction = get(message.reactions, emoji=payload.emoji.name)
        if reaction:
            current_count = reaction.count-1
            quote_id_str = message.content.split()[0][1:-1]
            if not quote_id_str.isnumeric():
                return
            quote_id = int(quote_id_str)
            if not check_quote_exists_by_id(quote_id):
                return
            quote = select_quote_by_id(quote_id)
            if(current_count > quote.interesting):
                update_interesting_score_of_quote(quote_id,current_count)
            new_message = f"{message.content[0:-1]}{current_count}"
        await message.edit(content=new_message)
   


# @bot.command(name='addhistory',help="Adds quotes from the message history of this channel")
async def add_historical_quotes(ctx):
    messages = await ctx.channel.history(limit=2000).flatten()
    for message in messages:
        if message.author.name == BOT_NAME:
            continue
        validQuote = validate_quote_format(message.content)
        if(validQuote != None):
            add_new_quote(validQuote.quote,validQuote.author)
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
    
def establish_db_Connection():
    return  psycopg2.connect(
    host=HOST,
    database=DATABASE,
    user=USERNAME,
    password=PASSWORD)

def add_new_quote(quote,author) -> None:
    if not check_quote_exists_by_quote_and_author(quote,author)[0]:
        insert_quote(quote,author)

def insert_quote(quote,author):
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"INSERT INTO {DB_TABLE}({DB_COL_AUTHOR}, {DB_COL_QUOTE}, {DB_COL_LIKE_SCORE}, {DB_COL_INTERESTING_SCORE}) VALUES  ('{author}', '{quote}', 0, 0);")
    conn.commit()
    conn.close()

def select_quote_by_id(quote_id : int) -> 'QuoteInfo':
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"SELECT {DB_COL_QID},{DB_COL_AUTHOR},{DB_COL_QUOTE},{DB_COL_LIKE_SCORE},DB_COL_INTERESTING_SCORE FROM {DB_TABLE} WHERE {DB_COL_QID} = {quote_id};")
    row = cur.fetchone()
    conn.close()
    return get_quote_info_from_row(row)

def select_person_quote(author):
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"SELECT {DB_COL_QID},{DB_COL_AUTHOR},{DB_COL_QUOTE},{DB_COL_LIKE_SCORE},{DB_COL_INTERESTING_SCORE} FROM {DB_TABLE} WHERE {DB_COL_AUTHOR} = \'{author}\' ORDER BY random() LIMIT 1;")
    row = cur.fetchone()
    conn.close()
    return get_quote_info_from_row(row) 

def select_any_quote() -> 'QuoteInfo':
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"SELECT {DB_COL_QID},{DB_COL_AUTHOR},{DB_COL_QUOTE},{DB_COL_LIKE_SCORE},{DB_COL_INTERESTING_SCORE} FROM {DB_TABLE} ORDER BY random() LIMIT 1;")
    row = cur.fetchone()
    conn.close()
    return get_quote_info_from_row(row)

def check_person_has_quote(author) -> bool:
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"SELECT EXISTS(SELECT 1 FROM {DB_TABLE} WHERE {DB_COL_AUTHOR} = \'{author}\')")
    row = cur.fetchone()
    conn.close()
    return row[0]

def check_quote_exists_by_id(quote_id):
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"SELECT EXISTS(SELECT 1 FROM {DB_TABLE} WHERE {DB_COL_QID} = {quote_id})")
    row = cur.fetchone()
    conn.close()
    return row[0]

def check_quote_exists_by_quote_and_author(quote,author):
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"SELECT EXISTS(SELECT 1 FROM {DB_TABLE} WHERE {DB_COL_AUTHOR} = \'{author}\' AND {DB_COL_QUOTE} = \'{quote}\')")
    row = cur.fetchone()
    conn.close()
    return row[0]

def update_like_score_of_quote(quote_id,new_score):
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE {DB_TABLE} SET {DB_COL_LIKE_SCORE}={new_score} WHERE {DB_COL_QID} = {quote_id}")
    conn.commit()
    conn.close()

def update_interesting_score_of_quote(quote_id,new_score):
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE {DB_TABLE} SET {DB_COL_INTERESTING_SCORE}={new_score} WHERE {DB_COL_QID} = {quote_id}")
    conn.commit()
    conn.close()

def get_top_liked_quotes(number_of_quotes):
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {DB_TABLE} ORDER BY {DB_COL_LIKE_SCORE} DESC LIMIT {number_of_quotes}")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_top_interesting_quotes(number_of_quotes):
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {DB_TABLE} ORDER BY {DB_COL_INTERESTING_SCORE} DESC LIMIT {number_of_quotes}")
    rows = cur.fetchall()
    conn.close()
    return rows
    

def delete_quote_by_quote_and_author(quote,author):
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {DB_TABLE} WHERE {DB_COL_QUOTE} = \'{quote}\' AND {DB_COL_AUTHOR} = \'{author}\';")
    conn.commit()
    conn.close()

def delete_quote_by_id(quote_id):
    conn = establish_db_Connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {DB_TABLE} WHERE {DB_COL_QID} = {quote_id};")
    conn.commit()
    conn.close()

def get_quote_info_from_row(row) -> 'QuoteInfo':
    if(row == None):
        return None
    return QuoteInfo(row)

class ValidatedQuote:
    def __init__(self,author,quote: tuple):
        self.author = author
        self.quote = quote

class QuoteInfo:
    def __init__(self,row: tuple):
        self.quote_id = row[0]
        self.author = row[1].capitalize()
        self.quote = row[2]
        self.like = row[3]
        self.interesting = row[4]

    def like_leaderboard_format(self) -> str:
        return f"Likes: {self.like}) \"{self.quote}\" - {self.author} (ID: {self.quote_id})"

    def interesting_leaderboard_format(self) -> str:
        return f"Interesting Score: {self.interesting}) \"{self.quote}\" - {self.author} (ID:{self.quote_id})"

    def __repr__(self) -> str:
        return f"\"{self.quote}\" - {self.author}\nLike Score: {self.like}, Interesting Score: {self.interesting} (ID: {self.quote_id})"
        
        
bot.run(TOKEN)