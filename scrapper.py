#! python3
from dotenv import load_dotenv
import praw
import pandas as pd
import datetime as dt
import os
import psycopg2
import send_sms

# load env vars, most of which are credentials
load_dotenv()

def single_insert(conn, insert_req):
    """ Execute a single INSERT request """
    cursor = conn.cursor()
    try:
        cursor.execute(insert_req)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    cursor.close()


def make_table(conn):
    """ Makes table in DB """
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE posts(
    id text PRIMARY KEY,
    url text,
    title text,
    score integer,
    comms_num integer,
    created float,
    body text)"""),

    conn.commit()
    cursor.close()

def post_exists(conn, post_id):
    """ Checks DB if post has been seen """
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM posts WHERE id = %s", (post_id,))
    return cursor.fetchone() is not None

# create connection to db
connection = psycopg2.connect(
    host = os.getenv("DB_HOST"),
    port = os.getenv("DB_PORT"),
    user = os.getenv("DB_USER"),
    password = os.getenv("DB_PSWD"),
    database=os.getenv("DB_NAME")
    )
# create reddit client object
reddit = praw.Reddit(client_id=os.getenv("REDDIT_CLIENT_ID"), \
                     client_secret=os.getenv("REDDIT_CLIENT_SECRET"), \
                     user_agent=os.getenv("REDDIT_USER_AGENT"), \
                     username=os.getenv("REDDIT_USERNAME"), \
                     password=os.getenv("REDDIT_PSWD"))

# specifiy subreddit and search criteria, and send request
subreddit = reddit.subreddit(os.getenv("REDDIT_SUBREDDIT"))
search_subreddit = subreddit.search(os.getenv("REDDIT_SEARCH"), sort='new', time_filter='day')

# organize data and place it into a panda dataframe
topics_dict = { "id":[],  \
                "url":[], \
                "title":[], \
                "score":[], \
                "comms_num": [], \
                "created": [], \
                "body":[]}

for submission in search_subreddit:
    topics_dict["id"].append(submission.id)
    topics_dict["url"].append(submission.url)
    # XXX i have no idea how to fix issues with commas. I tried to escape
    # the commas to no avail so screw the em, im just gonna replace 
    # them
    topics_dict["title"].append( (submission.title).replace(",", " ").replace("'", "''") )
    topics_dict["score"].append(submission.score)
    topics_dict["comms_num"].append(submission.num_comments)
    topics_dict["created"].append(submission.created)
    topics_dict["body"].append((submission.selftext).replace(",", " ").replace("\n", " ").replace("'", "''"))

dataframe = pd.DataFrame(topics_dict)

table_made = True
if not table_made:
    make_table(connection)

# Inserting each row into db
for i in dataframe.index:
    if not post_exists(connection, dataframe['id'][i]):
        print("New entry: Adding %s db" % (dataframe['id'][i]))
        query = """
        INSERT INTO posts(id, url, title, score, comms_num, created, body) VALUES('%s','%s','%s',%s,%s,%s,'%s');
        """ % (dataframe['id'][i], dataframe['url'][i], dataframe['title'][i], dataframe['score'][i], dataframe['comms_num'][i], dataframe['created'][i], dataframe['body'][i])
        single_insert(connection, query)
        print("Texting about new post")
        send_sms.send("New post: %s" % (dataframe['url'][i]))

    else: 
        print("Entry exists in db, skipping")

# Close the connection
connection.close()


