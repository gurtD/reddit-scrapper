# reddit-scrapper
A scrapper/notification script for reddit, created to run from a cron job to run every 5 min. It checks the specified subreddit for the specified search (64 and 65 in scrapper.py)
and sends out a text using twilio when a new post is found. Its connected to a postgres sql db in order to keep track of posts that have already been seen. Using it personally for 
market place subreddits when looking for specific items
