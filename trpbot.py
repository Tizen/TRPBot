import reloader
reloader.enable(blacklist=['inspect','os','pickle','time','re','random','urllib','stripclub','math','udquery','sys','traceback','json','hashlib','irc','irc.bot','irc.client','ircbot','bot','chatterbotapi','socket'])

from irc import strings
from inspect import getmembers, isfunction
from bs4 import BeautifulSoup
import os,pickle,time,re,random,urllib2,urllib,requests,math,udquery,sys,traceback,json,hashlib,socket,datetime
import trpbot_commands
import stripclub
import redis
from irc.client import ip_numstr_to_quad,ip_quad_to_numstr
from Pastebin import PastebinAPI
from irc import bot as ircbot
from fnmatch import fnmatch
from chatterbotapi import ChatterBotFactory, ChatterBotType
cbfactory = ChatterBotFactory()
cbot = cbfactory.create(ChatterBotType.CLEVERBOT)

HOST = 'blacklotus.ca.us.quakenet.org' #'servercentral.il.us.quakenet.org'
PORT = 6667
NICK = 'TRPBot'
CHAN = '#trpbot'
AUTOJOIN = ['#theredpill',]
BOSS = 'tizenwork'
VERSION = '#theredpill bot v1.12'
AUTH = ''
CONFIG = 'config.json'

class TRPBot(ircbot.SingleServerIRCBot):
	def __init__(self,nickname=NICK,server=HOST,port=PORT,channel=CHAN):
		ircbot.SingleServerIRCBot.__init__(self,[(server, port)],nickname,nickname)
		self.reactor.add_global_handler('all_events',self.command_caller)
		self.cbot = cbot
		self.cbots = {}
		self.channel = channel
		self.build_commands()
		self.pick = pickle
		self.datetime = datetime
		self.tyme = time
		self.fnmatch = fnmatch
		self.version = VERSION
		self.re = re
		self.rng = random
		self.soop = BeautifulSoup
		self.url2 = urllib2
		self.boss = '%s.users.quakenet.org' % BOSS
		self.hashlib = hashlib
		self.mqueue = []
		self.urllib = urllib
		self.requests = requests
		self.stripclub = stripclub
		self.udquery = udquery
		self.math = math
		self.os = os
		self.sys = sys
		self.json = json
		self.traceback = traceback
		self.botconfig = {}
		trpbot_commands.on_initialize(os.path.isfile,pickle,json,time)
		self.reactor.execute_every(1.5,self.process_mqueue)
		self.load_config()
		self.pb = PastebinAPI()
		self.pbkey = None
		self.AUTOJOIN = AUTOJOIN
		self.socket = socket
		if 'pb_devkey' in self.botconfig and 'pb_username' in self.botconfig and 'pb_password' in self.botconfig and self.botconfig['pb_devkey'] and self.botconfig['pb_username'] and self.botconfig['pb_password']:
			self.pbkey = self.pb.generate_user_key(self.botconfig['pb_devkey'],self.botconfig['pb_username'],self.botconfig['pb_password'])
		#def execute_every(self, period, function, arguments=())
		
	def load_config(self):
		if os.path.isfile(CONFIG):
			with open(CONFIG) as f:
				self.botconfig = json.load(f)
		else:
			self.botconfig = {
				'pb_devkey':'',
				'pb_username':'',
				'pb_password':'',
				'irc_auth':'',
			}
			self.save_config()
		
	def save_config(self):
		with open(CONFIG,'wb') as f:
			self.json.dump(self.botconfig,f,sort_keys=True,indent=4)

	def process_mqueue(self):
		if not len(self.mqueue):
			return
		c,target,msg = self.mqueue.pop(0)
		try:
			msg = ''.join(msg.splitlines())
			msg1 = msg[:386]
			msg2 = msg[386:]
			c.privmsg(target,msg1)
			if len(msg2):
				self.mqueue.append((c,target,msg2))
		except:
			#print('process_mqueue exception: %s' % (self.sys.exc_info(),))
			traceback.print_exc(file=sys.stdout)
			
	def add_mqueue(self,c,target,msg):
		self.mqueue.append((c,target,msg))
		
	def build_commands(self):
		self.commands = {}
		self.chatcmds = {}
		found = getmembers(trpbot_commands,isfunction)		
		for fname,f in found:
			if len(fname) > 3 and fname[0:3] == 'on_':
				self.commands[fname] = f
			elif len(fname) > 4 and fname[0:4] == 'cmd_':
				self.chatcmds[fname] = f

	def command_caller(self,c,e):
		event_name = 'on_%s' % (e.type,)
		if event_name in self.commands:
			self.commands[event_name](self,c,e)
		#print('%s: %s' % (e.type,e.arguments[0] if len(e.arguments) else ''))
			
	def on_pubmsg(self,c,e):
		if e.target in self.channels:
			ch = self.channels[e.target]
			if self.boss in e.source and e.arguments[0] == '.reload':
				reloader.reload(trpbot_commands)
				self.build_commands()
				self.add_mqueue(c,e.target,'reload complete')
		
	def on_nicknameinuse(self,c,e):
		c.nick('%s_' % (c.get_nickname(),))
		
	def on_welcome(self,c,e):
		if AUTH or ('irc_auth' in self.botconfig and self.botconfig['irc_auth']):
			c.send_raw(AUTH if AUTH else self.botconfig['irc_auth'])
			c.mode(c.get_nickname(),'+x')
		c.join(self.channel)
		for each_chan in AUTOJOIN:
			c.join(each_chan)
		
	def on_ctcp(self,c,e):
		nick = e.source.nick
		if e.arguments[0] == 'VERSION':
			c.ctcp_reply(nick,'VERSION %s' % (VERSION,))
		elif e.arguments[0] == 'PING':
			if len(e.arguments) > 1:
				c.ctcp_reply(nick,'PING %s' % (e.arguments[1],))
		elif e.arguments[0] == 'DCC' and e.arguments[1].split(' ',1)[0] == 'CHAT':
			self.on_dccchat(c,e)

	def on_dccchat(self,c,e):
		pass

def uprint(text):
	print(text.encode('UTF-8'))

if __name__ == '__main__':
	bot = TRPBot()
	keeptrying = True
	while keeptrying:
		try:
			uprint('%s initialized. connecting...' % (VERSION,))
			bot.start()
		except UnicodeDecodeError:
			traceback.print_exc(file=sys.stdout)
		except KeyboardInterrupt:
			uprint('disconnected, KeyboardInterrupt')
			bot.disconnect(VERSION)
			keeptrying = False
