import fb.intent as intent
from fb.modules.base import Module, response

# requirements
import urllib, json

class WeatherModule(Module):

	uid="weather"
	name="Weather"
	description="Functions for returning weather"
	author="Kyle Varga (kyle.varga@bazaarvoice.com)"

	wundergroundapikey = '83f199a422e382c3'

	commands = {
		"weather": {
			"keywords": "weather",
			"function": "getWeather",
			"name": "Get Current Weather",
			"description": "Gets the current weather"
		}
	}
			
	@response
	def getWeather(self, bot, room, user, args):

		defaultLoc = 'TX/Austin' 
		if len(args) > 0:
			defaultLoc = urllib.quote_plus(' '.join(args))

		url = 'http://api.wunderground.com/api/' + self.wundergroundapikey + '/conditions/q/' + defaultLoc + '.json'
		f = urllib.urlopen(url)

		buff = f.read().replace('\\/', '/')
		f.close()
		result = json.loads(buff)

		try:
			current = result['current_observation']
		except KeyError:
			return 'No Weather Found for ' + defaultLoc

		return 'Current Weather in ' + current['display_location']['full'] + ': ' + current['weather'] + ', ' + current['temperature_string']

module = WeatherModule
