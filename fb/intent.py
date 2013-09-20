import re, datetime, random, sys, hashlib

from fb.audit import log
from fb.config import cfg
from fb.db import db

CAPTURE_BEGIN = ['"', "'"] #, '{', '(', '[']
CAPTURE_END = ['"', "'"] #, '}', ')', ']']

def cleanString(text):
	return re.sub("[^a-zA-Z0-9 ]", '', text.lower()).strip()

def cutString(text):
	words = text.split()
	output = []

	capturing = None
	captured = [] 

	for word in words:
		if capturing is None:
			if word[0] in CAPTURE_BEGIN:
				capturing = CAPTURE_END[CAPTURE_BEGIN.index(word[0])]

				if word[-1] == capturing:
					output.append(word[1:-1])
					capturing = None
				else:
					captured.append(word[1:])
			else:
				output.append(word)
		else:
			if word[-1] == capturing:
				captured.append(word[:-1])
				output.append(' '.join(captured))
				captured = []
				capturing = None
			else:
				captured.append(word)
	if len(captured) > 0:
		output.append(' '.join(captured))
	return output
	
class IntentService(object):

	def __init__(self):
		self._listeners = {}
		self._commands = {}
		self._bot = None

	def link(self, bot):
		self._bot = bot

	def registerCommand(self, keywords=None, function=None, module=None, name=None, description='No description provided.', core=False):
		assert keywords is not None, "Command registration called without keywords."
		assert function is not None, "Command registration called without function."
		assert module is not None, "Command registration called without module."

		uid_hash = hashlib.md5()
		
		if type(keywords) != type([]):
			keywords = [keywords]

		for word in keywords:
			uid_hash.update(word)

		uid = uid_hash.digest()

		if name is None:
			name = keywords[0]

		rexwords = []
		for word in keywords:
			rexwords.append(re.compile('^' + word + "$", re.I))

		command = {'keywords': rexwords, 'originals': keywords, 'function': function, 'name': name, 'description': description, 'module': module, 'core': core}
		self._commands[uid] = command

	def registerListener(self, patterns=None, function=None, module=None, name=None, description='No description provided.'):
		assert patterns is not None, "Listener registration called without pattern(s)"
		assert function is not None, "Listener registration called without function"
		assert module is not None, "Listener registration called without module"

		uid_hash = hashlib.md5()

		if type(patterns) != type([]):
			patterns = [patterns]

		for word in patterns:
			uid_hash.update(word)

		uid = uid_hash.digest()

		if name is None:
			name = patterns[0]

		rexwords = []
		for word in patterns:
			rexwords.append(re.compile(word, re.I))

		listener = {'patterns': rexwords, 'function': function, 'name': name, 'description': description, 'module': module}
		self._listeners[uid] = listener

	def addressedToBot(self, text, room=None):
		'''Attempts to determine if a piece of text is addressed to the bot, as in, prefixed with its nickname.'''
		#TODO: Fix this so it works with multiple-work nicknames!
		nicknames = [cleanString(cfg.bot.name)]
		nicknames.extend(cfg.bot.nicknames)
		if room is not None:
			nicknames.append(room["nick"])

		out = text.split(' ', 1)

		if cleanString(out[0]) in nicknames and len(out) > 1:
			return out[1]

	def parseMessage(self, body, room, user):
		'''Parse an incoming message.'''
		address = self.addressedToBot(body, room)

		if address is not None:
			body = address
		
		#Check to see if this is a command
		if address is not None or room is None:
			if user.banned and not user.admin:
				user.send("You've lost your bot privledges, reason: " + user["banned"])
				return True

			words = cutString(body)

			for command in self._commands.values():
				for rex in command['keywords']:
					for i in reversed(range(1, len(words) + 1)):
						match = rex.search(cleanString(' '.join(words[:i])))

						if match is not None:
							#Pull out any matched groups...
							args = []
							for k in match.groups():
								args.append(k)
							if room is not None and room.squelched and command['core'] == False:
								user.send("I'm sorry, I can't do '{0}' right now as I am shut up in {2} for the next {1}.".format(command['name'], room.squelched, room.uid))
								return True #Since we got a valid function we should say we handled it.
							else:   
								#Anything left is added to the args
								args.extend(words[i:])
								handled = command['function'](self._bot, room, user, args)
								if handled:
									return True

		if room is None or (room is not None and room.squelched == False):
			if user.banned:
				return False

			for listener in self._listeners.values():
				for rex in listener['patterns']:
					match = rex.search(cleanString(body))

					if match is not None:
						handled = listener['function'](self._bot, room, user, match)
						if handled:
							return False

		if room is None:
			user.send('Huh?')
		elif address is not None:
			room.send('Huh?')

		return False

service = IntentService()

