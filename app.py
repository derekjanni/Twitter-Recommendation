# spyre
from spyre import server
# mongo db stuff
from pymongo import MongoClient
from bson.son import SON
from bson.code import Code
# nlp libs
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk.corpus import words
# sklearn
from sklearn.metrics import pairwise_distances_argmin_min
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans, MeanShift
# tweepy
import tweepy
import cnfg
import requests
from requests_oauthlib import OAuth1
# standard
import numpy as np
import pandas as pd
from scipy.stats.mstats import mode
from datetime import datetime

'''
<------------------------------------------------------------------->
MONGODB & TWEEPY CREDENTIALS
<------------------------------------------------------------------->
'''

# mongo setup
client = MongoClient('mongodb://52.10.8.92:27017/')
users = client.twitter_data.users2

# tweepy setup
config = cnfg.load(".twitter_config")
auth = tweepy.OAuthHandler(config["consumer_key"],
                           config["consumer_secret"])
auth.set_access_token(config["access_token"],
                      config["access_token_secret"])
api = tweepy.API(auth)

'''
<------------------------------------------------------------------->
SPYRE
<------------------------------------------------------------------->
'''

class SpyreApp(server.App):
    title = "Twitter Recommendation Engine"

    inputs = [{ "type":"text",
                "key":"user_name",
                "label":"Enter Twitter User",
                "value":"hello world", 
                "action_id":"simple_html_output"}]

    outputs = [{"type":"html",
                "id":"simple_html_output"}]

    def getHTML(self, params):
        user_name = params["user_name"]
        recs = main(user_name)
        html = '''
        <style>
            body {
                background-image: url("http://api.ning.com/files/Ap9VLg0NDkuA6RlYOoMYp2W*Wqn4eTIRdaEeVw5Zj7g1YiTeT9dwle6m1Cr1RarKMijV0duWmJDFAZDE*6pZ*X2rQhOfTmWu/1.jpg");
            }
        </style>
                <a class="twitter-timeline"
                  data-widget-id="634768088001576960"
                  data-screen-name="'''+ str(recs[0][1]).strip(' ') +'''"
                  href="https://twitter.com/''' + str(recs[0][1]).strip(' ') + '''""
                  width="300"
                  height="300">
                Tweets by @'''+ str(recs[0][1]).strip(' ') + '''
                </a>

                <a class="twitter-timeline"
                  data-widget-id="634768088001576960"
                  data-screen-name="'''+ str(recs[1][1]).strip(' ') +'''"
                  href="https://twitter.com/''' + str(recs[1][1]).strip(' ') + '''""
                  width="300"
                  height="300">
                Tweets by @'''+ str(recs[1][1]).strip(' ') + '''
                </a>

                <a class="twitter-timeline"
                  data-widget-id="634768088001576960"
                  data-screen-name="'''+ str(recs[2][1]).strip(' ') +'''"
                  href="https://twitter.com/''' + str(recs[2][1]).strip(' ') + '''""
                  width="300"
                  height="300">
                Tweets by @'''+ str(recs[2][1]).strip(' ') + '''
                </a>
        <script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0],p=/^http:/.test(d.location)?'http':'https';if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src=p+"://platform.twitter.com/widgets.js";fjs.parentNode.insertBefore(js,fjs);}}(document,"script","twitter-wjs");</script>
        '''
        return html

'''
<------------------------------------------------------------------->
RECCOMENDATION ENGINE
<------------------------------------------------------------------->
'''

class RecommendationEngine(object):

    def __init__(self):
        '''Setup Reccomendation engine basic'''
        self = self

    # get text
    def get_corpus(self):
        '''Get tweets from MongoDB in a a list format'''
        print "Gathering tweets from " + str(users.count()) + " twitter users. Such data."
        raw_text = [i['tweets'] for i in users.aggregate(
                [{"$project":{"tweets":"$tweets"}},{"$unwind":"$tweets"}]) if i['tweets'] > ['']]

        text = []
        for i in raw_text:
            i  = ' '.join(filter(lambda x: bool(wordnet.synsets(x)), i.split(' ')))
            if len(i) > 5:
                text.append(i)
        self.corpus = text
        return text

    # start kmeans, get model and centroids
    def get_Kmeans(self):
        ''' Set up Kmeans algorithm with arbitrary clusters'''
        k = 100
        vect = TfidfVectorizer(ngram_range=(1,2), stop_words='english')
        X = vect.fit_transform(self.corpus)
        model = KMeans(k)
        model.fit(X)
        order_centroids = model.cluster_centers_.argsort()[:, ::-1]
        terms = vect.get_feature_names()
        self.centroids = order_centroids
        self.model = model
        self.vect = vect
        return model, pairwise_distances_argmin_min(model.cluster_centers_, X, metric='cosine')

    # get reccomendations
    def get_recommendations(self, username):
        tweets = api.user_timeline(username)
        raw_text = [i.text for i in tweets]
        # clean text
        text = []
        for i in raw_text:
            i  = ' '.join(filter(lambda x: bool(wordnet.synsets(x)), i.split(' ')))
            if len(i) > 5:
                text.append(i)
        # find users like you
        user_score = int(mode([self.model.predict(self.vect.transform([i])) for i in text], axis=None)[0])
        for i in users.find():
            users.update({"_id": i["_id"]},
                 {'$set': {'cluster_score': int(mode(self.model.predict(self.vect.transform(i['tweets'])), 
                            axis=None)[0]
                            )}
                 })
        recs = [(i['user_id'], i['screen_name']) for i in users.find({'cluster_score': user_score})]
        return recs

    def update_db(self):
        for i in users.find():
            users.update({"_id": i["_id"]},
                 {'$set': {'cluster_score': int(mode(model.predict(RE.vect.transform(i['tweets'])), 
                            axis=None)[0]
                            )}
                 })

'''
<------------------------------------------------------------------->
MAIN METHOD FOR RECOMMENDATIONS
<------------------------------------------------------------------->
'''

def main(target):
    RE = RecommendationEngine()
    tweets = RE.get_corpus()
    model, centroids = RE.get_Kmeans()
    user_name = target
    recommendations = RE.get_recommendations(user_name)
    return recommendations[:5]
    '''
    #evaluation = raw_input('How did I do at suggesting followers (on a scale of 1 to 5)?')
    evaluation = 3
    feedback = client.twitter_data.user_feedback

    print "Thanks for the feedback, we'll do better next time!"
    feedback.insert({'user' : user_name,
                    'rating': evaluation,
                    'date_time': datetime.now()
                    })

    print 'Now updating scores'
    for i in users.find():
            users.update({"_id": i["_id"]},
                 {'$set': {'cluster_score': int(mode(RE.model.predict(RE.vect.transform(i['tweets'])), 
                            axis=None)[0]
                            )}
                 })'''


if __name__ == "__main__":
    app = SpyreApp()
    app.launch()
    #main()