#import reloader
#reloader.enable(blacklist=['inspect','os','pickle','time','re','random','urllib','stripclub','math','udquery','sys','traceback','json'])

from inspect import getmembers, isfunction
from bs4 import BeautifulSoup
import os,pickle,time,re,random,urllib2,urllib,requests,math,udquery,sys,traceback,json
import irc.bot
import trpbot_commands
import stripclub
from irc import strings
from irc.client import ip_numstr_to_quad,ip_quad_to_numstr

HOST = 'portlane.se.quakenet.org'
PORT = 6667
NICK = 'TRPBot'
CHAN = '#trpbot'
AUTOJOIN = ['#theredpill','#redpillwomen','#purplepilldebate']
BOSS = 'tizenwork'
VERSION = '#theredpill bot v20150106.1'
AUTH = ''

class TRPBot(irc.bot.SingleServerIRCBot):
	def __init__(self,nickname=NICK,server=HOST,port=PORT,channel=CHAN):
		irc.bot.SingleServerIRCBot.__init__(self,[(server, port)],nickname,nickname)
		self.reactor.add_global_handler('all_events',self.command_caller)
		self.channel = channel
		self.build_commands()
		self.pick = pickle
		self.tyme = time
		self.version = VERSION
		self.re = re
		self.rng = random
		self.soop = BeautifulSoup
		self.url2 = urllib2
		self.boss = '%s.users.quakenet.org' % BOSS
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
		trpbot_commands.on_initialize(os.path.isfile,pickle,json,time)
		self.reactor.execute_every(1,self.process_mqueue)
		#def execute_every(self, period, function, arguments=())

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
			print('process_mqueue exception: %s' % (self.sys.exc_info(),))
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
		ch = self.channels[e.target]
		if self.boss in e.source and e.arguments[0] == '.reload':
			#reloader.reload(trpbot_commands)
			self.build_commands()
			self.add_mqueue(c,e.target,'reload complete')
		
	def on_nicknameinuse(self,c,e):
		c.nick('%s_' % (c.get_nickname(),))
		
	def on_welcome(self,c,e):
		if AUTH:
			c.send_raw(AUTH)
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
	
if __name__ == '__main__':
	bot = TRPBot()
	keeptrying = True
	while keeptrying:
		try:
			print('%s initialized. connecting...' % (VERSION,))
			bot.start()
		except UnicodeDecodeError:
			print('disconnected, UnicodeDecodeError')
			bot.disconnect(VERSION)
		except KeyboardInterrupt:
			print('disconnected, KeyboardInterrupt')
			bot.disconnect(VERSION)
			keeptrying = False

