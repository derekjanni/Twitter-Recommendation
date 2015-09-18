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



# mongo setup
client = MongoClient('mongodb://52.10.8.92:27017/')
users = client.twitter_data.users

# tweepy setup
config = cnfg.load(".twitter_config")
auth = tweepy.OAuthHandler(config["consumer_key"],
                           config["consumer_secret"])
auth.set_access_token(config["access_token"],
                      config["access_token_secret"])
api = tweepy.API(auth)


class ReccomendationEngine(object):

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
		recs = [i['user'] for i in users.find({'cluster_score': user_score})]
		return recs

def main():
	print "Starting...."
	RE = ReccomendationEngine()
	tweets = RE.get_corpus()
	model, centroids = RE.get_Kmeans()
	user_name = raw_input('Please enter twitter username to provide reccomendation for:')
	recommendations = RE.get_recommendations(user_name)
	print "Follow these users?\n"
	for i in recommendations[:5]:
		print i
		print

	evaluation = raw_input('How did I do at suggesting followers (on a scale of 1 to 5)?')
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
                 })

if __name__ == "__main__":
    main()












