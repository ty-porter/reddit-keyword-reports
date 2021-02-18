import json, os, praw, time
from datetime import datetime as dt
from psaw import PushshiftAPI as pushshift

from data.types import *

# Try to import our config class, otherwise just stub it so it doesn't accidentally break
try:
    from env import Config
except ImportError:
    from stub_env import Config

class Bot:

    __CONFIG_PATH = 'config.json'
    __LAST_RUN    = -1 # Never
    
    with open('VERSION') as version:
        VERSION = version.read()

    def __init__(self):
        self.reddit = self.load_reddit()
        self.pushshift = pushshift()
        self.load_configuration(self.__CONFIG_PATH)

    def load_reddit(self):
        # Check where the script is running. If it's on a local machine, set the vars needed.
        # Otherwise, continue on, assuming these vars are set on Heroku.
        if 'SCRIPT_ENV' not in os.environ or os.environ['SCRIPT_ENV'] in ['test', 'development']:
            Config.set_env_vars()

        reddit = praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'],
                             client_secret=os.environ['REDDIT_CLIENT_SECRET'],
                             user_agent=os.environ['REDDIT_USER_AGENT'],
                             username=os.environ['REDDIT_USERNAME'],
                             password=os.environ['REDDIT_PASSWORD'])

        return reddit

    def run(self):
        utc_time  = dt.utcnow()
        curr_time = int(dt.timestamp(utc_time))

        if self.__LAST_RUN < curr_time - self.settings.delay:
            results = self.query_keywords()
            self.__LAST_RUN = curr_time

            
            date_str = dt.utcnow().strftime('%d/%m/%Y')
            title = 'Keyword Report {}'.format(date_str)
            text = self.build_results_text(results)

            if self.settings.post_to_subreddit_enabled:
                self.post_to_subreddit(title, text)

            self.message_users(title, text)

        time.sleep(600) # wait a while

    def query_keywords(self):
        multireddit_string = ','.join(subreddit.name for subreddit in self.subreddits)

        utc_time    = dt.utcnow()
        end_epoch   = int(dt.timestamp(utc_time))
        start_epoch = end_epoch - self.settings.delay

        results = {}

        # Here's where the magic happens
        for keyword in self.keywords:
            kw_results_gen = self.pushshift.search_comments(after=start_epoch,
                                                            subreddit=multireddit_string,
                                                            q=keyword.value)

            results[keyword.value] = 0
            for result in kw_results_gen:
                results[keyword.value] += result.body.count(keyword.value)

        return results

    def build_results_text(self, results):
        valid_results = []

        for keyword in results.keys():
            if results[keyword] >= self.settings.threshold:
                result_tuple = (keyword, results[keyword])
                valid_results.append(result_tuple)

        valid_results.sort(key=lambda pair: pair[1], reverse=True) # sort by the value, not the key

        date_str = dt.utcnow().strftime('%d/%m/%Y')
        text = 'Date: {}\n\n'.format(date_str)

        result_text = ['KEYWORD: {} / {}'.format(result[0], result[1]) for result in valid_results]

        text += '\n\n'.join(result_text)

        return text

    def post_to_subreddit(self, title, text):
        self.reddit.subreddit(self.settings.post_to_subreddit).submit(title=title, selftext=text)
    
    def message_users(self, subject, text):
        for redditor in self.redditors:
            self.reddit.redditor(redditor.name).message(subject=subject,
                                                        message=text)

    def load_configuration(self, path):
        with open(path) as f:
            data = json.load(f)

        self.subreddits = [Subreddit(name) for name in data['subreddits']]
        self.keywords   = [Keyword(value) for value in data['keywords']]
        self.redditors  = [Redditor(name) for name in data['redditors']]
        self.settings   = Settings(**data['settings'])

if __name__ == "__main__":
    bot = Bot()
    
    print('Reddit Keyword Reports v{} by /u/pawptart'.format(bot.VERSION))
    print('Starting!')

    while(True):
        bot.run()
