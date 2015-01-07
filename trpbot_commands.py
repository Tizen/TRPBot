VOCAB = {}
VOCAB_FNAME = 'trpbot.vocab'
BDATA = {
	'mods':[],
	'vhistory':{},
	'karma':{},
	'ranks':{},
	'memos':{},
	'seen':{}, # BDATA['seen'][nick.lower()] = [mask,when,what,deets]
	'activity':{},
	'votekick':{},
}

BDATA_FNAME = 'data/bdata.json'
DELAY_SET = 30
DELAY_NOW = 0
USER_AGENT = {'User-agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'}

BOSS_TERMS = ['trpbot','version']

def is_mod(self,c,e):
	nick = e.source.nick.lower()
	mask = e.source
	boss = self.boss in e.source
	oper = self.channels[e.target].is_oper(e.source.nick) or boss
	mod = True if oper else False
	if 'mods' in BDATA and e.target in BDATA['mods']:
		for m in BDATA['mods'][e.target]:
			if '%s.users.quakenet.org' % m in mask.lower():
				mod = True
				break
	return (boss,oper,mod)
	
def is_tmod(self,c,e,nick,chan=None): # return (tboss,toper,tmod,tmaskp,tmask)
	chan = chan if chan else e.target
	target = nick.lower()
	tmaskp = BDATA['seen'][target][0] if 'seen' in BDATA and target in BDATA['seen'] else target
	tmask = tmaskp if len(tmaskp.split('@')) < 2 else tmaskp.split('@')[1]
	tboss = self.boss in tmask
	toper = self.channels[chan].is_oper(target) or tboss
	tmod = True if toper else False
	if 'mods' in BDATA and chan in BDATA['mods']:
		for m in BDATA['mods'][chan]:
			if '%s.users.quakenet.org' % m in tmask.lower():
				tmod = True
				break
	return (tboss,toper,tmod,tmaskp,tmask)

def save_bdata(self):
	global BDATA
	with open(BDATA_FNAME,'wb') as f:
		self.json.dump(BDATA,f,sort_keys=True,indent=4)

def last_seen(self,c,e,nick,mask,when,what,deets):
	global BDATA
	if 'seen' not in BDATA:
		BDATA['seen'] = {}
	if 'mods' not in BDATA:
		BDATA['mods'] = {}
	if e.target not in BDATA['mods'] and type(BDATA['mods']) is dict:
		BDATA['mods'][e.target] = []
	BDATA['seen'][nick.lower()] = [mask,when,what,deets] # [mask,when,what,deets]
	if 'votebans' in BDATA:
		delbans = []
		delbanned = False
		for voteban in BDATA['votebans']:
			if voteban[1] <= self.tyme.time():
				c.mode(e.target,'-b %s' % (voteban[0],))
				delbans.append(voteban)
		for delban in delbans:
			delbanned = True
			BDATA['votebans'].remove(delban)
	save_bdata(self)
	
def voc_add(self,nick,term,modified=False,deleted=False):
	global BDATA
	term = term.lower()
	if 'vhistory' not in BDATA:
		BDATA['vhistory'] = {}
	if term not in BDATA['vhistory']:
		BDATA['vhistory'][term] = [nick,self.tyme.time(),0,nick,self.tyme.time(),0,nick,0] # add_nick, add_time, req_count, mod_nick, mod_time, mod_count, del_nick, del_time
	else:
		add_nick,add_time,req_count,mod_nick,mod_time,mod_count,del_nick,del_time = BDATA['vhistory'][term]
		if modified:			
			BDATA['vhistory'][term] = [add_nick,add_time,req_count,nick,self.tyme.time(),mod_count+1,del_nick,del_time]
		elif deleted:
			BDATA['vhistory'][term] = [add_nick,add_time,req_count,mod_nick,mod_time,mod_count,nick,self.tyme.time()]
		else:
			BDATA['vhistory'][term] = [add_nick,add_time,req_count+1,mod_nick,mod_time,mod_count,del_nick,del_time]
	save_bdata(self)
	
def term_macro(self,term,target):
	reterms = self.re.findall("{term:(.+?)}",VOCAB[term])
	retval = VOCAB[term]
	for reterm in reterms:
		if reterm.lower() not in VOCAB:
			continue
		retval = retval.replace('{term:%s}' % (reterm,),VOCAB[reterm.lower()])
	retval = retval.replace('{version}',self.version)
	retval = retval.replace('{stripclub}',self.stripclub.stripclub())
	retval = retval.replace('{time}',self.tyme.strftime('%H:%M:%S'))
	retval = retval.replace('{you}',target)
	
	return retval

def on_initialize(isfile,pick,json,tyme):
	print('Initializing...')
	global DELAY_NOW
	global VOCAB
	global BDATA
	DELAY_NOW = tyme.time()
	if isfile(VOCAB_FNAME):
		with open(VOCAB_FNAME) as f:
			VOCAB = pick.load(f)
	if isfile(BDATA_FNAME):
		with open(BDATA_FNAME) as f:
			BDATA = json.load(f)
	if 'mods' in BDATA and type(BDATA['mods']) is list:
		modscopy = BDATA['mods'][:]
		del BDATA['mods']
		BDATA['mods'] = {'#theredpill':modscopy}
		print('mods format upgraded.')

def __reload__(state):
	global VOCAB
	global BDATA
	global DELAY_NOW
	VOCAB = state['VOCAB']
	BDATA = state['BDATA']
	DELAY_NOW = state['DELAY_NOW']

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
	ago = ' '.join(t[0:2])
	return ago
	
def cmd_r_permissions(self,c,e):
	boss,oper,mod = is_mod(self,c,e)
	perms = []
	if boss: perms.append('boss')
	if oper: perms.append('oper')
	if mod: perms.append('mod')
	perms.append('user')
	self.add_mqueue(c,e.target,'Permissions: %s' % (', '.join(perms),))

def cmd_b_die(self,c,e):
	raise KeyboardInterrupt('Die Command Received.')
	
def cmd_r_seen(self,c,e):
	msg = e.arguments[0].strip().strip()
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
			about = '[quit%s%s]' % (': ' if deets else '',deets if deets else '',)
		elif what == 'idle':
			about = '[idling in %s]' % (deets,)
		self.add_mqueue(c,e.target,'%s (%s) last seen %s ago %s' % (nick,mask,time_ago(ago),about))
	else:
		self.add_mqueue(c,e.target,'%s has not been seen.' % (nick,))
		
def memo_send(self,c,e):
	global BDATA
	nick = e.source.nick
	msg = e.arguments[0].strip().strip()	
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 4:
		self.add_mqueue(c,nick,'Syntax: .%s send <nick> <message>' % (cmd,))
		return
	dest = parms[2].lower()
	if dest not in BDATA['seen']:
		self.add_mqueue(c,nick,'Cannot send memo to "%s". (TRPBot has not seen that person before)' % (parms[2],))
		return
	elif dest == c.get_nickname().lower():
		self.add_mqueue(c,nick,'Message sent, received and read. Good job.')
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
	save_bdata(self)
	
def memo_read(self,c,e):
	global BDATA
	nick = e.source.nick
	msg = e.arguments[0].strip().strip()
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
	save_bdata(self)

def memo_delete(self,c,e):
	global BDATA
	nick = e.source.nick
	msg = e.arguments[0].strip().strip()
	parms = msg.split(' ')

def on_privmsg(self,c,e):
	nick = e.source.nick
	msg = e.arguments[0].strip().strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	last_seen(self,c,e,nick,e.source,self.tyme.time(),'pmsg','') 
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
	elif cmd == 'test':
		pass
	match = self.re.match("(what)?('s | is |s )?(a |an )?(?P<term>.+)\?",msg)
	term = match.groupdict(0)['term'].lower() if match else ''
	if term in VOCAB:
		oterm = term_macro(self,term,e.source.nick)
		voc_add(self,nick,term)
		self.add_mqueue(c,nick,'%s: %s' % (term,oterm))
		return
		
def do_lurk_kick(self,c,e,chan=None):
	global BDATA
	started_tracking = 1417731484.161
	chan = chan if chan else e.target
	nick = e.source.nick.lower()
	if 'lurk' not in BDATA:
		BDATA['lurk'] = {}
	if 'vouch' not in BDATA:
		BDATA['vouch'] = {}
	if chan not in BDATA['lurk']:
		BDATA['lurk'][chan] = {}
	if nick not in BDATA['lurk'][chan]:
		BDATA['lurk'][chan][nick] = []
	lurkdata = (self.tyme.time(),e.arguments[0].strip())
	BDATA['lurk'][chan][nick].append(lurkdata)
	if len(BDATA['lurk'][chan][nick]) > 3:
		BDATA['lurk'][chan][nick].pop(0)
	lurkdata = {'safechat':[],'safemine':[],'safetime':[],'safeimmune':[],'kick':[],'vouched':[]}
	for user in self.channels[chan].users():		
		tboss,toper,tmod,tmaskp,tmask = is_tmod(self,c,e,user,chan)
		safe = False
		if tmod:
			lurkdata['safeimmune'].append(user)
			safe = True
		elif user.lower() in BDATA['vouch']:
			lurkdata['vouched'].append(user)
			safe = True
		elif user.lower() in BDATA['lurk'][chan] and len(BDATA['lurk'][chan][user.lower()]) > 2:
			lurkdata['safechat'].append(user)
			safe = True
		elif 'seen' in BDATA and user.lower() in BDATA['seen']:
			seen_when = BDATA['seen'][user.lower()][1]
			if self.tyme.time() - seen_when < (60*60): # 1 hour
				lurkdata['safetime'].append(user)
				safe = True
		elif self.tyme.time() < started_tracking+(60*60*24): # 24 hours
			lurkdata['safemine'].append(user)
			safe = True
		if not safe:
			lurkdata['kick'].append(user)
	save_bdata(self)
	return lurkdata

'''
def cmd_b_fixlurk(self,c,e):
	global BDATA
	if 'lurk' not in BDATA:
		BDATA['lurk'] = {}
	for chan in BDATA['lurk']:
		fixcount = 0
		fixnicks = []
		for nick in BDATA['lurk'][chan]:
			if nick.lower() != nick and nick.lower() not in BDATA['lurk'][chan]:
				fixnicks.append((lurktime,nick))
		for nick in fixnicks:
			BDATA['lurk'][chan][nick.lower()] = BDATA['lurk'][chan][nick]
			fixcount += 1
		if fixcount:
			self.add_mqueue(c,e.target,'Fixed %s nick lurk entries for %s.' % (fixcount,chan))
	save_bdata(self)
	
def cmd_b_lurkinfo(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	chan = e.target if len(parms) < 2 else parms[1]
	lurkdata = do_lurk_kick(self,c,e,chan)
	if len(parms) <	3:
		self.add_mqueue(c,e.target,'%s safeimmune: %s / vouched: %s / safechat: %s / safemine: %s / safetime: %s / kick: %s' % (chan,len(lurkdata['safeimmune']),len(lurkdata['vouched']),len(lurkdata['safechat']),len(lurkdata['safemine']),len(lurkdata['safetime']),len(lurkdata['kick']),))
	elif parms[2].lower() in lurkdata:
		self.add_mqueue(c,e.target,'%s %s: %s' % (chan,parms[2].lower(),', '.join(lurkdata[parms[2].lower()]),))
	elif parms[2].lower() == 'lurk' and len(parms) == 4:
		if 'lurk' in BDATA and chan in BDATA['lurk'] and parms[3].lower() in BDATA['lurk'][chan]:
			self.add_mqueue(c,e.target,"BDATA['lurk'][%s][%s]: %s" % (chan,parms[3].lower(),BDATA['lurk'][chan][parms[3].lower()],))
		else:
			self.add_mqueue(c,e.target,'BDATA information missing.')
	else:
		self.add_mqueue(c,e.target,'Syntax: .%s [<chan> [%s]]' % (cmd,'|'.join(lurkdata.keys()),))
'''
		
def cmd_o_kicklurkers(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	lurkdata = do_lurk_kick(self,c,e,e.target)
	if len(parms) == 1:
		kicklist = ': %s - %s09.%s go%s to initiate' % (', '.join(lurkdata['kick']),chr(3),cmd,chr(3),)
		self.add_mqueue(c,e.target,'%s target%s acquired%s' % (len(lurkdata['kick']),'' if len(lurkdata['kick']) == 1 else 's',kicklist if len(lurkdata['kick']) else '.',))
	elif parms[1].lower() == 'go':
		for nick in lurkdata['kick']:
			target = nick.lower()
			tmask = BDATA['seen'][target][0] if 'seen' in BDATA and target in BDATA['seen'] else target
			tmask = tmask if len(tmask.split('!')) < 2 else '*!%s' % (tmask.split('!')[1],)
			BDATA['votebans'].append((tmask,self.tyme.time()+(60*5)))
			c.mode(e.target,'+b %s' % (tmask,))
			c.kick(e.target,nick,'Kicked for lurking. (5 minute ban)')
			save_bdata(self)


def cmd_v_vouch(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) != 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <nick>' % (cmd,))
	else:
		nick = e.source.nick.lower()
		target = parms[1].lower()
		if 'vouch' not in BDATA:
			BDATA['vouch'] = {}
		if target not in BDATA['vouch']:
			BDATA['vouch'][target] = []
		vouched = False
		for vouch,vtime in BDATA['vouch'][target]:
			if vouch == nick:
				vouched = True
				break
		if vouched:
			self.add_mqueue(c,e.target,'You have already vouched for that nick.')
		else:
			BDATA['vouch'][target].append((nick,self.tyme.time()))
			self.add_mqueue(c,e.target,'Vouch registered.')
			save_bdata(self)
		
def cmd_b_tmaskinfo(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 3:
		self.add_mqueue(c,e.target,'Syntax: .%s <chan> <nick>' % (cmd,))
	else:
		chan = parms[1]
		user = parms[2]
		tboss,toper,tmod,tmaskp,tmask = is_tmod(self,c,e,user,chan)
		self.add_mqueue(c,e.target,'%s tmod=%s premask=%s postmask=%s' % (user,tmod,tmaskp,tmask,))
	

def on_pubmsg(self,c,e):
	global BDATA
	global DELAY_NOW

		
	msg = e.arguments[0].strip()
	last_seen(self,c,e,e.source.nick,e.source,self.tyme.time(),'msg',e.target)
	do_lurk_kick(self,c,e)
	if not len(msg):
		return
	if 'activity' not in BDATA:
		BDATA['activity'] = {}
	if e.target not in BDATA['activity']:
		BDATA['activity'][e.target] = {}
	BDATA['activity'][e.target][e.source.nick.lower()] = self.tyme.time()
	parms = msg.split(' ')
	boss,oper,voiced = is_mod(self,c,e)
	rcmd = parms[0].lower().replace('.','cmd_r_')
	vcmd = parms[0].lower().replace('.','cmd_v_') if voiced else ''
	ocmd = parms[0].lower().replace('.','cmd_o_') if oper else ''
	bcmd = parms[0].lower().replace('.','cmd_b_') if boss else ''
	for cmd in (bcmd,ocmd,vcmd,rcmd):
		if cmd in self.chatcmds:
			self.chatcmds[cmd](self,c,e)
			break
	match = self.re.match("^(.*)\+\+$",parms[0])
	if (parms[0] == '+1' and len(parms) == 2) or match:
		target = parms[1].lower() if not match else match.groups()[0]
		giver = e.source.nick.lower()
		thost = 0
		nhost = 1
		if 'seen' in BDATA and target in BDATA['seen']:
			mask,when,what,deets = BDATA['seen'][target]
			thost = mask.split('!')[1]
			nhost = e.source.split('!')[1]
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
		if thost == nhost:
			self.add_mqueue(c,e.target,'Cannot give karma to yourself.')
			return
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
		save_bdata(self)
		return
	match = self.re.match("^(.*)\-\-$",parms[0])
	if oper and ((parms[0] == '-1' and len(parms) == 2) or match):
		target = parms[1].lower() if not match else match.groups()[0]
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
		save_bdata(self)
		return
		
	match = self.re.match("(what)?('s | is |s )?(a |an )?(?P<term>.+)\?",msg)
	term = match.groupdict(0)['term'].lower() if match else ''
	if term in VOCAB:
		if self.tyme.time() >= DELAY_NOW or oper or voiced:
			if not oper and not voiced:
				DELAY_NOW = self.tyme.time() + DELAY_SET
			oterm = term_macro(self,term,e.source.nick)
			voc_add(self,e.source.nick,term)
			self.add_mqueue(c,e.target,'%s, %s: %s' % (e.source.nick,term,oterm))
			return
	
	match = self.re.match("\^(?P<opener>.+)",msg)
	if match and 'openers' in BDATA and match.group(1).lower() in BDATA['openers']:
		opener = match.group(1).lower()
		open_line,open_author,open_time,open_karma,open_hits = BDATA['openers'][opener]
		if e.source.nick.lower() not in open_karma:
			open_karma.append(e.source.nick.lower())
			BDATA['openers'][opener] = open_line,open_author,open_time,open_karma,open_hits
			self.add_mqueue(c,e.target,'+1 karma awarded to opener "%s"' % (opener,))
			save_bdata(self)

	karma = 0 if e.source.nick.lower() not in BDATA['karma'] else BDATA['karma'][e.source.nick.lower()]['count']
	titlefound = False
	for parm in parms:
		if 'http://' in parm or 'https://' in parm:
			parm = 'http'+parm.split('http')[1]
			allimg = []
			imgdbg = []
			try:
				r = self.requests.get(parm,headers=USER_AGENT,verify=False)
				if 'text/html' in r.headers['content-type']:
					# not an image
					soup = self.soop(r.content)
					if oper or voiced or karma > 0:
						if soup.title and len(soup.title.string) and not titlefound:
							self.add_mqueue(c,e.target,'(%s)' % (soup.title.string.strip()))
							titlefound = True
					imgs = soup.find_all('img')
					for img in imgs:
						try:
							if 'http://' in img['src'] or 'https://' in img['src']:
								allimg.append(img['src'])
								imgdbg.append(img)
						except KeyError:
							pass
				else:
					allimg.append(parm)
				dr = './images'
				if not self.os.path.isdir(dr):
					self.os.mkdir(dr)
				for img in allimg:
					if 'http://' not in img and 'https://' not in img and '//' in img:
						img = img.replace('//','http://')
					r = self.requests.get(img,headers=USER_AGENT,verify=False)
					fn = dr+'/'+img.split('/')[-1]
					fn = '%s%s' % (fn,'.jpg' if len(fn.split('.')) == 1 else '')
					#print('downloading %s (%s)' % (img.split('/')[-1],len(r.content)))
					if not self.os.path.isfile(fn) and len(r.content) > 30000:
						with open(fn, 'wb') as f:
							f.write(r.content)
			except:
				print('http fetch exception: %s' % (self.sys.exc_info(),))
				self.traceback.print_exc(file=self.sys.stdout)
				#print('allimg=%s parm=%s' % (allimg,parm))
					
def cmd_r_openers(self,c,e):
	return
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if 'openers' in BDATA:
		self.add_mqueue(c,e.target,'%s openers in database. Top %s: %s' % (len(BDATA['openers']),))

def cmd_b_nukeopeners(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if 'openers' in BDATA and len(parms) == 2:
		delthese = []
		for opener in BDATA['openers']:
			open_line,open_author,open_time,open_karma,open_hits = BDATA['openers'][opener]
			if open_author == parms[1].lower():
				delthese.append(opener)
		for opener in delthese:
			del BDATA['openers'][opener]
		self.add_mqueue(c,e.target,'%d openers deleted.' % (len(delthese),))
		if len(delthese):
			save_bdata(self)
	else:
		self.add_mqueue(c,e.target,'Syntax: .%s <author>' % (cmd,))
		
def cmd_r_ud(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <Urban Dictionary Search Term>' % (cmd,))
	else:
		term = ' '.join(parms[1:])
		result = self.udquery.define(term)
		result = result.replace('\r',' ')
		self.add_mqueue(c,e.target,result if result else 'UrbanDictionary definition not found.')
		
def cmd_r_quote(self,c,e):
	global BDATA
	do_save = False
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	nick = e.source.nick.lower()
	boss,oper,voiced = is_mod(self,c,e)
	if 'quotes' not in BDATA:
		BDATA['quotes'] = {}
		do_save = True
	if len(parms) < 2:
		if len(BDATA['quotes']):
			opener = self.rng.choice(BDATA['quotes'].keys())
			open_line,open_author,open_time,open_karma,open_hits = BDATA['quotes'][opener]
			BDATA['quotes'][opener] = open_line,open_author,open_time,open_karma,open_hits+1
			self.add_mqueue(c,e.target,'%s: %s' % (opener,open_line,))
			do_save = True
		else:
			opener_cmd = ' Say %s09,01.%s add <quote>%s to add a new quote.' % (chr(3),cmd,chr(3),)
			self.add_mqueue(c,e.target,'No quotes have been added yet.%s' % ('' if not voiced else opener_cmd,))
	elif parms[1].lower() in BDATA['quotes']:
		opener = parms[1].lower()
		open_line,open_author,open_time,open_karma,open_hits = BDATA['quotes'][opener]
		BDATA['quotes'][opener] = open_line,open_author,open_time,open_karma,open_hits+1
		open_msg = '%s: %s' % (opener,open_line,)
		self.add_mqueue(c,e.target,open_msg)
		do_save = True
	elif parms[1].lower() == 'add':
		if len(parms) < 3:
			self.add.mqueue(c,e.target,'Syntax: .%s add <quote>' % (cmd,))
			return
		n = 1
		while 1:
			opener = '%s%d' % (nick,n)
			if opener not in BDATA['quotes']:
				break
			n += 1
		BDATA['quotes'][opener] = [' '.join(parms[2:]),e.source.nick,self.tyme.time(),[],0]
		self.add_mqueue(c,e.target,'Quote added (ID: %s)' % (opener,))
		do_save = True
	elif parms[1].lower() in ('del','delete','remove'):
		if len(parms) != 3:
			self.add_mqueue(c,e.target,'Syntax: .%s %s <quote ID>' % (cmd,parms[1].lower()))
		elif parms[2].lower() not in BDATA['quotes']:
			self.add_mqueue(c,e.target,'Quote not found.')
		else:
			opener = parms[2].lower()
			open_line,open_author,open_time,open_karma,open_hits = BDATA['quotes'][opener]
			boss,oper,voiced = is_mod(self,c,e)
			if oper or nick == open_author:
				del BDATA['quotes'][opener]
				do_save = True
				self.add_mqueue(c,e.target,'Quote %s09,01%s%s deleted.' % (chr(3),opener,chr(3),))
			else:
				self.add_mqueue(c,e.target,'Unable to delete Quote.')
	else:
		self.add_mqueue(c,e.target,'Quote %s09,01%s%s not found.' % (chr(3),parms[1].lower(),chr(3),))
	if do_save:
		save_bdata(self)
					
def cmd_r_opener(self,c,e):
	global BDATA
	do_save = False
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	nick = e.source.nick.lower()
	boss,oper,voiced = is_mod(self,c,e)
	if 'openers' not in BDATA:
		BDATA['openers'] = {}
		do_save = True
	if len(parms) < 2:
		if len(BDATA['openers']):
			opener = self.rng.choice(BDATA['openers'].keys())
			open_line,open_author,open_time,open_karma,open_hits = BDATA['openers'][opener]
			BDATA['openers'][opener] = open_line,open_author,open_time,open_karma,open_hits+1
			self.add_mqueue(c,e.target,'Random opener: "%s" %s09,01^%s%s to upvote this opener.' % (open_line,chr(3),opener,chr(3),))
			do_save = True
		else:
			opener_cmd = ' Say %s09,01.addopener <your suave-as-fuck line here>%s to add a new opener.' % (chr(3),chr(3),)
			self.add_mqueue(c,e.target,'No openers have been added yet.%s' % ('' if not voiced else opener_cmd,))
	elif parms[1].lower() in BDATA['openers']:
		opener = parms[1].lower()
		open_line,open_author,open_time,open_karma,open_hits = BDATA['openers'][opener]
		BDATA['openers'][opener] = open_line,open_author,open_time,open_karma,open_hits+1
		open_msg = '%s: %s' % (opener,open_line,)
		self.add_mqueue(c,e.target,open_msg)
		do_save = True
	else:
		self.add_mqueue(c,e.target,'Opener %s09,01%s%s not found.' % (chr(3),parms[1].lower(),chr(3),))
	if do_save:
		save_bdata(self)
		
def cmd_v_delopener(self,c,e):
	global BDATA
	do_save = False
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	nick = e.source.nick.lower()
	do_save = False
	if 'openers' not in BDATA:
		self.add_mqueue(c,e.target,'No opener found. Add an opener with %s09,01.addopener <your suave-as-fuck line here>%s.' % (chr(3),chr(3),))
		BDATA['openers'] = {}
		do_save = True
	elif len(parms) < 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <opener ID>' % (cmd,))
	elif parms[1].lower() not in BDATA['openers']:
		self.add_mqueue(c,e.target,'Opener not found.')
	else:
		opener = parms[1].lower()
		open_line,open_author,open_time,open_karma,open_hits = BDATA['openers'][opener]
		boss,oper,voiced = is_mod(self,c,e)
		if oper or nick == open_author:
			del BDATA['openers'][opener]
			do_save = True
			self.add_mqueue(c,e.target,'Opener %s09,01%s%s deleted.' % (chr(3),opener,chr(3),))
		else:
			self.add_mqueue(c,e.target,'Unable to delete opener.')
	if do_save:
		save_bdata(self)


def cmd_v_addopener(self,c,e):
	global BDATA
	do_save = False
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	nick = e.source.nick.lower()
	if 'openers' not in BDATA:
		BDATA['openers'] = {}
		do_save = True
	if len(parms) > 1:
		n = 1
		while 1:
			opener = '%s%d' % (nick,n)
			if opener not in BDATA['openers']:
				break
			n += 1
		BDATA['openers'][opener] = [' '.join(parms[1:]),e.source.nick,self.tyme.time(),[],0]
		self.add_mqueue(c,e.target,'Opener added (ID: %s). This line will be included randomly in the %s09,01.opener%s command.' % (opener,chr(3),chr(3),))
		do_save = True
	else:
		self.add_mqueue(c,e.target,'Syntax: .%s <your suave-as-fuck line here>' % (cmd,))
	if do_save:
		save_bdata(self)

'''
def cmd_v_startvote(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	nick = e.source.nick.lower()
	if 'chanvote' not in BDATA:
		BDATA['chanvote'] = {}
	if e.target not in BDATA['chanvote']:
		BDATA['chanvote'][e.target] = {
			'creator':nick,
			'title':'',
			'options':[],
			'votes':{},
		}
	chanvote = BDATA['chanvote'][e.target]
	boss,oper,voiced = is_mod(self,c,e)
	if len(parms) < 2 or len(' '.join(parms[1:]).split('~')) < 3:
		if not chanvote['title']:
			self.add_mqueue(c,e.target,'Syntax: .%s <title>~<option1>~<option2>[~<option3>...]' % (cmd,))
			return
		self.add_mqueue(c,e.target,'There is a vote currently active. "%s" by %s' % (chanvote['title'],chanvote['creator']))
		totalvotes = 0
		for option in chanvote['options']:
			totalvotes = totalvotes + len(chanvote['votes'][option])
		for n,option in enumerate(chanvote['options']):
			pcnt = int((float(len(chanvote['votes'][option])) / float(totalvotes))*100)
			self.add_mqueue(c,e.target,'%s09,01.chanvote %s%s: %s [%s votes (%s%s)]' % (chr(3),n+1,chr(3),option,len(chanvote['votes'][option]),pcnt,'%'))
		return
	vparms = ' '.join(parms[1:]).split('~')
	chanvote['title'] = vparms[0]
	self.add_mqueue(c,e.target,'Channel vote started: %s04%s%s' % (chr(3),vparms[0],chr(3)))
	chanvote['options'] = vparms[1:]
	for n,option in enumerate(chanvote['options']):
		self.add_mqueue(c,e.target,'%s09,01.chanvote %s%s: %s' % (chr(3),n+1,chr(3),option,))
		chanvote['votes'][option] = []
	self.add_mqueue(c,e.target,'(only users with karma may cast a vote)')
	save_bdata(self)
'''
def cmd_o_kb(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 3 or not is_int(parms[2]):
		self.add_mqueue(c,e.target,'Syntax: .%s <nick> <minutes> [reason]' % (cmd,))
	else:
		target = parms[1].lower()
		length = int(parms[2])
		reason = 'Banned for %s minute%s' % (length,'' if length == 1 else 's')
		if length < 1:
			reason = 'Banned FOREVER'
		if len(parms) >= 4:
			reason = '%s (%s)' % (' '.join(parms[3:]),reason)		
		tmask = BDATA['seen'][target][0] if 'seen' in BDATA and target in BDATA['seen'] else target
		tmask = tmask if len(tmask.split('!')) < 2 else '*!%s' % (tmask.split('!')[1],)
		BDATA['votebans'].append((tmask,self.tyme.time()+(length*60 if length > 0 else 60*60*24*365*1000)))
		c.mode(e.target,'+b %s' % (tmask,))	
		c.kick(e.target,target,reason)
		save_bdata(self)
		
def cmd_o_mute(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 3 or not is_int(parms[2]):
		self.add_mqueue(c,e.target,'Syntax: .%s <nick> <minutes>' % (cmd,))
	else:
		target = parms[1].lower()
		length = int(parms[2])
		reason = 'Muted for %s minute%s' % (length,'' if length == 1 else 's')
		if length < 1:
			reason = 'Muted FOREVER'	
		tmask = BDATA['seen'][target][0] if 'seen' in BDATA and target in BDATA['seen'] else target
		tmask = tmask if len(tmask.split('!')) < 2 else '*!%s' % (tmask.split('!')[1],)
		BDATA['votebans'].append((tmask,self.tyme.time()+(length*60 if length > 0 else 60*60*24*365*1000)))
		c.mode(e.target,'+b %s' % (tmask,))	
		self.add_mqueue(c,e.target,'%s: %s' % (target,reason))
		save_bdata(self)

def cmd_r_votekick(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	nick = e.source.nick.lower()
	do_save = False
	boss,oper,voiced = is_mod(self,c,e)
	k = 0 if 'karma' not in BDATA or nick not in BDATA['karma'] else BDATA['karma'][nick]['count']
	if k == 0 and not voiced:
		self.add_mqueue(c,e.target,'You need karma before you can use the %s command.' % (cmd,))
		return
	if 'votekick' not in BDATA:
		BDATA['votekick'] = {}
	if 'votebans' not in BDATA:
		BDATA['votebans'] = []
	if e.target not in BDATA['votekick']:
		BDATA['votekick'][e.target] = {
			'nick':'',
			'time':0,
			'amount':0,
			'votes':[],
		}
		do_save = True	
	if len(parms) < 2 or parms[1].lower() == BDATA['votekick'][e.target]['nick']:
		if BDATA['votekick'][e.target]['time'] < self.tyme.time() - (60*5):
			print('parms=%s' % (parms,))
			print('votekick=%s' % (BDATA['votekick'],))
			if len(parms) > 1 and parms[1].lower() == BDATA['votekick'][e.target]['nick']:
				self.add_mqueue(c,e.target,'Votekick has been cancelled due to timeout.')
				del BDATA['votekick'][e.target]
				do_save = True				
			else:
				self.add_mqueue(c,e.target,'There is no votekick currently active. To nominate someone, type .votekick <nick>')
		elif not self.channels[e.target].has_user(BDATA['votekick'][e.target]['nick']):
			self.add_mqueue(c,e.target,'Votekick has been cancelled; %s no longer present.' % (BDATA['votekick'][e.target]['nick'],))
			del BDATA['votekick'][e.target]
			do_save = True
		elif oper or BDATA['votekick'][e.target]['nick'] == nick:
			target = BDATA['votekick'][e.target]['nick']
			tmask = BDATA['seen'][target][0] if 'seen' in BDATA and target in BDATA['seen'] else target
			tmask = tmask if len(tmask.split('!')) < 2 else '*!%s' % (tmask.split('!')[1],)
			BDATA['votebans'].append((tmask,self.tyme.time()+(60*5)))
			c.mode(e.target,'+b %s' % (tmask,))
			c.kick(e.target,BDATA['votekick'][e.target]['nick'],'Vote passed. Temp ban for 5 minutes.')
			del BDATA['votekick'][e.target]
			do_save = True
		elif e.source.nick not in BDATA['votekick'][e.target]['users']:
			self.add_mqueue(c,e.target,'Invalid voter registration ID.')
		elif nick not in BDATA['votekick'][e.target]['votes']:
			do_save = True
			BDATA['votekick'][e.target]['votes'].append(nick)
			vote_cnt = len(BDATA['votekick'][e.target]['votes'])
			vote_req = BDATA['votekick'][e.target]['amount']
			if vote_cnt >= vote_req:
				target = BDATA['votekick'][e.target]['nick']
				tmask = BDATA['seen'][target][0] if 'seen' in BDATA and target in BDATA['seen'] else target
				tmask = tmask if len(tmask.split('!')) < 2 else '*!%s' % (tmask.split('!')[1],)
				BDATA['votebans'].append((tmask,self.tyme.time()+(60*5)))
				c.mode(e.target,'+b %s' % (tmask,))
				c.kick(e.target,BDATA['votekick'][e.target]['nick'],'The tribe has spoken. Temp ban for 5 minutes')
				del BDATA['votekick'][e.target]
			else:
				BDATA['votekick'][e.target]['time'] = self.tyme.time()
				self.add_mqueue(c,e.target,'Vote registered. %d more vote%s needed.' % (vote_req-vote_cnt,'' if vote_req-vote_cnt == 1 else 's',))
	elif BDATA['votekick'][e.target]['time'] >= self.tyme.time() - (60*5):
		ago = time_ago((60*5)-(self.tyme.time()-BDATA['votekick'][e.target]['time']))
		nik = BDATA['votekick'][e.target]['nick']
		self.add_mqueue(c,e.target,'The current votekick for %s has %s remaining. Please wait for the current vote to finish before starting another.' % (nik,ago,))
	else:
		target = parms[1].lower()
		tboss,toper,tmod,tmaskp,tmask = is_tmod(self,c,e,target) # return (tboss,toper,tmod,tmaskp,tmask)
		if not self.channels[e.target].has_user(target):
			self.add_mqueue(c,e.target,'That user is not in the channel.')
		elif toper and not oper:
			c.kick(e.target,e.source.nick,'Blasphemy!' if not voiced else '*sniff* why you make me do this?')
		elif toper and oper:
			self.add_mqueue(c,e.target,'%s: can\'t we all just get along?' % (e.source.nick,))
		elif oper or target == nick:
			tmask = BDATA['seen'][target][0] if 'seen' in BDATA and target in BDATA['seen'] else target
			tmask = tmask if len(tmask.split('!')) < 2 else '*!%s' % (tmask.split('!')[1],)
			BDATA['votebans'].append((tmask,self.tyme.time()+(60*5)))
			c.mode(e.target,'+b %s' % (tmask,))	
			c.kick(e.target,target,'Vote passed. Temp ban for 5 minutes.')
		elif tmod and not voiced:
			self.add_mqueue(c,e.target,'%s: No.' % (e.source.nick,))
		elif 'activity' in BDATA and e.target in BDATA['activity']:
			r = 15
			qualify = []
			for n in BDATA['activity'][e.target]:
				if BDATA['activity'][e.target][n] >= self.tyme.time() - (60*r) and self.channels[e.target].has_user(n):
					nmask = BDATA['seen'][n][0] if 'seen' in BDATA and n in BDATA['seen'] else n
					nmask = nmask if len(nmask.split('@')) < 2 else nmask.split('@')[1]
					nboss = self.boss in nmask
					noper = self.channels[e.target].is_oper(n) or nboss
				        nmod = True if noper else False
					if 'mods' in BDATA:
						for m in BDATA['mods'][e.target]:
							if '%s.users.quakenet.org' % m in nmask.lower():
								nmod = True
								break					
					k = 0 if 'karma' not in BDATA or n not in BDATA['karma'] else BDATA['karma'][n]['count']
					k = 1 if nmod else k
					if k > 0:
						qualify.append(n)
			amount = int(self.math.ceil(len(qualify) * 0.50))
			if amount >= 2:				
				BDATA['votekick'][e.target] = {
					'nick':target,
					'time':self.tyme.time(),
					'amount':amount,
					'votes':[nick,],
					'users':self.channels[e.target].users(),
				}
				needed = '%d vote%s %s needed.' % (amount-1,'' if amount-1 == 1 else 's','is' if amount-1==1 else 'are')
				self.add_mqueue(c,e.target,'A votekick has been initiated. Type %s09,01.votekick%s to cast your vote for kicking %s. %s' % (chr(3),chr(3),target,needed,))
				do_save = True
			else:
				self.add_mqueue(c,e.target,'Not enough active users to initiate a votekick.')
		else:
			self.add_mqueue(c,e.target,'I pooped my pants.')
	if do_save:
		save_bdata(self)
					
def cmd_v_mask(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) > 1:
		n = parms[1].lower()
		report = []
		report.append('n=%s' % (n,))
		report.append('seen is in BDATA' if 'seen' in BDATA else 'seen not in BDATA')
		report.append('n in BDATA[seen]' if n in BDATA['seen'] else 'n not in BDATA[seen]')
		nmask = BDATA['seen'][n][0] if 'seen' in BDATA and n in BDATA['seen'] else n
		report.append('nmask1=%s' % (nmask,))
		nmask = nmask if len(nmask.split('@')) < 2 else nmask.split('@')[1]
		report.append('nmask2=%s' % (nmask,))
		self.add_mqueue(c,e.target,'. '.join(report))

def cmd_v_activity(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()	
	if 'activity' in BDATA and e.target in BDATA['activity']:
		r = int(parms[1]) if len(parms) > 1 and is_int(parms[1]) and int(parms[1]) <= 60 else 10
		qualify = []
		for n in BDATA['activity'][e.target]:
			if BDATA['activity'][e.target][n] >= self.tyme.time() - (60*r) and self.channels[e.target].has_user(n):
				nmask = BDATA['seen'][n][0] if 'seen' in BDATA and n in BDATA['seen'] else n
				nmask = nmask if len(nmask.split('@')) < 2 else nmask.split('@')[1]
				nboss = self.boss in nmask
				noper = self.channels[e.target].is_oper(n) or nboss
				nmod = True if noper else False
				if 'mods' in BDATA:
					for m in BDATA['mods'][e.target]:
						if '%s.users.quakenet.org' % m in nmask.lower():
							nmod = True
							break
				k = 0 if 'karma' not in BDATA or n not in BDATA['karma'] else BDATA['karma'][n]['count']
				k = 1 if nmod else k
				if k > 0:
					qualify.append(n)
		self.add_mqueue(c,e.target,'%d users with karma active in %s in the last %dmin: %s' % (len(qualify),e.target,r,', '.join(qualify),))
	else:
		self.add_mqueue(c,e.target,'No activity data.')
					
def cmd_v_lmgtfy(self,c,e):
	# urllib.urlencode({'q':'something something?!'})
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 3:
		self.add_mqueue(c,e.target,'Syntax: .%s <nick> <search term>' % (cmd,))
		return
	target = parms[1].lower()
	if not self.channels[e.target].has_user(target):
		self.add_mqueue(c,e.target,'That user is not in the channel.')
		return
	result = self.requests.get('http://autoinsult.com/webinsult.php?style=3',headers=USER_AGENT,verify=False)
	content = result.content if result.status_code == 200 else None
	if content:
		soup = self.soop(content)
		insult = soup.find('div','insult').text.lower()
	else:
		insult = ''
	search = 'http://lmgtfy.com/?%s' % (self.urllib.urlencode({'q':' '.join(parms[2:])}),)
	self.add_mqueue(c,e.target,'%s: %s%s' % (parms[1],search,' - Google it next time, %s.' % (insult,) if insult else ''))
	
'''
def cmd_b_fixranks(self,c,e):
	global BDATA
	if e.target not in BDATA['ranks']:
		rankcopy = BDATA['ranks'].copy()
		del BDATA['ranks']
		BDATA['ranks'] = {e.target:rankcopy}
		save_bdata(self)
		self.add_mqueue(c,e.target,'Rank system updated.')
		
def cmd_b_moveranks(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 3:
		self.add_mqueue(c,e.target,'Syntax: .%s <source> <destination>' % (cmd,))
		return
	source = parms[1]
	destination = parms[2]
	if source not in BDATA['ranks']:
		self.add_mqueue(c,e.target,'Source channel has no ranks.')
	elif destination in BDATA['ranks']:
		self.add_mqueue(c,e.target,'Destination channel already has %s ranks.' % (len(BDATA['ranks'][destination]),))
	else:
		rankcopy = BDATA['ranks'][source].copy()
		BDATA['ranks'][destination] = rankcopy
		del BDATA['ranks'][source]
		save_bdata(self)
		self.add_mqueue(c,e.target,'%s ranks moved from %s to %s.' % (len(BDATA['ranks'][destination]),source,destination,))
'''

def cmd_o_setrank(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <karma> [title]' % (cmd,))
		return
	if e.target not in BDATA['ranks']:
		BDATA['ranks'][e.target] = {}
	amnt = parms[1].lower()
	if len(parms) == 2:
		if amnt in BDATA['ranks'][e.target]:
			self.add_mqueue(c,e.target,'rank %s: %s' % (amnt,BDATA['ranks'][e.target][amnt],))
		else:
			self.add_mqueue(c,e.target,'rank %s does not exist.' % (amnt,))
	else:
		rank = ' '.join(parms[2:])
		self.add_mqueue(c,e.target,'rank added.' if amnt not in BDATA['ranks'][e.target] else 'rank modified.')
		BDATA['ranks'][e.target][amnt] = rank
		save_bdata(self)		
	
def cmd_o_delrank(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <karma>' % (cmd,))
		return
	amnt = parms[1].lower()
	if is_int(amnt):
		amnt = int(amnt)
	if e.target not in BDATA['ranks']:
		BDATA['ranks'][e.target] = {}
	if amnt not in BDATA['ranks'][e.target]:
		self.add_mqueue(c,e.target,'rank does not exist.')
	else:
		del BDATA['ranks'][e.target][amnt]
		save_bdata(self)
		self.add_mqueue(c,e.target,'rank deleted.')
		
def cmd_r_ranks(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	chan = e.target if len(parms) != 2 else parms[1]
	if 'ranks' not in BDATA or chan not in BDATA['ranks'] or len(BDATA['ranks'][chan]) < 1:
		self.add_mqueue(c,e.source.nick,'There are no ranks.')
		return
	delranks = []
	addranks = {}
	for rank in BDATA['ranks'][chan]:
		if is_int(rank) and type(rank) is unicode:
			addranks[int(rank)] = BDATA['ranks'][chan][rank]
			delranks.append(rank)
	for rank in delranks:
		del BDATA['ranks'][chan][rank]
	for rank in addranks:
		BDATA['ranks'][chan][rank] = addranks[rank]
	ranks = BDATA['ranks'][chan].keys()
	ranks.sort()
	for rank in ranks:
		self.add_mqueue(c,e.source.nick,'Rank %s: %s' % (rank,BDATA['ranks'][chan][rank],))
		
'''
def cmd_b_rankdebug(self,c,e):
	if e.target not in BDATA['ranks']:
		BDATA['ranks'][e.target] = {}
	self.add_mqueue(c,e.source.nick,'%s' % (BDATA['ranks'][e.target].keys(),))
'''


def cmd_b_save(self,c,e):
	save_bdata(self)
	self.add_mqueue(c,e.target,'data saved.')
	
def cmd_b_nick(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) != 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <nick>' % (cmd,))
		return
	c.nick(parms[1])	
	
def cmd_o_setkarma(self,c,e):
	msg = e.arguments[0].strip()
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
	save_bdata(self)
	return
	
def cmd_r_karma(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	me = e.source.nick.lower()
	target = me if len(parms) == 1 else parms[1].lower()
	amnt = 0 if target not in BDATA['karma'] else BDATA['karma'][target]['count']
	frank = ''
	if 'ranks' in BDATA and e.target in BDATA['ranks'] and len(BDATA['ranks']):
		if target in BDATA['ranks'][e.target]:
			frank = ' (Rank: %s)' % (BDATA['ranks'][e.target][target],)
		else:
			ranks = BDATA['ranks'][e.target].keys()
			intranks = []
			for rank in ranks:
				if is_int(rank):
					intranks.append(int(rank))
			intranks.sort()
			for intrank in intranks:
				rank = str(intrank)
				if amnt >= intrank:
					frank = ' (Rank: %s)' % (BDATA['ranks'][e.target][rank],)
				else:
					break
	if len(parms) == 1 or target == me:
		self.add_mqueue(c,e.target,'%s, you have %s karma.%s' % (e.source.nick,'no' if amnt == 0 else amnt,frank))
	elif target == c.get_nickname().lower():
		self.add_mqueue(c,e.target,'I have all the karma. (Rank: Karma Chameleon)')
	else:
		self.add_mqueue(c,e.target,'%s has %s karma.%s' % (target,'no' if amnt == 0 else amnt,frank))
		
def cmd_v_mods(self,c,e):
	self.add_mqueue(c,e.target,'%s %s mods: %s' % (e.target,len(BDATA['mods'][e.target]),', '.join(BDATA['mods'][e.target])))
			
def cmd_o_addmod(self,c,e):
	#BDATA['mods'] = []
	msg = e.arguments[0].strip()
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) != 2:
		self.add_mqueue(c,e.target,'Syntax %s <nick>' % (cmd,))
	else:
		target = msg.split(' ')[1]
		if e.target not in BDATA['mods']:
			BDATA['mods'][e.target] = []
		if not self.channels[e.target].has_user(target):
			self.add_mqueue(c,e.target,'That user is not in the channel.')
		elif target.lower() in BDATA['mods'][e.target]:
			self.add_mqueue(c,e.target,'%s is already a mod.' % (target,))
		else:
			BDATA['mods'][e.target].append(target.lower())
			save_bdata(self)
			self.add_mqueue(c,e.target,'%s added to mod list.' % (target,))

def cmd_o_delmod(self,c,e):
	msg = e.arguments[0].strip()
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) != 2:
		self.add_mqueue(c,e.target,'Syntax %s <nick>' % (cmd,))
	else:
		target = msg.split(' ')[1]
		if e.target not in BDATA['mods']:
			BDATA['mods'][e.target] = []
		if target.lower() not in BDATA['mods'][e.target]:
			self.add_mqueue(c,e.target,'%s is not a mod.' % (target,))
		else:
			BDATA['mods'][e.target].remove(target.lower())
			save_bdata(self)
			self.add_mqueue(c,e.target,'%s deleted from mod list.' % (target,))
			
def cmd_b_msg(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 3:
		self.add_mqueue(c,e.target,'Syntax: %s <target> <message>' % (cmd,))
	else:
		self.add_mqueue(c,parms[1],' '.join(parms[2:]))
		
def cmd_v_tell(self,c,e):
	msg = e.arguments[0].strip()
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
				oterm = term_macro(self,term,target)
				voc_add(self,e.source.nick,term)
				self.add_mqueue(c,e.target,'%s, %s: %s' % (target,term,oterm))
		
def on_join(self,c,e):
	nick = e.source.nick
	if nick != c.get_nickname():
		last_seen(self,c,e,nick,e.source,self.tyme.time(),'join',e.target)
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
		last_seen(self,c,e,nick,e.source,self.tyme.time(),'part',e.target)
		
def on_nick(self,c,e):
	#self.channels[e.target].has_user(BDATA['votekick'][e.target]['nick']
	before,after = e.source.nick,e.target
	for cname in self.channels:
		ch = self.channels[cname]
		if 'votekick' in BDATA and cname in BDATA['votekick'] and BDATA['votekick'][cname]['nick'] == before.lower():
			BDATA['votekick'][cname]['nick'] = after.lower()
	
def on_quit(self,c,e):
	nick = e.source.nick
	if nick != c.get_nickname():
		last_seen(self,c,e,nick,e.source,self.tyme.time(),'quit',e.arguments[0])

def on_endofnames(self,c,e):
	chan = e.arguments[0]
	for each_nick in self.channels[chan].users():
		nick_mask = each_nick if 'seen' not in BDATA or each_nick.lower() not in BDATA['seen'] else BDATA['seen'][each_nick.lower()][0]
		last_seen(self,c,e,each_nick,nick_mask,self.tyme.time(),'idle',chan)
	
def cmd_o_boss(self,c,e):
	self.add_mqueue(c,e.target,'Boss: %s' % self.boss)

def cmd_o_lurkin(self,c,e):
	msg = e.arguments[0].strip()
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
	msg = e.arguments[0].strip()
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
			voc_add(self,e.source.nick,term)
			self.add_mqueue(c,e.target,'Term added.')
			
def cmd_v_modterm(self,c,e):
	global VOCAB
	msg = e.arguments[0].strip()
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) < 3:
		self.add_mqueue(c,e.target,'Syntax: %s <term> <definition>' % (cmd,))
	else:
		term = msg.split(' ')[1].lower()		
		if term not in VOCAB:
			self.add_mqueue(c,e.target,'Term does not exist. Use .addterm to add new terms.')
		elif term in BOSS_TERMS and self.boss not in e.source:
			self.add_mqueue(c,e.target,'Term modification not allowed.')
		else:			
			VOCAB[term] = ' '.join(msg.split(' ')[2:])
			with open(VOCAB_FNAME,'wb') as f:
				self.pick.dump(VOCAB,f)
			voc_add(self,e.source.nick,term,True)
			self.add_mqueue(c,e.target,'Term modified.')
			
			
def cmd_v_delterm(self,c,e):
	global VOCAB
	msg = e.arguments[0].strip()
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) != 2:
		self.add_mqueue(c,e.target,'Syntax: %s <term>' % (cmd,))
	else:
		term = msg.split(' ')[1].lower()		
		if term not in VOCAB:
			self.add_mqueue(c,e.target,'Term does not exist.')
		elif term in BOSS_TERMS and self.boss not in e.source:
			self.add_mqueue(c,e.target,'Term deletion not allowed.')
		else:			
			del VOCAB[term]
			with open(VOCAB_FNAME,'wb') as f:
				self.pick.dump(VOCAB,f)
			voc_add(self,e.source.nick,term,deleted=True)
			self.add_mqueue(c,e.target,'Term deleted.')
			
def cmd_r_termraw(self,c,e):
	msg = e.arguments[0].strip()
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) != 2:
		self.add_mqueue(c,e.target,'Syntax: %s <term>' % (cmd,))
	else:
		term = msg.split(' ')[1].lower()		
		if term not in VOCAB:
			self.add_mqueue(c,e.target,'Term does not exist.')
		else:
			self.add_mqueue(c,e.target,'%s: %s' % (term,VOCAB[term],))
			
def cmd_r_terminfo(self,c,e):
	msg = e.arguments[0].strip()
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) != 2:
		self.add_mqueue(c,e.target,'Syntax: %s <term>' % (cmd,))
		return
	term = msg.split(' ')[1].lower()		
	if term not in BDATA['vhistory']:
		self.add_mqueue(c,e.target,'Term information does not exist.')
		return
	add_nick,add_time,req_count,mod_nick,mod_time,mod_count,del_nick,del_time = BDATA['vhistory'][term]
	# time_ago(s)
	info = '"%s" queried %s times. Originally referenced by %s (%s ago).' % (term,req_count,add_nick,time_ago(self.tyme.time()-add_time),)
	if mod_count:
		info = '%s Modified %s times (last time was %s ago by %s).' % (info,mod_count,time_ago(self.tyme.time()-mod_time),mod_nick,)
	if del_time and term not in VOCAB:
		info = '%s Deleted %s ago by %s.' % (info,time_ago(self.tyme.time()-del_time),del_nick)
	self.add_mqueue(c,e.target,info)
	
			
def cmd_v_terms(self,c,e):
	if not len(VOCAB):
		self.add_mqueue(c,e.target,'There are no existing terms. Use .addterm to add new terms.')
		return
	terms = []
	for term in VOCAB.keys():
		terms.append(term)
	terms.sort()
	self.add_mqueue(c,e.target,'%s terms.' % (len(terms),))
	
def cmd_v_allterms(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if not len(VOCAB):
		self.add_mqueue(c,e.target,'There are no existing terms. Use .addterm to add new terms.')
		return
	terms = []
	for term in VOCAB.keys():
		terms.append(term)
	terms.sort()
	allterms = []
	termpage = []
	for term in terms:
		allterms.append(term)
		tout = ', '.join(allterms)
		if len(tout) > 300:
			termpage.append(tout)
			#self.add_mqueue(c,e.source.nick,'%s' % (tout,))
			allterms = []
	if len(allterms):
		tout = ', '.join(allterms)
		termpage.append(tout)
		#self.add_mqueue(c,e.source.nick,'%s' % (tout,))
	if len(parms) < 2:
		self.add_mqueue(c,e.source.nick,'%s pages of terms in database. use %s09,01.%s <#>%s to specify a certain page.' % (len(termpage),chr(3),cmd,chr(3),))
	elif not is_int(parms[1]) or int(parms[1]) > len(termpage) or int(parms[1]) < 1:
		self.add_mqueue(c,e.source.nick,'Syntax: %s09,01.%s <Page#>%s' % (chr(3),cmd,chr(3),))
	else:
		n = int(parms[1])-1
		self.add_mqueue(c,e.source.nick,'%s' % (termpage[n],))
	
def cmd_r_help(self,c,e):
	me = e.source.nick.lower()
	karma = 0 if me not in BDATA['karma'] else BDATA['karma'][me]['count']	
	boss,oper,voiced = is_mod(self,c,e)
	cmds = []
	for cmd in self.chatcmds.keys():
		if 'cmd_b_' in cmd and boss:
			cmds.append(cmd.replace('cmd_b_','$'))
		elif 'cmd_o_' in cmd and oper:
			cmds.append(cmd.replace('cmd_o_','@'))
		elif 'cmd_v_' in cmd and voiced:
			cmds.append(cmd.replace('cmd_v_','+'))
		elif 'cmd_r_' in cmd:
			cmds.append(cmd.replace('cmd_r_',''))
		elif 'cmd_' in cmd and is_int(cmd.split('_')[1]):
			cmds.append(cmd.split('_')[2],'^')
			
	cmds.sort()	
	self.add_mqueue(c,e.target,'Commands: %s' % (', '.join(cmds),))
	
