#Searching Twitter

import json, urllib

from fb.db import db

from twisted.python import log

import fb.intent as intent
from fb.modules.base import Module, require_auth, response

class TwitterModule(Module):

	uid="twitter"
	name="Twitter"
	description="Functionality for searching Twitter"
	author="Kyle Varga (kyle.varga@bazaarvoice.com)"

	commands = {
		"twitter": {
			"keywords": "twitter",
			"function": "twitter",
			"name": "Twitter Search",
			"description": "Returns all results from Twitter Search API"
		}, 
		"twitterclear": {
			"keywords": "twitterclear",
			"function": "twitterClear",
			"name": "Twitter Clear",
			"description": "Clears recent history for all or a specific query"
		}
	}

	@require_auth('twitter', "Twitter isn't allowed here!", False)
	@response
	def twitter(self, bot, room, user, args):
		query = urllib.urlencode({'q':' '.join(args)})
		existing = db.db.twittersearch.find_one({"query": query})
		url = "http://search.twitter.com/search.json?"
		
		# Logic to determine if we have searched this query before
		# TODO: Make these expire after X hours or X days?
		if existing is None:
			print 'Never searched for this before.. searching now..'
			msg = 'First time I`ve searched for this before...\n' 
		else:
			print 'Searching now...'
			msg = 'I`ve searched for this before. Only showing recent results:\n'
			since = str(existing['max_id'])
			url = 'http://search.twitter.com/search.json?since_id=' + since + '&'
		
		url += query

		twitter_response = urllib.urlopen(url)
		twitter_results = twitter_response.read()
		results = json.loads(twitter_results)
		data = results
		since = results['max_id']

		# Remove current search history, insert latest
		db.db.twittersearch.remove({"query": query})
		db.db.twittersearch.insert({"query": query, "max_id": since});
		
		if len(data['results']):
			count = 0
			for result in data['results']:
				msg += '\t@' + result['from_user'] + ': ' + result['text'] + '\n'
				count += 1
				if count >= 5:
					break
		else:
			if existing is not None:
				msg = "Slow your roll {0}, Twitter doesn't have anything new yet.".format(user['nick'])
			else:
				msg = "Sorry, {0}, Twitter doesn't know what you are talking about.".format(user['nick'])
		return msg

	@response
	def twitterClear(self, bot, room, user, args):
		db.db.twittersearch.remove()
		return 'Removed all twitter search history'

module = TwitterModule
