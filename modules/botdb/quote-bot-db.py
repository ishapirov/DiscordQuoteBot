import os
import psycopg2
from domain.quoteinfo import QuoteInfo;
import configparser

HOST=os.environ['HOST']
DATABASE=os.environ['DATABASE']
USERNAME=os.environ['USERNAME']
PASSWORD=os.environ['PASSWORD']

config = configparser.ConfigParser()
config.read('dbconfig.ini')
DB_TABLE = config['Table']
DB_COL_QID = config['colQuoteId']
DB_COL_AUTHOR = config['colAuthor']
DB_COL_QUOTE = config['colQuote']
DB_COL_LIKE_SCORE = config['colLikeScore']
DB_COL_INTERESTING_SCORE = config['colInterestingScore']

def establish_db_Connection():
    return  psycopg2.connect(
    host=HOST,
    database=DATABASE,
    user=USERNAME,
    password=PASSWORD)

def add_new_quote(quote,author) -> None:
    if not check_quote_exists_by_quote_and_author(quote,author):
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
    cur.execute(f"SELECT {DB_COL_QID},{DB_COL_AUTHOR},{DB_COL_QUOTE},{DB_COL_LIKE_SCORE},{DB_COL_INTERESTING_SCORE} FROM {DB_TABLE} WHERE {DB_COL_QID} = {quote_id};")
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