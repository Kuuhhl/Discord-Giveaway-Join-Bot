""" 
TODO:
- Add multithreading/async
- Add GUI
- Improve code readability and efficiency
""" 

import requests, json

limit = 100 #Number of messages to scan in the channel. MAX: 100
baseurl = ("https://discord.com/api/v6")

def server(x, servers, token):
		serverid = servers[x]['id']
		servername = servers[x]['name']
		channels = json.loads(requests.get(baseurl + '/guilds/' + serverid + '/channels', headers={"Authorization":token}).text) #Getting list of channels in server
		print('Starting with: ' + servername)
		for y in range(len(channels)):
				type = channels[y]['type']
				channelid = channels[y]['id']
				response = requests.get(baseurl + '/channels/' + channelid + '/messages?limit=' + str(limit), headers={"Authorization":token}) #Getting messages in channel
				if response.status_code == 200 and type == 0: #Checking if we have access to channel and if it is a text-channel 
						channel(y, type, channelid, response, token)
		return ('(' + str(x+1) + '/' + str(len(servers)) + ') ' + servername + ' complete.')

def channel(y, type, channelid, response, token):
	messages = json.loads(response.text)
	for i in range(len(messages)):
		msg = messages[i]
		try: #Try-Catch to check if the message was sent by a bot
			bot = msg['author']['bot']
		except KeyError:
			continue
		message(msg, token, channelid)

def message(msg, token, channelid):
	content = msg['content']
	msgid = msg['id']
	try:
		msg['reactions']
	except KeyError:
		return 'No reactions found.'
	for f in range(len(msg['reactions'])): # Iterate over reactions
		reactions = msg['reactions'][f]['emoji']['name']
		participated = msg['reactions'][f]['me']
		reaction(channelid, msgid, reactions, participated, token)
		return 'Reaction found.'

def reaction(channelid, msgid, reactions, participated, token):
		if participated == False and reactions == '🎉' or reactions == '🎁':
			requests.put(baseurl + "/channels/" + str(channelid) + "/messages/" + str(msgid) + "/reactions/" + str(reactions) + "/@me", headers={"Authorization":token})
			return 'Reacted to giveaway!'
		return 'Not reacted.'
def init():
	token = input("Input authentification token here: ")
	user = requests.get(baseurl + '/users/@me', headers={"Authorization":token})
	if user.status_code == 200:
		user = json.loads(user.text)['username']
		servers = json.loads(requests.get(baseurl + '/users/@me/guilds', headers={"Authorization":token}).text) #Getting list of joined servers
		print('----------------------')
		print('Logged in with user ' + user)
		print('Number of servers: ' + str(len(servers)))
		print('----------------------')
		for x in range(len(servers)):
			print(server(x, servers, token))
			print()
	elif user.status_code == 401:
		print('Wrong token.')
		print()
		init()

if __name__ == '__main__':
    init()
print('All servers completed!')
