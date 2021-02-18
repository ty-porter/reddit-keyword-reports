class Subreddit:
    def __init__(self, name):
        self.name = name

class Keyword:
    def __init__(self, value):
        self.value = value

class Redditor:
    def __init__(self, name):
        self.name = name

class Settings:
    def __init__(self, 
                 messaging_enabled: False, 
                 post_to_subreddit_enabled: False, 
                 post_to_subreddit: None,
                 threshold: 5,
                 delay: { "hours": 24 }):
        self.messaging_enabled = messaging_enabled
        self.post_to_subreddit_enabled = post_to_subreddit_enabled
        self.post_to_subreddit = post_to_subreddit
        self.threshold = threshold
        self.build_delay_in_seconds(delay)

    def build_delay_in_seconds(self, delay):
        durations = {
            'days': 24 * 60 * 60,
            'hours': 60 * 60,
            'minutes': 60,
            'seconds': 1
        }
        
        self.delay = 0
        for duration in durations.keys():
            self.delay += delay[duration] * durations[duration]