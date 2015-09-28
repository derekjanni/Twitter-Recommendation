import tweepy
import cnfg
from time import sleep
from pymongo import MongoClient
import calendar
import datetime
config = cnfg.load(".twitter_config")
client = MongoClient('mongodb://52.10.8.92:27017/')
user_data = client.twitter_data.users2
auth = tweepy.OAuthHandler(config["consumer_key"], config["consumer_secret"])
auth.set_access_token(config["access_token"], config["access_token_secret"])
api = tweepy.API(auth)
count = 0
for page in tweepy.Cursor(api.followers, screen_name='twitter').pages():
    for i in page:
        count += 1
        print i.name, count
        try:
            if i.lang == u'en' and \
                [j.text for j in i.timeline()] != [] and \
                 i.timeline()[0].lang == u'en' and \
                [j.name for j in i.followers()] != []:
                user_data.insert({'user' : i.name,
                                   'screen_name': i.screen_name,
                                   'user_id': i.id,
                                   'tweets': [j.text for j in i.timeline()],
                                   'followers': [j.name for j in i.followers()],
                                   'friends': [j.name for j in i.friends()]
                })
        except:
            pass
        sleep(60)
    sleep(60)

