VOCAB = {}
VOCAB_FNAME = 'trpbot.vocab'
BDATA = {
	'mods':[],
	'vhistory':[],
	'karma':{},
	'ranks':{},
	'memos':{},
	'seen':{}, # BDATA['seen'][nick.lower()] = [mask,when,what,deets]
}
BDATA_FNAME = 'trpbot.bdata'
DELAY_SET = 30
DELAY_NOW = 0

BOSS_TERMS = ['trpbot','version']

def save_bdata(pickle):
	global BDATA
	with open(BDATA_FNAME,'wb') as f:
		pickle.dump(BDATA,f)

def last_seen(self,nick,mask,when,what,deets):
	global BDATA
	if 'seen' not in BDATA:
		BDATA['seen'] = {}
	BDATA['seen'][nick.lower()] = [mask,when,what,deets] # [mask,when,what,deets]
	save_bdata(self.pick)

def on_initialize(isfile,pick,tyme):
	global DELAY_NOW
	global VOCAB
	global BDATA
	DELAY_NOW = tyme.time()
	if isfile(VOCAB_FNAME):
		with open(VOCAB_FNAME) as f:
			VOCAB = pick.load(f)
	if isfile(BDATA_FNAME):
		with open(BDATA_FNAME) as f:
			BDATA = pick.load(f)

def __reload__(state):
	global VOCAB
	global BDATA
	global DELAY_NOW
	VOCAB = state['VOCAB']
	BDATA = state['BDATA']
	DELAY_NOW = state['DELAY_NOW']
	if 'ranks' not in BDATA:
		BDATA['ranks'] = {}
		print('BDATA upgraded.')
	if 'memos' not in BDATA:
		BDATA['memos'] = {}
		print('BDATA[memos] upgraded.')

def is_int(n):
    try:
        int(n)
        return True
    except ValueError:
        return False
		
def time_ago(s):
	s = int(s)
	m,s = divmod(s,60) if s >= 60 else (0,s)
	h,m = divmod(m,60) if m >= 60 else (0,m)
	d,h = divmod(h,24) if h >= 24 else (0,h)
	y,d = divmod(d,365) if d >= 365 else (0,d)
	t = []
	for unit,abb in ((y,'y'),(d,'d'),(h,'h'),(m,'m')):
		if unit > 0: t.append('%s%s' % (unit,abb))
	t.append('%ss' % (s,))
	ago = ' '.join(t)
	return ago

def cmd_b_die(self,c,e):
	raise KeyboardInterrupt('Die Command Received.')
	
def cmd_r_seen(self,c,e):
	msg = e.arguments[0]
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) != 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <nick>' % (cmd,))
		return
	nick = parms[1].strip()
	# BDATA['seen'][nick.lower()] = [mask,when,what,deets] # [mask,when,what,deets]
	if 'seen' in BDATA and nick.lower() in BDATA['seen']:
		mask,when,what,deets = BDATA['seen'][nick.lower()]
		ago = self.tyme.time() - when
		# (pmsg,msg,join,part,quit,idle)
		about = ''
		if what == 'pmsg':
			about = '[speaking privately to bot]'
		elif what == 'msg':
			about = '[chatting in %s]' % (deets,)
		elif what == 'join':
			about = '[joining %s]' % (deets,)
		elif what == 'part':
			about = '[leaving %s]' % (deets,)
		elif what == 'quit':
			about = '[disconnected: %s]' % (deets,)
		elif what == 'idle':
			about = '[idling in %s]' % (deets,)
		self.add_mqueue(c,e.target,'%s (%s) last seen %s ago %s' % (nick,mask,time_ago(ago),about))
	else:
		self.add_mqueue(c,e.target,'%s has not been seen.' % (nick,))
		
def memo_send(self,c,e):
	global BDATA
	nick = e.source.nick
	msg = e.arguments[0]
	parms = msg.split(' ')
	if len(parms) < 4:
		self.add_mqueue(c,nick,'Syntax: .memo send <nick> <message>' % (cmd,))
		return
	dest = parms[2].lower()
	if dest not in BDATA['seen']:
		self.add_mqueue(c,nick,'Cannot send memo to "%s". (TRPBot has not seen that person before)' % (parms[2],))
		return
	msg = [nick,self.tyme.time(),False,' '.join(parms[3:])] # from, time, read_flag, message
	if 'memos' not in BDATA:
		BDATA['memos'] = {}
	if dest not in BDATA['memos']:
		BDATA['memos'][dest] = []
	BDATA['memos'][dest].append(msg)
	self.add_mqueue(c,nick,'Memo sent to "%s".' % (parms[2],))
	is_online = False
	for chan in self.channels:
		for usr in self.channels[chan].users():
			if usr.lower() == dest:
				is_online = True
				break
		if is_online:
			break
	if is_online:
		self.add_mqueue(c,dest,'You have received a new memo from %s. Tell me ".memo read %s" to read this memo.' % (nick,len(BDATA['memos'][dest]),))
	save_bdata(self.pick)
	
def memo_read(self,c,e):
	global BDATA
	nick = e.source.nick
	msg = e.arguments[0]
	parms = msg.split(' ')
	if len(parms) != 3 or not is_int(parms[2]):
		self.add_mqueue(c,nick,'Syntax: .memo read <#>' % (cmd,))
		return
	n = int(parms[2])
	msgs = [] if 'memos' not in BDATA or nick.lower() not in BDATA['memos'] else BDATA['memos'][nick.lower()]
	if n > len(msgs):
		self.add_mqueue(c,nick,'That memo # does not exist.')
		return
	sender,tyme,readflag,msg = msgs[n-1]
	self.add_mqueue(c,nick,'(%s ago) <%s> %s' % (time_ago(self.tyme.time()-tyme),sender,msg))
	msgs[n-1] = (sender,tyme,True,msg)
	save_bdata(self.pick)

def memo_delete(self,c,e):
	global BDATA
	nick = e.source.nick
	msg = e.arguments[0]
	parms = msg.split(' ')

def on_privmsg(self,c,e):
	nick = e.source.nick
	msg = e.arguments[0]
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	last_seen(self,nick,e.source,self.tyme.time(),'pmsg','') 
	print('<%s> %s' % (nick,msg,))
	if cmd in ('memo','memos'):
		if len(parms) == 1:
			if 'memos' not in BDATA or nick.lower() not in BDATA['memos'] or len(BDATA['memos'][nick.lower()]) < 1:
				self.add_mqueue(c,nick,'You have no memos.')
				return
			msgs = BDATA['memos'][nick.lower()]
			n = 1
			for sender,tyme,readflag,msg in msgs:
				preview = '#%s [%s] %s <%s>' % (n,'Read' if readflag else 'Unread',time_ago(self.tyme.time()-tyme),sender,)
				'''
				mlen = 50-len(preview)
				smsg = ''
				if mlen > 0:
					smsg = msg[:mlen] if mlen < len(msg) else msg
				self.add_mqueue(c,nick,'%s%s' % (preview,smsg))
				'''
				self.add_mqueue(c,nick,'%s (.memo read %s)' % (preview,n))
				n += 1
				
		elif parms[1].lower() not in ('send','read','del','delete',):
			self.add_mqueue(c,nick,'Syntax: .%s <send/read/delete>' % (cmd,))
		elif parms[1].lower() == 'send':
			memo_send(self,c,e)
		elif parms[1].lower() == 'read':
			memo_read(self,c,e)
		elif parms[1].lower() in ('del','delete'):
			memo_delete(self,c,e)

def on_pubmsg(self,c,e):
	global DELAY_NOW
	msg = e.arguments[0].strip()
	last_seen(self,e.source.nick,e.source,self.tyme.time(),'msg',e.target) 
	if not len(msg):
		return
	parms = msg.split(' ')
	boss = e.source.nick.lower() in self.boss
	oper = self.channels[e.target].is_oper(e.source.nick) or boss
	voiced = self.channels[e.target].is_voiced(e.source.nick) or oper or e.source.nick.lower() in BDATA['mods']
	rcmd = parms[0].lower().replace('.','cmd_r_')
	vcmd = parms[0].lower().replace('.','cmd_v_') if voiced else ''
	ocmd = parms[0].lower().replace('.','cmd_o_') if oper else ''
	bcmd = parms[0].lower().replace('.','cmd_b_') if boss else ''
	for cmd in (bcmd,ocmd,vcmd,rcmd):
		if cmd in self.chatcmds:
			self.chatcmds[cmd](self,c,e)
			break
	if parms[0] == '+1' and len(parms) == 2:
		target = parms[1].lower()
		giver = e.source.nick.lower()
		if target == giver:
			self.add_mqueue(c,e.target,'Cannot give karma to yourself.')
			return
		if not self.channels[e.target].has_user(target):
			self.add_mqueue(c,e.target,'That user is not in the channel.')
			return
		if giver not in BDATA['karma']:
			BDATA['karma'][giver] = {'count':0,'next':0,}
		if BDATA['karma'][giver]['count'] < 1 and not voiced:
			self.add_mqueue(c,e.target,'Cannot give karma until you receive it.')
			return # cannot give karma until you receive it
		if not oper and self.tyme.time() < BDATA['karma'][giver]['next']:
			self.add_mqueue(c,e.target,'Must wait longer.')
			return # must wait longer
		if voiced:
			BDATA['karma'][giver]['next'] = self.tyme.time() + self.rng.randint(60*35,60*60*3) # between 35min and 3hrs.
		elif not oper:
			BDATA['karma'][giver]['next'] = self.tyme.time() + 60*60*12 # 12 hours
		if target not in BDATA['karma']:
			BDATA['karma'][target] = {'count':0,'next':0,}
		BDATA['karma'][target]['count'] += 1
		self.add_mqueue(c,e.target,'+1 karma awarded to %s by %s.' % (target,giver))
		save_bdata(self.pick)
		return
	if parms[0] == '-1' and len(parms) == 2 and oper:
		target = parms[1].lower()
		giver = e.source.nick.lower()
		if not self.channels[e.target].has_user(target):
			self.add_mqueue(c,e.target,'That user is not in the channel.')
			return
		if giver not in BDATA['karma']:
			BDATA['karma'][giver] = {'count':0,'next':0,}
		if target not in BDATA['karma']:
			BDATA['karma'][target] = {'count':0,'next':0,}
		BDATA['karma'][target]['count'] -= 1
		self.add_mqueue(c,e.target,'-1 karma given to %s by %s.' % (target,giver))
		save_bdata(self.pick)
		return

		
	match = self.re.match("(what)?('s | is |s )?(a |an )?(?P<term>.+)\?",msg)
	term = match.groupdict(0)['term'].lower() if match else ''
	if term in VOCAB:
		if self.tyme.time() >= DELAY_NOW or oper or voiced:
			if not oper and not voiced:
				DELAY_NOW = self.tyme.time() + DELAY_SET
			oterm = VOCAB[term].replace('{version}',self.version)
			oterm = oterm.replace('{time}',self.tyme.strftime('%H:%M:%S'))
			self.add_mqueue(c,e.target,'%s, %s: %s' % (e.source.nick,term,oterm))
			return
	

	karma = 0 if e.source.nick.lower() not in BDATA['karma'] else BDATA['karma'][e.source.nick.lower()]['count']
	if oper or voiced or karma > 0:
		for parm in parms:
			if 'http://' in parm or 'https://' in parm:
				try:
					soup = self.soop(self.url2.urlopen(parm))
					if len(soup.title.string):
						self.add_mqueue(c,e.target,'(%s)' % (soup.title.string))
						return
				except:
					pass

def cmd_o_setrank(self,c,e):
	global BDATA
	msg = e.arguments[0]
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <karma> [title]' % (cmd,))
		return
	amnt = parms[1].lower()
	if not is_int(amnt):
		self.add_mqueue(c,e.target,'Invalid amount.')
		return
	amnt = int(amnt)
	if len(parms) == 2:
		if amnt in BDATA['ranks']:
			self.add_mqueue(c,'rank %d: %s' % (amnt,BDATA['ranks'][amnt],))
		else:
			self.add_mqueue(c,'rank %d does not exist.' % (amnt,))
	else:
		rank = ' '.join(parms[2:])
		self.add_mqueue(c,e.target,'rank added.' if amnt not in BDATA['ranks'] else 'rank modified.')
		BDATA['ranks'][amnt] = rank
		save_bdata(self.pick)		
	
def cmd_o_delrank(self,c,e):
	msg = e.arguments[0]
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <karma>' % (cmd,))
		return
	amnt = parms[1].lower()
	if not is_int(amnt):
		self.add_mqueue(c,e.target,'Invalid amount.')
		return
	amnt = int(amnt)
	if amnt not in BDATA['ranks']:
		self.add_mqueue(c,'rank does not exist.')
	else:
		del BDATA['ranks'][amnt]
		save_bdata(self.pick)
		self.add_mqueue(c,e.target,'rank deleted.')
		
def cmd_r_ranks(self,c,e):
	if 'ranks' not in BDATA or len(BDATA['ranks']) < 1:
		self.add_mqueue(c,e.source.nick,'There are no ranks.')
		return
	ranks = BDATA['ranks'].keys()
	ranks.sort()
	for rank in ranks:
		self.add_mqueue(c,e.source.nick,'Rank %d: %s' % (rank,BDATA['ranks'][rank],))


def cmd_b_save(self,c,e):
	save_bdata(self.pick)
	self.add_mqueue(c,e.target,'data saved.')
	
def cmd_b_nick(self,c,e):
	msg = e.arguments[0]
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) != 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <nick>' % (cmd,))
		return
	c.nick(parms[1])	
	
def cmd_o_setkarma(self,c,e):
	msg = e.arguments[0]
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) != 3:
		self.add_mqueue(c,e.target,'Syntax: .%s <nick> <value>' % (cmd,))
		return
	target = parms[1].lower()
	amnt = parms[2]
	if not is_int(amnt):
		self.add_mqueue(c,e.target,'Invalid amount.')
		return
	amnt = int(amnt)
	if not self.channels[e.target].has_user(target):
		self.add_mqueue(c,e.target,'That user is not in the channel.')
		return
	if target not in BDATA['karma']:
		BDATA['karma'][target] = {'count':0,'next':0,}
	BDATA['karma'][target]['count'] = amnt
	self.add_mqueue(c,e.target,'karma set.')
	save_bdata(self.pick)
	return
			
def cmd_r_karma(self,c,e):
	msg = e.arguments[0]
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	me = e.source.nick.lower()
	target = me if len(parms) == 1 else parms[1].lower()
	amnt = 0 if target not in BDATA['karma'] else BDATA['karma'][target]['count']
	frank = ''
	if 'ranks' in BDATA and len(BDATA['ranks']):
		ranks = BDATA['ranks'].keys()
		ranks.sort()
		for rank in ranks:
			if amnt >= rank:
				frank = ' (Rank: %s)' % (BDATA['ranks'][rank],)
	if len(parms) == 1 or target == me:
		self.add_mqueue(c,e.target,'You have %s karma.%s' % ('no' if amnt == 0 else amnt,frank))
	else:
		self.add_mqueue(c,e.target,'%s has %s karma.%s' % (target,'no' if amnt == 0 else amnt,frank))

def cmd_v_mods(self,c,e):
	self.add_mqueue(c,e.target,'%s mods: %s' % (len(BDATA['mods']),', '.join(BDATA['mods'])))
			
def cmd_o_addmod(self,c,e):
	#BDATA['mods'] = []
	msg = e.arguments[0]
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) != 2:
		self.add_mqueue(c,e.target,'Syntax %s <nick>' % (cmd,))
	else:
		target = msg.split(' ')[1]
		if not self.channels[e.target].has_user(target):
			self.add_mqueue(c,e.target,'That user is not in the channel.')
		elif target.lower() in BDATA['mods']:
			self.add_mqueue(c,e.target,'%s is already a mod.' % (target,))
		else:
			BDATA['mods'].append(target.lower())
			save_bdata(self.pick)
			self.add_mqueue(c,e.target,'%s added to mod list.' % (target,))

def cmd_o_delmod(self,c,e):
	msg = e.arguments[0]
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) != 2:
		self.add_mqueue(c,e.target,'Syntax %s <nick>' % (cmd,))
	else:
		target = msg.split(' ')[1]
		if target.lower() not in BDATA['mods']:
			self.add_mqueue(c,e.target,'%s is not a mod.' % (target,))
		else:
			BDATA['mods'].remove(target.lower())
			save_bdata(self.pick)
			self.add_mqueue(c,e.target,'%s deleted from mod list.' % (target,))
		
def cmd_v_tell(self,c,e):
	msg = e.arguments[0]
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) < 3:
		self.add_mqueue(c,e.target,'Syntax: %s <target> <term>' % (cmd,))
	else:
		target = msg.split(' ')[1]
		if not self.channels[e.target].has_user(target):
			self.add_mqueue(c,e.target,'That user is not in the channel.')
		else:
			term = msg.split(' ')[2].lower()		
			if term not in VOCAB:
				self.add_mqueue(c,e.target,'Term does not exist. Use .addterm to add new terms.')
			else:			
				self.add_mqueue(c,e.target,'%s, %s: %s' % (target,term,VOCAB[term].replace('{version}',self.version)))
		
def on_join(self,c,e):
	nick = e.source.nick
	if nick != c.get_nickname():
		last_seen(self,nick,e.source,self.tyme.time(),'join',e.target)
		if 'memos' in BDATA and nick.lower() in BDATA['memos']:
			msgs = BDATA['memos'][nick.lower()]
			unread = 0
			for sender,tyme,readflag,msg in msgs:
				if not readflag:
					unread += 1
			if unread > 0:
				self.add_mqueue(c,nick,'You have %d unread memo%s. Send me the private command .memos to see your memos.' % (unread,'' if unread == 1 else 's'))
		#self.add_mqueue(c,e.target,'Welcome to %s, %s.' % (e.target,e.source.nick))

def on_part(self,c,e):
	nick = e.source.nick
	if nick != c.get_nickname():
		last_seen(self,nick,e.source,self.tyme.time(),'part',e.target)
		
def on_quit(self,c,e):
	nick = e.source.nick
	if nick != c.get_nickname():
		last_seen(self,nick,e.source,self.tyme.time(),'quit',e.target)

def on_endofnames(self,c,e):
	chan = e.arguments[0]
	for each_nick in self.channels[chan].users():
		nick_mask = each_nick if 'seen' not in BDATA or each_nick.lower() not in BDATA['seen'] else BDATA['seen'][each_nick.lower()][0]
		last_seen(self,each_nick,nick_mask,self.tyme.time(),'idle',chan)
	
def cmd_o_lurkin(self,c,e):
	msg = e.arguments[0]
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) != 2:
		self.add_mqueue(c,e.target,'Syntax: %s <channel>' % (cmd,))
	else:
		c.join(msg.split(' ')[1])
		
def cmd_o_gtfo(self,c,e):
	if (e.target != self.channel):
		c.part(e.target)

def cmd_v_addterm(self,c,e):
	global VOCAB
	msg = e.arguments[0]
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) < 3:
		self.add_mqueue(c,e.target,'Syntax: %s <term> <definition>' % (cmd,))
	else:
		term = msg.split(' ')[1].lower()		
		if term in VOCAB:
			self.add_mqueue(c,e.target,'Term already exists. Use .modterm to modify existing terms.')
		else:			
			VOCAB[term] = ' '.join(msg.split(' ')[2:])
			with open(VOCAB_FNAME,'wb') as f:
				self.pick.dump(VOCAB,f)
			self.add_mqueue(c,e.target,'Term added.')
			
def cmd_v_modterm(self,c,e):
	global VOCAB
	msg = e.arguments[0]
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) < 3:
		self.add_mqueue(c,e.target,'Syntax: %s <term> <definition>' % (cmd,))
	else:
		term = msg.split(' ')[1].lower()		
		if term not in VOCAB:
			self.add_mqueue(c,e.target,'Term does not exist. Use .addterm to add new terms.')
		elif term in BOSS_TERMS and e.source.nick.lower() not in self.boss:
			self.add_mqueue(c,e.target,'Term modification not allowed.')
		else:			
			VOCAB[term] = ' '.join(msg.split(' ')[2:])
			with open(VOCAB_FNAME,'wb') as f:
				self.pick.dump(VOCAB,f)
			self.add_mqueue(c,e.target,'Term modified.')
			
def cmd_v_delterm(self,c,e):
	global VOCAB
	msg = e.arguments[0]
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) != 2:
		self.add_mqueue(c,e.target,'Syntax: %s <term>' % (cmd,))
	else:
		term = msg.split(' ')[1].lower()		
		if term not in VOCAB:
			self.add_mqueue(c,e.target,'Term does not exist.')
		elif term in BOSS_TERMS and e.source.nick.lower() not in self.boss:
			self.add_mqueue(c,e.target,'Term deletion not allowed.')
		else:			
			del VOCAB[term]
			with open(VOCAB_FNAME,'wb') as f:
				self.pick.dump(VOCAB,f)
			self.add_mqueue(c,e.target,'Term deleted.')
			
def cmd_v_terms(self,c,e):
	if not len(VOCAB):
		self.add_mqueue(c,e.target,'There are no existing terms. Use .addterm to add new terms.')
		return
	terms = []
	for term in VOCAB.keys():
		terms.append(term)
	terms.sort()
	self.add_mqueue(c,e.target,'%s terms.' % (len(terms),))
	
def cmd_r_help(self,c,e):
	boss = e.source.nick.lower() in self.boss
	oper = self.channels[e.target].is_oper(e.source.nick) or boss
	voiced = self.channels[e.target].is_voiced(e.source.nick) or oper or e.source.nick.lower() in BDATA['mods']
	cmds = []
	for cmd in self.chatcmds.keys():
		if 'cmd_b_' in cmd and boss:
			cmds.append(cmd.replace('cmd_b_','$'))
		if 'cmd_o_' in cmd and oper:
			cmds.append(cmd.replace('cmd_o_','@'))
		if 'cmd_v_' in cmd and voiced:
			cmds.append(cmd.replace('cmd_v_','+'))
		if 'cmd_r_' in cmd:
			cmds.append(cmd.replace('cmd_r_',''))
	cmds.sort()	
	self.add_mqueue(c,e.target,'Commands: %s' % (', '.join(cmds),))
	