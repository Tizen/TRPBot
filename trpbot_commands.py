VOCAB = {}
VOCAB_FNAME = 'trpbot.vocab'
KARMA_DEFAULT = {
	'count':0,
	'next':0,
	'host':'',
}
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
DELAY_SET = 5
DELAY_NOW = 0
USER_AGENT = {'User-agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'}

BOSS_TERMS = ['trpbot','version']


def uprint(text):
	print(text.encode('UTF-8'))

def is_mod(self,c,e):
	nick = e.source.nick.lower()
	mask = e.source
	boss = self.boss in e.source
	oper = False
	if e.target.lower() != c.get_nickname().lower():
		oper = self.channels[e.target].is_oper(e.source.nick) or boss
	oper = boss or oper
	mod = True if oper else False
	if 'mods' in BDATA and e.target in BDATA['mods']:
		for m in BDATA['mods'][e.target]:
			if '%s.users.quakenet.org' % m in mask.lower():
				mod = True
				break
	return (boss,oper,mod)
	
def is_dev(self,c,e):
	mask = e.source
	boss = self.boss in mask.lower()
	dev = True if boss else False
	if not dev and 'devs' in BDATA:
		for d in BDATA['devs']:
			if '%s.users.quakenet.org' % d in mask.lower():
				dev = True
				break
	return dev
	
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
	
def dict_hash(self,d):
	return self.hashlib.sha512(self.json.dumps(d,sort_keys=True)).hexdigest()

def save_bdata(self,force=False):
	global BDATA
	lastsave = BDATA['lastsave'] if 'lastsave' in BDATA else 0
	if lastsave >= self.tyme.time()-300.0 and not force:
		return
	try:
		with open(BDATA_FNAME,'wb') as f:
			self.json.dump(BDATA,f,sort_keys=True,indent=4)
		BDATA['lastsave'] = self.tyme.time()
	except IOError:
		uprint('Exception: save_bdata IOError')

def last_seen(self,c,e,nick,mask,when,what,deets):
	global BDATA
	if 'seen_history' not in BDATA:
		BDATA['seen_history'] = {}
	if 'host_usage' not in BDATA:
		BDATA['host_usage'] = {}
	if 'kiwii_cache' not in BDATA:
		BDATA['kiwii_cache'] = {}
	host = mask.split('!')[-1]
	hosts = [host,]
	if 'clients.kiwiirc.com' in host:
		khost = '%s@*.clients.kiwiirc.com' % (host.split('@')[0],)
		if khost not in BDATA['kiwii_cache']:
			ident = host.split('@')[0]
			validident = True
			try:
				int(ident,16)
			except ValueError:
				validident = False
			if validident:
				intip = []
				for slot in range(4):
					intip.append(str(int(ident[slot*2:(slot*2)+2],16)))
				ip2resolve = '.'.join(intip)
				BDATA['kiwii_cache'][khost] = '%s@%s' % (ident,ip2resolve)
				try:
					dns = self.socket.gethostbyaddr(ip2resolve)
				except self.socket.gaierror:
					dns = None
				except TypeError:
					dns = None
				except self.socket.herror:
					dns = None
				if dns and len(dns) == 3:
					BDATA['kiwii_cache'][khost] = '%s@%s' % (ident,dns[0],)
				hosts.append(BDATA['kiwii_cache'][khost])
		else:
			hosts.append(BDATA['kiwii_cache'][khost])
	for host in hosts:
		if host not in BDATA['host_usage']:
			BDATA['host_usage'][host] = []		
		if nick.lower() not in BDATA['host_usage'][host]:
			BDATA['host_usage'][host].append(nick.lower())		
		if nick.lower() not in BDATA['seen_history']:
			BDATA['seen_history'][nick.lower()] = []
		if host not in BDATA['seen_history'][nick.lower()]:
			BDATA['seen_history'][nick.lower()].append(host)
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
	uprint('Initializing...')
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
		uprint('mods format upgraded.')

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
	except TypeError:
		return False
		
def is_float(n):
	try:
		float(n)
		return True
	except ValueError:
		return False
	except TypeError:
		return False
		
def time_ago(s):
	s = int(s)
	m,s = divmod(s,60) if s >= 60 else (0,s)
	h,m = divmod(m,60) if m >= 60 else (0,m)
	d,h = divmod(h,24) if h >= 24 else (0,h)
	w,d = divmod(d,7) if d >= 7 else (0,d)
	y,w = divmod(w,52) if w >= 52 else (0,w)
	t = []
	for unit,abb in ((y,'y'),(w,'w'),(d,'d'),(h,'h'),(m,'m')):
		if unit > 0: t.append('%s%s' % (unit,abb))
	t.append('%ss' % (s,))
	ago = ' '.join(t[0:2])
	return ago
	
def find_host(self,nick):
	nick = nick.lower()
	retval = []
	if 'seen_history' in BDATA and nick in BDATA['seen_history']:
		for mask in BDATA['seen_history'][nick]:
			host = mask.split('!')[-1]
			retval.append(host)
			if 'clients.kiwiirc.com' in host:
				ident = host.split('@')[0]
				try:
					int(ident,16)
				except ValueError:
					continue
				intip = []
				for slot in range(4):
					intip.append(str(int(ident[slot*2:(slot*2)+2],16)))
				ip2resolve = '.'.join(intip)
				retval.append('%s@%s' % (ident,ip2resolve))
				try:
					dns = self.socket.gethostbyaddr(ip2resolve)
				except self.socket.gaierror:
					dns = None
				except TypeError:
					dns = None
				except self.socket.herror:
					dns = None
				if dns and len(dns) == 3:
					retval.append('%s@%s' % (ident,dns[0],))
	return retval
	
def fetch_clones(self,c,e,nick,depth):
	all_nicks = []
	new_nicks = [nick,]
	loops = 0
	while len(new_nicks) > len(all_nicks):
		check_these = []
		loops += 1
		if loops > depth:
			break
		for each_nick in new_nicks:
			if each_nick not in all_nicks:
				all_nicks.append(each_nick)
				check_these.append(each_nick)
		for each_nick in check_these:
			hosts = BDATA['seen_history'][each_nick]
			for host in hosts:
				if host not in BDATA['host_usage']:
					continue
				for host_nick in BDATA['host_usage'][host]:
					if host_nick not in new_nicks:
						new_nicks.append(host_nick)

	return new_nicks
'''	
def paste_send(self,c,e,cachename,checkchan=False):
	target = e.target if c.get_nickname().lower() != e.target.lower() else e.source.nick.lower()
	if checkchan:
		chan = checkchan
	else:
		chan = e.target if c.get_nickname().lower() != e.target.lower() else e.source.nick.lower()
	if 'context' not in BDATA or chan not in BDATA['context']:
		self.add_mqueue(c,target,'Context unavailable.')
		return
	if 'contextcache' in BDATA:
		oldcache,oldurl = BDATA['contextcache']
		newcache = dict_hash(self,BDATA['context'][chan])
		if newcache == oldcache:
			self.add_mqueue(c,target,'%s: %s' % (e.source.nick,oldurl,))
			return
	if not self.pbkey:
		self.add_mqueue(c,target,'Pastebin API key not found.')
		return
	pbcontext = []
	for each_context in BDATA['context'][chan]:
		c_time,c_msg = each_context
		pbcontext.append('[%s] %s' % (self.tyme.strftime('%H:%M:%S',self.tyme.localtime(c_time)),c_msg,))
	# pb go for launch
	try:
		pasteurl = self.pb.paste(
			self.botconfig['pb_devkey'],
			'\r\n'.join(pbcontext).encode('utf-8'),
			api_user_key=self.pbkey,
			paste_name='%s .context' % (chan,),
			paste_format='text',
			paste_private='unlisted',
			paste_expire_date='N'
		)
	except:
		pasteurl = None
	if pasteurl:
		self.add_mqueue(c,target,'%s: %s' % (e.source.nick,pasteurl,))
		if 'contextcache' in BDATA:
			oldcache,oldurl = BDATA['contextcache']
			paste_key = oldurl.split('/')[-1]
			try:
				result = self.pb.delete_paste(
					self.botconfig['pb_devkey'],
					self.pbkey,
					paste_key
				)
			except:
				pass
		BDATA['contextcache'] = (dict_hash(self,BDATA['context'][chan]),pasteurl)
		save_bdata(self)			
	else:
		self.add_mqueue(c,target,'%s: Unable to post to pastebin.' % (e.source.nick,))
'''

def cmd_b_votebans(self,c,e):
	if 'votebans' in BDATA:
		self.add_mqueue(c,e.target,'votebans: %s' % (BDATA['votebans'],))
	else:
		self.add_mqueue(self,e.target,'votebans is empty.')
	
def cmd_d_clones(self,c,e):
	msg = e.arguments[0].strip().strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) not in (2,3):
		self.add_mqueue(c,e.target,'Syntax: .%s <nick>' % (cmd,))
		return
	nick = parms[1].lower()
	if 'seen_history' not in BDATA or nick not in BDATA['seen_history']:
		self.add_mqueue(c,e.target,'%s: I have never seen that nick.' % (e.source.nick,))
		return
	depth = 1 if len(parms) != 3 or not is_int(parms[2]) else int(parms[2])
	new_nicks = fetch_clones(self,c,e,nick,depth)
	if len(new_nicks) == 1:
		self.add_mqueue(c,e.target,'No clones found for %s.' % (nick,))
	else:
		self.add_mqueue(c,e.target,'found %s clones: %s' % (len(new_nicks),', '.join(new_nicks),))
		
def cmd_b_bdatainfo(self,c,e):
	msg = e.arguments[0].strip().strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) == 1:
		self.add_mqueue(c,e.target,'bdata has %s keys.' % (len(BDATA.keys()),))
	else:
		key = parms[1]
		if key not in BDATA:
			self.add_mqueue(c,e.target,'bdata does not contain key "%s""' % (key,))
		else:
			self.add_mqueue(c,e.target,'bdata[%s] has %s length (%s)' % (key,len(BDATA[key]),type(BDATA[key]),))
			
def cmd_b_delaynow(self,c,e):
	self.add_mqueue(c,e.target,'DELAY_NOW: %s / DELAY_SET: %s' % (DELAY_NOW,DELAY_SET))
	
def cmd_b_test(self,c,e):
	global BDATA
	msg = e.arguments[0].strip().strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) == 2:
		nick = parms[1].lower()
		if not self.channels[e.target].has_user(nick):
			self.add_mqueue(c,e.target,'user is not in the channel.')
			return
		try:
			host = BDATA['seen'][nick][0]
			self.add_mqueue(c,e.target,'result: %s' % (host,))
		except:
			self.add_mqueue(c,e.target,'exception.')
			self.traceback.print_exc(file=self.sys.stdout)

def on_ctcp(self,c,e):
	if e.arguments[0] == 'DCC':
		uprint('on_ctcp: %s/%s/%s' % (e.arguments,e.target,e.source,))
		msg = e.arguments[1]
	
	
def cmd_r_permissions(self,c,e):
	boss,oper,mod = is_mod(self,c,e)
	dev = is_dev(self,c,e)
	perms = []
	if boss: perms.append('boss')
	if dev: perms.append('dev')
	if oper: perms.append('oper')
	if mod: perms.append('mod')
	perms.append('user')
	self.add_mqueue(c,e.target,'Permissions: %s' % (', '.join(perms),))

def cmd_b_die(self,c,e):
	raise KeyboardInterrupt('Die Command Received.')
	
def cmd_d_findhostnicks(self,c,e):
	# self.fnmatch(source,pattern)
	msg = e.arguments[0].strip().strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) != 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <search pattern>' % (cmd,))
		return
	pattern = parms[1].lower()
	matches = {}
	maxmatches = 15
	for host in BDATA['host_usage'].keys():
		if self.fnmatch(host.lower(),pattern) and host.lower() not in matches:
			matches[host.lower()] = BDATA['host_usage'][host]
	for host in BDATA['kiwii_cache'].keys():
		lhost = host.lower()
		if self.fnmatch(lhost,pattern) and lhost not in matches:
			matches[lhost] = []
			for uhost in BDATA['host_usage'].keys():
				if self.fnmatch(uhost.lower(),lhost):
					matches[lhost] += BDATA['host_usage'][uhost]
		lhost = BDATA['kiwii_cache'][host].lower()
		if self.fnmatch(lhost,pattern) and lhost not in matches:
			matches[lhost] = []
			whost = '*@%s' % (lhost.split('@')[-1],)
			for uhost in BDATA['host_usage'].keys():
				if self.fnmatch(uhost.lower(),whost):
					matches[lhost] += BDATA['host_usage'][uhost]
		#if len(matches.keys()) > maxmatches:
		#	break
	if len(matches.keys()) > 1:
		matchdeets = []
		for match in matches:
			for nmatch in matches[match]:
				if nmatch not in matchdeets:
					matchdeets.append(nmatch)
		if len(matchdeets) > maxmatches:
			self.add_mqueue(c,e.target,'Too many matches (%s). Narrow your search pattern.' % (len(matchdeets),))
		else:
			self.add_mqueue(c,e.target,'%s matches: %s' % (len(matchdeets),', '.join(matchdeets),))
	elif len(matches.keys()) == 1:
		for match in matches:
			self.add_mqueue(c,e.target,'Match: %s (%s)' % (match,', '.join(matches[match]),))
	else:
		self.add_mqueue(c,e.target,'No matches found.')
	
def cmd_d_findhost(self,c,e):
	# self.fnmatch(source,pattern)
	msg = e.arguments[0].strip().strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) != 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <search pattern>' % (cmd,))
		return
	pattern = parms[1].lower()
	matches = {}
	maxmatches = 10
	for host in BDATA['host_usage'].keys():
		if self.fnmatch(host.lower(),pattern) and host.lower() not in matches:
			matches[host.lower()] = BDATA['host_usage'][host]
	for host in BDATA['kiwii_cache'].keys():
		lhost = host.lower()
		if self.fnmatch(lhost,pattern) and lhost not in matches:
			matches[lhost] = []
			for uhost in BDATA['host_usage'].keys():
				if self.fnmatch(uhost.lower(),lhost):
					matches[lhost] += BDATA['host_usage'][uhost]
		lhost = BDATA['kiwii_cache'][host].lower()
		if self.fnmatch(lhost,pattern) and lhost not in matches:
			matches[lhost] = []
			whost = '*@%s' % (lhost.split('@')[-1],)
			for uhost in BDATA['host_usage'].keys():
				if self.fnmatch(uhost.lower(),whost):
					matches[lhost] += BDATA['host_usage'][uhost]
		#if len(matches.keys()) > maxmatches:
		#	break
	if len(matches.keys()) > maxmatches:
		self.add_mqueue(c,e.target,'Too many matches (%s). Narrow your search pattern.' % (len(matches.keys()),))
	elif len(matches.keys()) > 1:
		matchdeets = []
		for match in matches:
			if len(matches[match]) < 1:
				continue
			info = '%s (%s nick%s)' % (match,len(matches[match]),'' if len(matches[match]) == 1 else 's')
			matchdeets.append(info)
		self.add_mqueue(c,e.target,'%s matches: %s' % (len(matches),', '.join(matchdeets),))
	elif len(matches.keys()) == 1:
		for match in matches:
			self.add_mqueue(c,e.target,'Match: %s (%s)' % (match,', '.join(matches[match]),))
	else:
		self.add_mqueue(c,e.target,'No matches found.')

	
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
		mask = mask.split('!')[1] if len(mask.split('!')) > 1 else mask
		self.add_mqueue(c,e.target,'%s (%s) last seen %s ago %s' % (nick,mask,time_ago(ago),about))
	else:
		self.add_mqueue(c,e.target,'%s has not been seen.' % (nick,))
		
def cmd_r_memos(self,c,e):
	nick = e.source.nick
	msg = e.arguments[0].strip().strip()	
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if 'memos' not in BDATA or nick.lower() not in BDATA['memos'] or len(BDATA['memos'][nick.lower()]) < 1:
		self.add_mqueue(c,nick,'You have no memos. To send a memo, tell me %s09.memo send <nick> <message>%s' % (chr(3),chr(3),))
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

def memo_sent(self,c,e):
	global BDATA
	nick = e.source.nick
	msg = e.arguments[0].strip().strip()
	parms = msg.split(' ')
	if len(parms) != 2:
		self.add_mqueue(c,nick,'Syntax: .memo sent')
		return
	if 'memos' not in BDATA:
		self.add_mqueue(c,nick,'You have no sent memos.')
		return
	msgs = []
	for memonick in BDATA['memos']:
		for memo in BDATA['memos'][memonick]:
			sender,tyme,readflag,msg = memo
			if sender.lower() == nick.lower():
				msgs.append((memonick,memo))
	n = 1
	for memonick,memo in msgs:
		sender,tyme,readflag,msg = memo
		preview = '#%s [%s] %s <%s>' % (n,'Read' if readflag else 'Unread',time_ago(self.tyme.time()-tyme),memonick,)
		mlen = 50-len(preview)
		smsg = ''
		if mlen > 0:
			smsg = msg[:mlen] if mlen < len(msg) else msg
		preview = '%s %s' % (preview,smsg)
		self.add_mqueue(c,nick,'%s (.memo sent %s)' % (preview,n))
		n += 1

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
	boss,oper,voiced = is_mod(self,c,e)
	last_seen(self,c,e,nick,e.source,self.tyme.time(),'pmsg','') 
	uprint('<%s> %s' % (nick,msg,))
	if 'ignore' in BDATA:
		for ignore in BDATA['ignore']:
			if self.fnmatch(e.source.lower(),ignore):
				return
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
				
		elif parms[1].lower() not in ('send','read','del','delete','sent'):
			self.add_mqueue(c,nick,'Syntax: .%s <send/read/delete>' % (cmd,))
		elif parms[1].lower() == 'send':
			memo_send(self,c,e)
		elif parms[1].lower() == 'read':
			memo_read(self,c,e)
		elif parms[1].lower() in ('del','delete'):
			memo_delete(self,c,e)
		elif parms[1].lower() == 'sent':
			memo_sent(self,c,e)
	elif cmd == 'ud':
		cmd_r_ud(self,c,e)
		return
	elif cmd == 'ignore' and boss:
		cmd_b_ignore(self,c,e)
		return
	elif cmd == 'kbc' and boss:
		cmd_b_kbc(self,c,e)
		return
	elif cmd == 'context':
		if len(parms) == 2:
			cmd_r_context(self,c,e,parms[1])
		else:
			cmd_r_context(self,c,e)
		return
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
			with open('kicks.txt') as f:
				kicklines = f.readlines()
			kick = self.rng.choice(kicklines)
			kick = kick.strip()
			kick = kick.replace('%k',nick)
			kick = kick.replace('%u',e.source.nick)
			kickban(self,c,e,target,bantime=60*5,kickreason='%s (lurking, 5 minute ban)' % (kick,))
			print('kickban: %s (%s)' % (target,'%s (lurking, 5 minute ban)' % (kick,),))
			
def cmd_o_kick(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) == 1:
		self.add_mqueue(c,e.target,'Syntax: .%s <nick> [reason]' % (cmd,))
	elif not self.channels[e.target].has_user(parms[1]):
		self.add_mqueue(c,e.target,'User not found.')
	else:
		target = parms[1]
		with open('kicks.txt') as f:
			kicklines = f.readlines()
		kick = self.rng.choice(kicklines)
		kick = kick.strip()
		kick = kick.replace('%k',target)
		kick = kick.replace('%u',e.source.nick)
		c.kick(e.target,target,kick)

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
		
def cmd_d_tmaskinfo(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 3:
		self.add_mqueue(c,e.target,'Syntax: .%s <chan> <nick>' % (cmd,))
	else:
		chan = parms[1]
		user = parms[2]
		if chan not in self.channels:
			self.add_mqueue(c,e.target,'%s is not a valid channel.' % (chan,))
		tboss,toper,tmod,tmaskp,tmask = is_tmod(self,c,e,user,chan)
		self.add_mqueue(c,e.target,'%s tmod=%s premask=%s postmask=%s' % (user,tmod,tmaskp,tmask,))
	
def add_context(self,c,e,msg=None):
	if 'context' not in BDATA:
		BDATA['context'] = {}
	cminutes = get_setting('context',10)
	cminutes = 10 if not is_int(cminutes) or int(cminutes) < 1 else int(cminutes)
	chan = e.target if c.get_nickname().lower() != e.target.lower() else e.source.nick.lower()
	msg = '<%s> %s' % (e.source.nick,e.arguments[0],) if not msg else msg
	context = (self.tyme.time(),msg)
	if chan not in BDATA['context'] or BDATA['context'][chan][-1][0] < self.tyme.time()-(60*cminutes):
		# initialize dict if empty or last context was > 10m ago.
		BDATA['context'][chan] = []
	# if the context is greater than 5 lines, pop off each line that is > 10m.
	while len(BDATA['context'][chan]) > 5:
		if BDATA['context'][chan][0][0] < self.tyme.time()-(60*cminutes):
			BDATA['context'][chan].pop(0)
		else:
			break
	BDATA['context'][chan].append(context)
	save_bdata(self)
	
def get_setting(key,value=None):
	key = key.lower()
	retval = value
	if 'settings' in BDATA and key in BDATA['settings']:
		retval = BDATA['settings'][key]
	return retval
	
def cmd_b_settings(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	dosave = False
	if 'settings' not in BDATA:
		BDATA['settings'] = {}
		dosave = True
	if len(parms) == 1:
		if not len(BDATA['settings']):
			self.add_mqueue(c,e.target,'No settings in database. Use .settings add <key> <value>')
		else:
			setlen = len(BDATA['settings'])
			self.add_mqueue(c,e.target,'%s setting%s in database: %s' % (setlen,'' if setlen == 1 else 's',', '.join(BDATA['settings'].keys()),))
		return
	subcmd = parms[1].lower()
	if subcmd == 'add' and len(parms) >= 4:
		setkey = parms[2].lower()
		setval = ' '.join(parms[3:])
		if setkey in BDATA['settings']:
			self.add_mqueue(c,e.target,'Key already exists in settings database. Use .settings set <key> <value>')
		else:
			BDATA['settings'][setkey] = setval
			self.add_mqueue(c,e.target,'Setting added.')
			dosave = True
	elif subcmd == 'set' and len(parms) >= 4:
		setkey = parms[2].lower()
		setval = ' '.join(parms[3:])
		if setkey not in BDATA['settings']:
			self.add_mqueue(c,e.target,'Key not found in settings database. Use .settings add <key> <value>')
		elif BDATA['settings'][setkey] == setval:
			self.add_mqueue(c,e.target,'Setting unchanged.')
		else:
			BDATA['settings'][setkey] = setval
			self.add_mqueue(c,e.target,'Setting modified.')
			dosave = True
	elif subcmd in ('del','delete','rem','remove') and len(parms) == 3:
		setkey = parms[2].lower()
		if setkey not in BDATA['settings']:
			self.add_mqueue(c,e.target,'Key not found in settings database. To view available keys, use .settings')
		else:
			del BDATA['settings'][setkey]
			self.add_mqueue(c,e.target,'Key removed from settings database.')
			dosave = True
	elif subcmd in BDATA['settings'] and len(parms) == 2:
		self.add_mqueue(c,e.target,'%s: %s' % (subcmd,BDATA['settings'][subcmd],))
	if dosave:
		save_bdata(self)
	
def cmd_b_fixcontext(self,c,e):
	BDATA['context'] = {}
	save_bdata(self)
	self.add_mqueue(c,e.target,'done.')
	
def cmd_r_context(self,c,e,checkchan=None):
	target = e.target if c.get_nickname().lower() != e.target.lower() else e.source.nick.lower()
	if checkchan:
		chan = checkchan
	else:
		chan = e.target if c.get_nickname().lower() != e.target.lower() else e.source.nick.lower()
	if 'context' not in BDATA or chan not in BDATA['context']:
		self.add_mqueue(c,target,'Context unavailable.')
		return
	if 'contextcache' in BDATA:
		oldcache,oldurl = BDATA['contextcache']
		newcache = dict_hash(self,BDATA['context'][chan])
		if newcache == oldcache:
			self.add_mqueue(c,target,'%s: %s' % (e.source.nick,oldurl,))
			return
	if not self.pbkey:
		self.add_mqueue(c,target,'Pastebin API key not found.')
		return
	pbcontext = []
	for each_context in BDATA['context'][chan]:
		c_time,c_msg = each_context
		pbcontext.append('[%s] %s' % (self.tyme.strftime('%H:%M:%S',self.tyme.localtime(c_time)),c_msg,))
	# pb go for launch
	try:
		pasteurl = self.pb.paste(
			self.botconfig['pb_devkey'],
			'\r\n'.join(pbcontext).encode('utf-8'),
			api_user_key=self.pbkey,
			paste_name='%s .context' % (chan,),
			paste_format='text',
			paste_private='unlisted',
			paste_expire_date='N'
		)
	except:
		pasteurl = None
	if pasteurl:
		self.add_mqueue(c,target,'%s: %s' % (e.source.nick,pasteurl,))
		if 'contextcache' in BDATA:
			oldcache,oldurl = BDATA['contextcache']
			paste_key = oldurl.split('/')[-1]
			try:
				result = self.pb.delete_paste(
					self.botconfig['pb_devkey'],
					self.pbkey,
					paste_key
				)
			except:
				pass
		BDATA['contextcache'] = (dict_hash(self,BDATA['context'][chan]),pasteurl)
		save_bdata(self)			
	else:
		self.add_mqueue(c,target,'%s: Unable to post to pastebin.' % (e.source.nick,))

def on_action(self,c,e):
	msg = '* %s %s' % (e.source.nick,e.arguments[0],)
	uprint(msg)
	if 'ignore' in BDATA:
		for ignore in BDATA['ignore']:
			if self.fnmatch(e.source.lower(),ignore):
				return
	add_context(self,c,e,msg)
	
def on_pubmsg(self,c,e):
	global BDATA
	global DELAY_NOW		
	msg = e.arguments[0].strip()
	formatmsg = '<%s%s> %s' % (e.source.nick,e.target,msg)
	try:
		uprint(formatmsg[:79])
	except:
		pass
	if 'ignore' in BDATA:
		for ignore in BDATA['ignore']:
			if self.fnmatch(e.source.lower(),ignore):
				return
	if not self.fnmatch(msg,'.*'):
		add_context(self,c,e)
	last_seen(self,c,e,e.source.nick,e.source,self.tyme.time(),'msg',e.target)
	#do_lurk_kick(self,c,e)
	if not len(msg):
		return
	if 'activity' not in BDATA:
		BDATA['activity'] = {}
	if e.target not in BDATA['activity']:
		BDATA['activity'][e.target] = {}
	BDATA['activity'][e.target][e.source.nick.lower()] = self.tyme.time()
	parms = msg.split(' ')
	if len(parms) > 1 and parms[0].lower() in ('%s,' % (c.get_nickname().lower(),),c.get_nickname().lower(),'bot','bot:','bot,','%s:' % (c.get_nickname().lower(),)):
		tothink = ' '.join(parms[1:]).lower()
		tothink = tothink.replace(c.get_nickname().lower(),'cleverbot')
		if e.source.nick.lower() in self.cbots:
			cbot = self.cbots[e.source.nick.lower()]
		else:
			cbot = self.cbot.create_session()
			self.cbots[e.source.nick.lower()] = cbot
		try:
			response = cbot.think(tothink)
		except UnicodeEncodeError:
			response = ''
		if response:
			response = response.lower()
			response = response.replace('cleverbot',c.get_nickname(),)
			self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,response,))
			return
	boss,oper,voiced = is_mod(self,c,e)
	dev = is_dev(self,c,e)
	rcmd = parms[0].lower().replace('.','cmd_r_')
	vcmd = parms[0].lower().replace('.','cmd_v_') if voiced else ''
	ocmd = parms[0].lower().replace('.','cmd_o_') if oper else ''
	bcmd = parms[0].lower().replace('.','cmd_b_') if boss else ''
	dcmd = parms[0].lower().replace('.','cmd_d_') if dev else ''
	for cmd in (dcmd,bcmd,ocmd,vcmd,rcmd):
		if cmd in self.chatcmds:
			self.chatcmds[cmd](self,c,e)
			break
	if '.' in parms[0]:
		me = e.source.nick.lower()
		karma = 0 if me not in BDATA['karma'] else BDATA['karma'][me]['count']	
		cmds = []
		rancmd = False
		for cmd in self.chatcmds.keys():
			if 'cmd_' in cmd and is_int(cmd.split('_')[1]) and int(cmd.split('_')[1]) <= karma and '.'+cmd.split('_')[2] == parms[0].lower():
				try:
					self.chatcmds[cmd](self,c,e)
					rancmd = True
				except:
					self.add_mqueue(c,'Tizen','%s exception' % (cmd,))
					self.traceback.print_exc(file=self.sys.stdout)
		if rancmd:
			return
	lmsg = msg.lower()
	# what is 250lbs to kg?
	match = self.re.match("^(what is |whats |what's )?(?P<found>.*)(lb|lbs){1}( to kg| to kgs)?(\?)?$",lmsg)
	if match:
		amnt = match.group('found')
		if is_float(amnt):
			amnt = float(amnt)
			kgs = ("%.3f" % (amnt/2.2046226218,)).replace(".000", "")			
			self.add_mqueue(c,e.target,'%s: %skgs' % (e.source.nick,kgs,))
			return
	match = self.re.match("^(what is |whats |what's )?(?P<found>.*)(kg|kgs){1}( to lb| to lbs)?(\?)?$",lmsg)
	if match:
		amnt = match.group('found')
		if is_float(amnt):
			amnt = float(amnt)
			lbs = ("%.3f" % (amnt*2.2046226218,)).replace(".000", "")			
			self.add_mqueue(c,e.target,'%s: %slbs' % (e.source.nick,lbs,))
			return
	# what is 98.6f to c?
	match = self.re.match("^(what is |whats |what's )?(?P<found>.*)f( to c)?(\?)?$",lmsg)
	if match:
		amnt = match.group('found')
		if is_float(amnt):
			amnt = float(amnt)
			amnt = ((amnt-32.0)*5.0)/9.0
			lbs = ("%.1f" % (amnt,)).replace(".0", "")			
			self.add_mqueue(c,e.target,'%s: %sC' % (e.source.nick,lbs,))
			return
	match = self.re.match("^(what is |whats |what's )?(?P<found>.*)c( to f)?(\?)?$",lmsg)
	if match:
		amnt = match.group('found')
		if is_float(amnt):
			amnt = float(amnt)
			amnt = ((amnt*9.0)/5.0)+32.0
			lbs = ("%.1f" % (amnt,)).replace(".0", "")			
			self.add_mqueue(c,e.target,'%s: %sF' % (e.source.nick,lbs,))
			return
	#M x 3.281 = Ft
	match = self.re.match("^(what is |whats |what's )?(?P<found>.*)(m| meter| meters){1}( to f| to feet)?(\?)?$",lmsg)
	if match:
		amnt = match.group('found')
		if is_float(amnt):
			amnt = float(amnt)
			kgs = ("%.2f" % (amnt*3.281,)).replace(".00", "")
			self.add_mqueue(c,e.target,'%s: %sft' % (e.source.nick,kgs,))
			return
	match = self.re.match("^(what is |whats |what's )?(?P<found>.*)(ft| feet|\'){1}( to m| to meters)?(\?)?$",lmsg)
	if match:
		amnt = match.group('found')
		if is_float(amnt):
			amnt = float(amnt)
			kgs = ("%.2f" % (amnt/3.281,)).replace(".00", "")
			self.add_mqueue(c,e.target,'%s: %s meters' % (e.source.nick,kgs,))
			return
	# cm = in / 0.3937
	match = self.re.match("^(what is |whats |what's )?(?P<found>.*)(in| inch| inches|\"){1}( to cm| to centimetre| to centimetres)?(\?)?$",lmsg)
	if match:
		amnt = match.group('found')
		if is_float(amnt):
			amnt = float(amnt)
			kgs = ("%.2f" % (amnt/0.3937,)).replace(".00", "")
			self.add_mqueue(c,e.target,'%s: %scm' % (e.source.nick,kgs,))
			return
	match = self.re.match("^(what is |whats |what's )?(?P<found>.*)(cm| centimetre| centimetres){1}( to in| to inches| to inch)?(\?)?$",lmsg)
	if match:
		amnt = match.group('found')
		if is_float(amnt):
			amnt = float(amnt)
			kgs = ("%.2f" % (amnt*0.3937,)).replace(".00", "")
			self.add_mqueue(c,e.target,'%s: %sin' % (e.source.nick,kgs,))
			return
	match = self.re.match("^(what is |whats |what's )?(?P<found>.*)(cm| centimetre| centimetres){1}( to ft| to feet)?(\?)?$",lmsg)
	if match:
		amnt = match.group('found')
		if is_float(amnt):
			amnt = float(amnt)
			kgs = ("%.2f" % ((amnt*0.3937)/12.0,)).replace(".00", "")
			self.add_mqueue(c,e.target,'%s: %sft' % (e.source.nick,kgs,))
			return
	match = self.re.match("^(.*)\+\+$",parms[0])
	if (parms[0] == '+1' and len(parms) == 2) or match:
		target = parms[1] if not match else match.groups()[0]
		target = target.lower()
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
			BDATA['karma'][giver] = KARMA_DEFAULT.copy()
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
			BDATA['karma'][giver]['next'] = self.tyme.time() + 60*60*3 # 3 hours
		if target not in BDATA['karma']:
			BDATA['karma'][target] = KARMA_DEFAULT.copy()
		BDATA['karma'][target]['count'] += 1
		self.add_mqueue(c,e.target,'+1 karma awarded to %s by %s.' % (target,giver))
		save_bdata(self)
		return
	match = self.re.match("^(.*)\-\-$",parms[0])
	if oper and ((parms[0] == '-1' and len(parms) == 2) or match):
		target = parms[1].lower() if not match else match.groups()[0]
		giver = e.source.nick.lower()
		if not self.channels[e.target].has_user(target):
			#self.add_mqueue(c,e.target,'That user is not in the channel.')
			return
		if giver not in BDATA['karma']:
			BDATA['karma'][giver] = KARMA_DEFAULT.copy()
		if target not in BDATA['karma']:
			BDATA['karma'][target] = KARMA_DEFAULT.copy()
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
				uprint('http fetch exception: %s' % (self.sys.exc_info(),))
				self.traceback.print_exc(file=self.sys.stdout)
				#print('allimg=%s parm=%s' % (allimg,parm))
	if len(parms) > 1 and parms[-1].lower() in ('%s.' % (c.get_nickname().lower(),),'bot','bot.','bot?','bot!',c.get_nickname().lower(),'%s?' % (c.get_nickname().lower(),)):
		tothink = ' '.join(parms[:-1])
		tothink = tothink.replace(c.get_nickname().lower(),'cleverbot')
		if e.source.nick.lower() in self.cbots:
			cbot = self.cbots[e.source.nick.lower()]
		else:
			cbot = self.cbot.create_session()
			self.cbots[e.source.nick.lower()] = cbot
		try:
			response = cbot.think(tothink)
		except UnicodeEncodeError:
			response = ''
		if response:
			response = response.lower()
			response = response.replace('cleverbot',c.get_nickname(),)
			self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,response,))
			return
	randchat = get_setting('randchat_'+e.target,20)
	randchat = 20 if not is_int(randchat) or int(randchat) < 1 else int(randchat)
	if randchat > 20 and self.rng.randint(1,randchat) == 1:
		tothink = ' '.join(parms)
		tothink = tothink.replace(c.get_nickname().lower(),'cleverbot')
		if e.source.nick.lower() in self.cbots:
			cbot = self.cbots[e.source.nick.lower()]
		else:
			cbot = self.cbot.create_session()
			self.cbots[e.source.nick.lower()] = cbot
		try:
			response = cbot.think(tothink)
		except UnicodeEncodeError:
			response = ''
		if response:
			response = response.lower()
			response = response.replace('cleverbot',c.get_nickname(),)
			self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,response,))
			return
		
def cmd_r_ud(self,c,e):
	chan = e.source.nick if e.target == c.get_nickname() else e.target
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 2:
		self.add_mqueue(c,chan,'Syntax: .%s <Urban Dictionary Search Term>' % (cmd,))
	else:
		term = ' '.join(parms[1:])
		result = self.udquery.define(term)
		udurl = None
		result = result.replace('\r',' ')
		msg = ''.join(result.splitlines())
		if len(msg) > 386:
			msg = msg[:386]
			udurl = 'http://www.urbandictionary.com/define.php?%s' % (self.urllib.urlencode({'term':term}),)
		self.add_mqueue(c,chan,msg if msg else 'UrbanDictionary definition not found.')
		if udurl:
			self.add_mqueue(c,chan,'Read full description here: %s' % (udurl,))
			
def cmd_r_moneyconvert(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 4 or not is_float(parms[1]):
		self.add_mqueue(c,e.target,'Syntax: .%s <amount> <source> <destination>' % (cmd,))
		return
	if 'currency' not in BDATA:
		result = self.requests.get('http://www.freecurrencyconverterapi.com/api/v3/currencies')
		content = result.content if result.status_code == 200 else None
		if content:
			results = self.json.loads(content)
			if 'results' in results:
				BDATA['currency'] = results['results']
				save_bdata(self)
	if 'currency' not in BDATA:
		self.add_mqueue(c,e.target,'Could not read currency data.')
		return
	scanfor = [[parms[2],'source'],[parms[3],'destination']]
	scanfound = {'source':None,'destination':None}
	for scan,slot in scanfor:
		if scan.upper() in BDATA['currency']:
			scanfound[slot] = scan.upper()
		else:
			self.add_mqueue(c,e.target,'Could not locate currency "%s"' % (scan,))
			return
	qcode = '%s_%s' % (scanfound['source'],scanfound['destination'],)
	buildurl = 'http://www.freecurrencyconverterapi.com/api/v3/convert?%s' % (self.urllib.urlencode({'q':qcode,'compact':'y'}),)
	result = self.requests.get(buildurl)
	content = result.content if result.status_code == 200 else None
	if not content:
		self.add_mqueue(c,e.target,'Could not convert currency "%s"' % (qcode,))
		return
	results = self.json.loads(content)
	if qcode not in results:
		self.add_mqueue(c,e.target,'Could not convert currency "%s"' % (qcode,))
		return
	amount = float(parms[1]) * float(results[qcode]['val'])
	source_symbol = BDATA['currency'][scanfound['source']]['currencySymbol']
	dest_symbol = BDATA['currency'][scanfound['destination']]['currencySymbol']
	self.add_mqueue(c,e.target,'%s: %s%s => %s%.2f' % (e.source.nick,source_symbol,parms[1],dest_symbol,amount))	
		
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
			self.add_mqueue(c,e.target,'Syntax: .%s add <quote>' % (cmd,))
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
			openerout = open_line
			if 'subhazard' == open_author:
				openerout = '%s *nuclear termination*' % (openerout,)
			self.add_mqueue(c,e.target,'Random opener: "%s" %s09,01^%s%s to upvote this opener.' % (openerout,chr(3),opener,chr(3),))
			do_save = True
		else:
			opener_cmd = ' Say %s09,01.addopener <your suave-as-fuck line here>%s to add a new opener.' % (chr(3),chr(3),)
			self.add_mqueue(c,e.target,'No openers have been added yet.%s' % ('' if not voiced else opener_cmd,))
	elif parms[1].lower() in BDATA['openers']:
		opener = parms[1].lower()
		open_line,open_author,open_time,open_karma,open_hits = BDATA['openers'][opener]
		BDATA['openers'][opener] = open_line,open_author,open_time,open_karma,open_hits+1
		openerout = open_line
		if 'subhazard' == open_author:
			openerout = '%s *nuclear termination*' % (openerout,)
		open_msg = '%s: %s (%s karma)' % (opener,openerout,len(open_karma))
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
		dev = is_dev(self,c,e)
		if dev or nick == open_author:
			del BDATA['openers'][opener]
			do_save = True
			self.add_mqueue(c,e.target,'Opener %s09,01%s%s deleted.' % (chr(3),opener,chr(3),))
		else:
			self.add_mqueue(c,e.target,'Unable to delete opener.')
	if do_save:
		save_bdata(self)
		
def labelinfo(chan,nick):
	if 'labels' not in BDATA or chan not in BDATA['labels']:
		return None
	nick = nick.lower()
	for label in BDATA['labels'][chan]:
		if nick in BDATA['labels'][chan][label]['mods']:
			return [label,'mod',BDATA['labels'][chan][label]['mods'][nick]]
		if nick in BDATA['labels'][chan][label]['nicks'] and BDATA['labels'][chan][label]['nicks'][nick]:
			return [label,'usr',BDATA['labelhost'][nick]]
	return None
	
def cmd_b_labelinfo(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) == 3:
		chan,nick = parms[1].lower(),parms[2].lower()
		self.add_mqueue(c,e.target,'labelinfo(%s,%s): %s' % (chan,nick,labelinfo(chan,nick),))
		
def cmd_r_labels(self,c,e):
	global BDATA
	do_save = False
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if 'labels' not in BDATA or e.target not in BDATA['labels'] or len(BDATA['labels'][e.target]) == 0:
		self.add_mqueue(c,e.target,'No labels exist. A channel op may add labels by saying %s09.label add <label name>%s09' % (chr(3),chr(3),))
	else:
		if len(parms) > 1:
			label = ' '.join(parms[1:]).lower()
			if label in BDATA['labels'][e.target]:
				mods = BDATA['labels'][e.target][label]['mods'].keys()
				if not len(mods):
					self.add_mqueue(c,e.target,'Label has no mods. A channel op may add mods by saying %s09.labelmod add <nick> <label name>%s09' % (chr(3),chr(3),))
				else:
					self.add_mqueue(c,e.target,'Label %s has %s mod%s: %s' % (label,len(mods),'' if len(mods) == 1 else 's',', '.join(mods),))
			else:
				self.add_mqueue(c,e.target,'Label does not exist.')
		else:
			count = len(BDATA['labels'][e.target].keys())
			self.add_mqueue(c,e.target,'%s label%s: %s' % (count,'' if count == 1 else 's',', '.join(BDATA['labels'][e.target].keys()),))
			
def cmd_r_labelme(self,c,e):
	global BDATA
	do_save = False
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if 'labels' not in BDATA:
		BDATA['labels'] = {}
	if e.target not in BDATA['labels']:
		BDATA['labels'][e.target] = {}
	if len(parms) < 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <label name>' % (cmd,))
		return
	nick = e.source.nick.lower()
	host = BDATA['seen'][nick][0].split('@')[-1]
	label = ' '.join(parms[1:]).lower()
	noadd = False
	delentry = None
	for each_label in BDATA['labels'][e.target].keys():
		if nick in BDATA['labels'][e.target][each_label]['nicks']:
			if BDATA['labels'][e.target][each_label]['nicks'][nick]:
				self.add_mqueue(c,e.target,'You are already a verified member of the %s label.' % (each_label,))
				noadd = True
			elif each_label == label:
				self.add_mqueue(c,e.target,'You are already waiting to be verified as a member of the %s label.' % (each_label,))
				noadd = True
			else:
				delentry = each_label			
			break
		if nick in BDATA['labels'][e.target][each_label]['mods']:
			self.add_mqueue(c,e.target,'Your nick is already listed as a label mod for %s.' % (each_label,))
			noadd = True
			break
	if '.users.quakenet.org' not in host:
		self.add_mqueue(c,e.target,'%s: You must auth with Q and set mode +x before requesting a label.' % (e.source.nick,))
		return
	pretext = 'Label requested.'
	if delentry:
		del BDATA['labels'][e.target][delentry]['nicks'][nick]
		save_bdata(self)
		pretext = 'Request for %s label cancelled. New label requested.' % (delentry,)
	if noadd:
		return
	if label not in BDATA['labels'][e.target]:
		self.add_mqueue(c,e.target,'Label does not exist. Use the %s09.labels%s command to see a list of available labels.' % (chr(3),chr(3),))
		return
	if 'labelhost' not in BDATA:
		BDATA['labelhost'] = {}
	nicktaken = False
	for lnick in BDATA['labelhost']:
		if host == BDATA['labelhost'][lnick]:
			nicktaken = lnick
			break
	if nicktaken and nicktaken != nick:
		self.add_mqueue(c,e.target,'Your host has already been allocated to "%s".' % (nicktaken,))
		return
	BDATA['labelhost'][nick] = host
	BDATA['labels'][e.target][label]['nicks'][nick] = False
	save_bdata(self)
	self.add_mqueue(c,e.target,'%s A label mod for %s must say %s09.labelverify %s%s to confirm your request.' % (pretext,label,chr(3),nick,chr(3),))
	
		
def cmd_o_label(self,c,e):
	global BDATA
	do_save = False
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if 'labels' not in BDATA:
		BDATA['labels'] = {}
	if e.target not in BDATA['labels']:
		BDATA['labels'][e.target] = {}
	if len(parms) < 3 or parms[1].lower() not in ('add','delete','del','rem','remove','clear'):
		self.add_mqueue(c,e.target,'Syntax: .%s <add|del> <label name>' % (cmd,))
	elif parms[1].lower() == 'add':
		label = ' '.join(parms[2:]).lower()
		if label in BDATA['labels'][e.target]:
			self.add_mqueue(c,e.target,'Label already exists.')
		else:
			do_save = True
			BDATA['labels'][e.target][label] = {'mods':{},'nicks':{},}
			self.add_mqueue(c,e.target,'Label added.')
	else:
		label = ' '.join(parms[2:]).lower()
		if label not in BDATA['labels'][e.target]:
			self.add_mqueue(c,e.target,'Label does not exist.')
		else:
			count = len(BDATA['labels'][e.target][label]['nicks'].keys())
			if parms[1].lower() != 'clear' and count > 0:
				self.add_mqueue(c,e.target,'Label has %s nick%s associated. Use %s09.%s clear %s%s to confirm you want to delete this label.' % (count,'' if count == 1 else 's',chr(3),cmd,label,chr(3),))
			else:
				do_save = True
				del BDATA['labels'][e.target][label]
				self.add_mqueue(c,e.target,'Label removed.')
	if do_save:
		save_bdata(self)
		
def cmd_r_labelverify(self,c,e):
	global BDATA
	do_save = False
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	nick = e.source.nick.lower()
	host = BDATA['seen'][nick][0].split('@')[-1]
	if 'labels' not in BDATA:
		BDATA['labels'] = {}
	if e.target not in BDATA['labels']:
		BDATA['labels'][e.target] = {}
	ismod = None
	for label in BDATA['labels'][e.target]:
		if nick in BDATA['labels'][e.target][label]['mods']:
			if host == BDATA['labels'][e.target][label]['mods'][nick]:
				ismod = label
				break
			else:
				self.add_mqueue(c,e.target,'%s: You must auth with Q and set mode +x before using the .labelverify command.' % (e.source.nick,))
				return
	if not ismod:
		self.add_mqueue(c,e.target,'%s: This command is only available to label mods.' % (e.source.nick,))
		return
	if len(parms) > 2:
		self.add_mqueue(c,e.target,'Syntax: .%s [nick]' % (cmd,))
		return	
	nicks = []
	for lnick in BDATA['labels'][e.target][ismod]['nicks']:
		if not BDATA['labels'][e.target][ismod]['nicks'][lnick]:
			nicks.append(lnick)
	if len(parms) == 1:
		if len(nicks):
			self.add_mqueue(c,e.target,'%s pending label request%s: %s' % (len(nicks),'' if len(nicks) == 1 else 's',', '.join(nicks),))
		else:
			self.add_mqueue(c,e.target,'No pending label requests.')
		return
	vnick = parms[1].lower()
	if vnick not in nicks:
		self.add_mqueue(c,e.target,'Nick not found in pending label requests. Use the %s09.labelverify%s command to view requests.' % (chr(3),chr(3),))
		return
	BDATA['labels'][e.target][ismod]['nicks'][vnick] = True
	self.add_mqueue(c,e.target,'%s confirmed as %s' % (vnick,ismod,))
	save_bdata(self)	
				
def cmd_o_labelmod(self,c,e):
	global BDATA
	do_save = False
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if 'labels' not in BDATA:
		BDATA['labels'] = {}
	if e.target not in BDATA['labels']:
		BDATA['labels'][e.target] = {}
	if len(parms) < 4 or parms[1].lower() not in ('add','delete','del','rem','remove',):
		self.add_mqueue(c,e.target,'Syntax: .%s <add|del> <nick> <label name>' % (cmd,))
	elif parms[1].lower() == 'add':
		modnick = parms[2].lower()
		label = ' '.join(parms[3:]).lower()
		for each_label in BDATA['labels'][e.target]:			
			if modnick in BDATA['labels'][e.target][each_label]['mods']:
				self.add_mqueue(c,e.target,'%s is already a label mod for %s' % (modnick,each_label,))
				return
		if label not in BDATA['labels'][e.target]:
			self.add_mqueue(c,e.target,'Label does not exist.')
			return
		if not self.channels[e.target].has_user(modnick):
			self.add_mqueue(c,e.target,'%s is not in the channel.' % (modnick,))
			return
		host = BDATA['seen'][modnick][0].split('@')[-1]
		if '.users.quakenet.org' not in host:
			self.add_mqueue(c,e.target,'%s must auth with Q and set mode +x' % (modnick,))
		else:
			do_save = True
			BDATA['labels'][e.target][label]['mods'][modnick] = host
			self.add_mqueue(c,e.target,'Label mod added.')
	else:
		modnick = parms[2].lower()
		label = ' '.join(parms[3:]).lower()
		if label not in BDATA['labels'][e.target]:
			self.add_mqueue(c,e.target,'Label does not exist.')
		elif modnick not in BDATA['labels'][e.target][label]['mods']:
			self.add_mqueue(c,e.target,'Label mod does not exist.')
		else:
			do_save = True
			del BDATA['labels'][e.target][label]['mods'][modnick]
			self.add_mqueue(c,e.target,'Label mod removed.')
	if do_save:
		save_bdata(self)		

def cmd_10_addopener(self,c,e):
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

def cmd_r_openers(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	topcnt = 3 if len(BDATA['openers']) > 3 else len(BDATA['openers'])
	
	# BDATA['openers'][opener] = open_line,open_author,open_time,open_karma,open_hits+1
	sorted_openers = []
	for opener in BDATA['openers']:
		open_line,open_author,open_time,open_karma,open_hits = BDATA['openers'][opener]
		sorted_openers.append((len(open_karma),opener))
	sorted(sorted_openers)
	toplist = []
	for open_karma,opener in sorted_openers[0:topcnt]:
		toplist.append(opener)
	if 'openers' in BDATA:
		self.add_mqueue(c,e.target,'%s openers in database. Top %s: %s' % (len(BDATA['openers']),topcnt,', '.join(toplist),))
		
def cmd_r_allopeners(self,c,e):
	if 'openers' not in BDATA:
		BDATA['openers'] = {}
	if 'allopenerscache' in BDATA:
		oldcache,oldurl = BDATA['allopenerscache']
		newcache = dict_hash(self,BDATA['openers'])
		if newcache == oldcache:
			self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,oldurl,))
			return
	openkeys = BDATA['openers'].keys()
	openkeys.sort()
	if not self.pbkey:
		self.add_mqueue(c,e.target,'Pastebin API key not found.')
		return
	pbopeners = []
	for opener in openkeys:
		open_line,open_author,open_time,open_karma,open_hits = BDATA['openers'][opener]
		pbopeners.append('%s: %s' % (opener,open_line,))
	# pb go for launch
	try:
		pasteurl = self.pb.paste(
			self.botconfig['pb_devkey'],
			'\r\n'.join(pbopeners),
			api_user_key=self.pbkey,
			paste_name='.allopeners (%s entries)' % (len(openkeys),),
			paste_format='text',
			paste_private='unlisted',
			paste_expire_date='N'
		)
	except:
		pasteurl = None
	if pasteurl:
		self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,pasteurl,))
		if 'allopenerscache' in BDATA:
			oldcache,oldurl = BDATA['allopenerscache']
			paste_key = oldurl.split('/')[-1]
			try:
				result = self.pb.delete_paste(
					self.botconfig['pb_devkey'],
					self.pbkey,
					paste_key
				)
			except:
				pass
		BDATA['allopenerscache'] = (dict_hash(self,BDATA['openers']),pasteurl)
		save_bdata(self)			
	else:
		self.add_mqueue(c,e.target,'%s: Unable to post to pastebin.' % (e.source.nick,))

	
def cmd_r_allquotes(self,c,e):
	# open_line,open_author,open_time,open_karma,open_hits = BDATA['quotes'][opener]
	if 'quotes' not in BDATA:
		BDATA['quotes'] = {}
	if 'allquotescache' in BDATA:
		oldcache,oldurl = BDATA['allquotescache']
		newcache = dict_hash(self,BDATA['quotes'])
		if newcache == oldcache:
			self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,oldurl,))
			return
	openkeys = BDATA['quotes'].keys()
	openkeys.sort()
	if not self.pbkey:
		self.add_mqueue(c,e.target,'Pastebin API key not found.')
		return
	pbopeners = []
	for opener in openkeys:
		open_line,open_author,open_time,open_karma,open_hits = BDATA['quotes'][opener]
		pbopeners.append('%s: %s' % (opener,open_line,))
	# pb go for launch
	try:
		pasteurl = self.pb.paste(
			self.botconfig['pb_devkey'],
			'\r\n'.join(pbopeners),
			api_user_key=self.pbkey,
			paste_name='.allquotes (%s entries)' % (len(openkeys),),
			paste_format='text',
			paste_private='unlisted',
			paste_expire_date='N'
		)
	except:
		pasteurl = None
	if pasteurl:
		self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,pasteurl,))
		if 'allquotescache' in BDATA:
			oldcache,oldurl = BDATA['allquotescache']
			paste_key = oldurl.split('/')[-1]
			try:
				result = self.pb.delete_paste(
					self.botconfig['pb_devkey'],
					self.pbkey,
					paste_key
				)
			except:
				pass
		BDATA['allquotescache'] = (dict_hash(self,BDATA['openers']),pasteurl)
		save_bdata(self)			
	else:
		self.add_mqueue(c,e.target,'%s: Unable to post to pastebin.' % (e.source.nick,))

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
def kickban(self,c,e,target,bantime=-1,kickreason=None,tchan=None):
	tchan = e.target if not tchan else tchan
	tmask = BDATA['seen'][target][0] if 'seen' in BDATA and target in BDATA['seen'] else target
	tmask = tmask if len(tmask.split('!')) < 2 else '*!%s' % (tmask.split('!')[1],)
	if 'clients.kiwiirc.com' in tmask:
		tmask = '%s@*.clients.kiwiirc.com' % (tmask.split('@')[0],)
	BDATA['votebans'].append((tmask,self.tyme.time()+(bantime if bantime > 0 else 60*60*24*365*1000)))
	c.mode(tchan,'+b %s' % (tmask,))	
	if kickreason:
		c.kick(tchan,target,kickreason)

def cmd_o_kb(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 3 or not is_int(parms[2]):
		self.add_mqueue(c,e.target,'Syntax: .%s <nick> <minutes> [reason]' % (cmd,))
	else:
		target = parms[1].lower()
		if not self.channels[e.target].has_user(target):
			self.add_mqueue(c,e.target,'User not found.')
			return
		length = int(parms[2])
		reason = 'Banned for %s minute%s' % (length,'' if length == 1 else 's')
		if length < 1:
			reason = 'Banned FOREVER'
		if len(parms) >= 4:
			reason = '%s (%s)' % (' '.join(parms[3:]),reason)
		else:
			with open('kicks.txt') as f:
				kicklines = f.readlines()
			kick = self.rng.choice(kicklines)
			kick = kick.strip()
			kick = kick.replace('%k',target)
			kick = kick.replace('%u',e.source.nick)
			reason = '%s (%s)' % (kick,reason)
				
		kickban(self,c,e,target,bantime=length*60,kickreason=reason)
		
def cmd_b_kicktest(self,c,e):
	with open('kicks.txt') as f:
		kicklines = f.readlines()
		kick = self.rng.choice(kicklines)
		kick = kick.strip()
		kick = kick.replace('%k',e.source.nick)
		kick = kick.replace('%u',c.get_nickname())
		self.add_mqueue(c,e.target,'Random kick: %s' % (kick,))
		
def cmd_b_kbc(self,c,e):
	global BDATA	
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	tchan = e.target if len(parms) < 2 else parms[1]
	chan = e.source.nick if e.target == c.get_nickname() else e.target
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 4 or not is_int(parms[3]):
		self.add_mqueue(c,chan,'Syntax: .%s <chan> <nick> <minutes> [reason]' % (cmd,))
	else:
		target = parms[2].lower()
		length = int(parms[3])
		reason = 'Banned for %s minute%s' % (length,'' if length == 1 else 's')
		if length < 1:
			reason = 'Banned FOREVER'
		if len(parms) >= 5:
			reason = '%s (%s)' % (' '.join(parms[4:]),reason)
		kickban(self,c,e,target,bantime=length*60,kickreason=reason,tchan=tchan)

		
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
		kickban(self,c,e,target,bantime=length*60)
		self.add_mqueue(c,e.target,'%s: %s' % (target,reason))
		save_bdata(self)
		
def cmd_d_termsearch(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <term>' % (cmd,))
	else:
		for term in VOCAB.keys():
			if parms[1].lower() in term.lower():
				breakdown = []
				for char in term:
					breakdown.append(str(ord(char)))
				self.add_mqueue(c,e.target,'%s: %s' % (term,','.join(breakdown)))
				
	

def cmd_1_votekick(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	nick = e.source.nick.lower()
	do_save = False
	boss,oper,voiced = is_mod(self,c,e)
	if not oper and e.target != '#theredpill':
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
			#print('parms=%s' % (parms,))
			#print('votekick=%s' % (BDATA['votekick'],))
			if len(parms) > 1 and parms[1].lower() == BDATA['votekick'][e.target]['nick']:
				self.add_mqueue(c,e.target,'%s has been cancelled due to timeout.' % (cmd,))
				del BDATA['votekick'][e.target]
				do_save = True				
			else:
				self.add_mqueue(c,e.target,'There is no %s currently active. To nominate someone, type .%s <nick>' % (cmd,cmd))
		elif not self.channels[e.target].has_user(BDATA['votekick'][e.target]['nick']):
			self.add_mqueue(c,e.target,'%s has been cancelled; %s no longer present.' % (cmd,BDATA['votekick'][e.target]['nick'],))
			del BDATA['votekick'][e.target]
			do_save = True
		elif oper or BDATA['votekick'][e.target]['nick'] == nick:
			target = BDATA['votekick'][e.target]['nick']
			kickban(self,c,e,target,bantime=60*5,kickreason='Vote passed. Temp ban for 5 minutes.')
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
				kickban(self,c,e,target,bantime=60*5,kickreason='The tribe has spoken. Temp ban for 5 minutes')
				del BDATA['votekick'][e.target]
			else:
				BDATA['votekick'][e.target]['time'] = self.tyme.time()
				self.add_mqueue(c,e.target,'Vote registered. %d more vote%s needed.' % (vote_req-vote_cnt,'' if vote_req-vote_cnt == 1 else 's',))
	elif BDATA['votekick'][e.target]['time'] >= self.tyme.time() - (60*5):
		ago = time_ago((60*5)-(self.tyme.time()-BDATA['votekick'][e.target]['time']))
		nik = BDATA['votekick'][e.target]['nick']
		self.add_mqueue(c,e.target,'The current %s for %s has %s remaining. Please wait for the current vote to finish before starting another.' % (cmd,nik,ago,))
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
			kickban(self,c,e,target,bantime=60*5,kickreason='Vote passed. Temp ban for 5 minutes.')
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
				self.add_mqueue(c,e.target,'A %s has been initiated. Type %s09,01.votekick%s to cast your vote for kicking %s. %s' % (cmd,chr(3),chr(3),target,needed,))
				do_save = True
			else:
				self.add_mqueue(c,e.target,'Not enough active users to initiate a %s.' % (cmd,))
		else:
			self.add_mqueue(c,e.target,'I pooped my pants.')
	if do_save:
		save_bdata(self)
		
def cmd_1_voteban(self,c,e):
	cmd_1_votekick(self,c,e)
		
def cmd_100_votekarma(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	nick = e.source.nick.lower()
	do_save = False
	boss,oper,voiced = is_mod(self,c,e)
	if 'votekarma' not in BDATA:
		BDATA['votekarma'] = {}
	if e.target not in BDATA['votekarma']:
		BDATA['votekarma'][e.target] = {
			'nick':'',
			'time':0,
			'amount':0,
			'votes':[],
		}
		do_save = True	
	if len(parms) < 2 or parms[1].lower() == BDATA['votekarma'][e.target]['nick']:
		if BDATA['votekarma'][e.target]['time'] < self.tyme.time() - (60*5):
			#print('parms=%s' % (parms,))
			#print('votekarma=%s' % (BDATA['votekarma'],))
			if len(parms) > 1 and parms[1].lower() == BDATA['votekarma'][e.target]['nick']:
				self.add_mqueue(c,e.target,'votekarma has been cancelled due to timeout.')
				del BDATA['votekarma'][e.target]
				do_save = True				
			else:
				self.add_mqueue(c,e.target,'There is no votekarma currently active. To nominate someone, type .votekarma <nick>')
		elif not self.channels[e.target].has_user(BDATA['votekarma'][e.target]['nick']):
			self.add_mqueue(c,e.target,'votekarma has been cancelled; %s no longer present.' % (BDATA['votekarma'][e.target]['nick'],))
			del BDATA['votekarma'][e.target]
			do_save = True
		elif oper or BDATA['votekarma'][e.target]['nick'] == nick:
			target = BDATA['votekarma'][e.target]['nick']
			#kickban(self,c,e,target,bantime=60*5,kickreason='Vote passed. Temp ban for 5 minutes.')
			del BDATA['votekarma'][e.target]
			if target not in BDATA['karma']:
				BDATA['karma'][target] = KARMA_DEFAULT.copy()
			BDATA['karma'][target]['count'] -= 1
			self.add_mqueue(c,e.target,'Vote passed. 1 karma taken from %s.' % (target,))
			do_save = True
		elif e.source.nick not in BDATA['votekarma'][e.target]['users']:
			self.add_mqueue(c,e.target,'Invalid voter registration ID.')
		elif nick not in BDATA['votekarma'][e.target]['votes']:
			do_save = True
			BDATA['votekarma'][e.target]['votes'].append(nick)
			vote_cnt = len(BDATA['votekarma'][e.target]['votes'])
			vote_req = BDATA['votekarma'][e.target]['amount']
			if vote_cnt >= vote_req:
				target = BDATA['votekarma'][e.target]['nick']
				#kickban(self,c,e,target,bantime=60*5,kickreason='The tribe has spoken. Temp ban for 5 minutes')
				del BDATA['votekarma'][e.target]
				if target not in BDATA['karma']:
					BDATA['karma'][target] = KARMA_DEFAULT.copy()
				BDATA['karma'][target]['count'] -= 1
				self.add_mqueue(c,e.target,'Vote passed. 1 karma taken from %s.' % (target,))
			else:
				BDATA['votekarma'][e.target]['time'] = self.tyme.time()
				self.add_mqueue(c,e.target,'Vote registered. %d more vote%s needed.' % (vote_req-vote_cnt,'' if vote_req-vote_cnt == 1 else 's',))
	elif BDATA['votekarma'][e.target]['time'] >= self.tyme.time() - (60*5):
		ago = time_ago((60*5)-(self.tyme.time()-BDATA['votekarma'][e.target]['time']))
		nik = BDATA['votekarma'][e.target]['nick']
		self.add_mqueue(c,e.target,'The current votekarma for %s has %s remaining. Please wait for the current vote to finish before starting another.' % (nik,ago,))
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
			kickban(self,c,e,target,bantime=60*5,kickreason='Vote passed. Temp ban for 5 minutes.')
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
				BDATA['votekarma'][e.target] = {
					'nick':target,
					'time':self.tyme.time(),
					'amount':amount,
					'votes':[nick,],
					'users':self.channels[e.target].users(),
				}
				needed = '%d vote%s %s needed.' % (amount-1,'' if amount-1 == 1 else 's','is' if amount-1==1 else 'are')
				self.add_mqueue(c,e.target,'A votekarma has been initiated. Type %s09,01.votekarma%s to cast your vote for kicking %s. %s' % (chr(3),chr(3),target,needed,))
				do_save = True
			else:
				self.add_mqueue(c,e.target,'Not enough active users to initiate a votekarma.')
		else:
			self.add_mqueue(c,e.target,'I pooped my pants.')
	if do_save:
		save_bdata(self)
					
'''
def cmd_d_mask(self,c,e):
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
		self.add_mqueue(c,e.target,'. '.join(report)
'''

def cmd_1_activity(self,c,e):
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
					
def cmd_5_lmgtfy(self,c,e):
	# urllib.urlencode({'q':'something something?!'})
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 2:
		self.add_mqueue(c,e.target,'Syntax: .%s [nick] <search term>' % (cmd,))
		return
	target = parms[1].lower()
	if not self.channels[e.target].has_user(target):
		search = 'http://lmgtfy.com/?%s' % (self.urllib.urlencode({'q':' '.join(parms[1:])}),)
		self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,search,))
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
	
def cmd_b_fixranks(self,c,e):
	global BDATA
	BDATA['rankscache'] = {}
	save_bdata(self)		
	
'''
		
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
def cmd_d_hex2ip(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) != 2 or len(parms[1]) != 8:
		self.add_mqueue(c,e.target,'Syntax: .%s <8-digit hex>' % (cmd,))
		return
	try:
		int(parms[1],16)
	except ValueError:
		self.add_mqueue(c,e.target,'Invalid hex.')
		return		
	intip = []
	for slot in range(4):
		intip.append(str(int(parms[1][slot*2:(slot*2)+2],16)))
	ip2resolve = '.'.join(intip)
	uprint('resolving %s' % (ip2resolve,))	
	try:
		dns = self.socket.gethostbyaddr(ip2resolve)
	except self.socket.gaierror:
		dns = None
	except TypeError:
		dns = None
	except self.socket.herror:
		dns = None
	if dns and len(dns) == 3:
		self.add_mqueue(c,e.target,'%s: %s (%s)' % (e.source.nick,ip2resolve,dns[0],))
	else:
		self.add_mqueue(c,e.target,'%s: %s (dns lookup failed)' % (e.source.nick,ip2resolve,))
	

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
	global BDATA
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
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	chan = e.target if len(parms) != 2 else parms[1]
	if 'ranks' not in BDATA or chan not in BDATA['ranks'] or len(BDATA['ranks'][chan]) < 1:
		self.add_mqueue(c,e.target,'There are no ranks.')
		return
	if 'rankscache' in BDATA and chan in BDATA['rankscache']:
		oldcache,oldurl = BDATA['rankscache'][chan]
		newcache = dict_hash(self,BDATA['ranks'][chan])
		if newcache == oldcache:
			self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,oldurl,))
			return
	if not self.pbkey:
		self.add_mqueue(c,e.target,'Pastebin API key not found.')
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
	rankkeys = BDATA['ranks'][chan].keys()
	rankkeys.sort()
	pbranks = []
	for rank in rankkeys:
		pbranks.append('Rank %s: %s' % (rank,BDATA['ranks'][chan][rank],))
	# pb go for launch
	try:
		pasteurl = self.pb.paste(
			self.botconfig['pb_devkey'],
			'\r\n'.join(pbranks),
			api_user_key=self.pbkey,
			paste_name='%s .ranks (%s ranks)' % (chan,len(rankkeys),),
			paste_format='text',
			paste_private='unlisted',
			paste_expire_date='N'
		)
	except:
		pasteurl = None
	if pasteurl:
		self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,pasteurl,))
		if 'rankscache' in BDATA and chan in BDATA['rankscache']:
			oldcache,oldurl = BDATA['rankscache'][chan]
			paste_key = oldurl.split('/')[-1]
			try:
				result = self.pb.delete_paste(
					self.botconfig['pb_devkey'],
					self.pbkey,
					paste_key
				)
			except:
				pass
		if 'rankscache' not in BDATA:
			BDATA['rankscache'] = {}
		BDATA['rankscache'][chan] = (dict_hash(self,BDATA['ranks'][chan]),pasteurl)
		save_bdata(self)			
	else:
		self.add_mqueue(c,e.target,'%s: Unable to post to pastebin.' % (e.source.nick,))

		
'''
def cmd_b_rankdebug(self,c,e):
	if e.target not in BDATA['ranks']:
		BDATA['ranks'][e.target] = {}
	self.add_mqueue(c,e.source.nick,'%s' % (BDATA['ranks'][e.target].keys(),))
'''


def cmd_b_save(self,c,e):
	save_bdata(self,force=True)
	self.add_mqueue(c,e.target,'data saved.')
	
def cmd_b_nick(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) != 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <nick>' % (cmd,))
		return
	c.nick(parms[1])	
	
def cmd_d_setkarma(self,c,e):
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
	#if not self.channels[e.target].has_user(target):
	#	self.add_mqueue(c,e.target,'That user is not in the channel.')
	#	return
	if target not in BDATA['karma']:
		BDATA['karma'][target] = KARMA_DEFAULT.copy()
	BDATA['karma'][target]['count'] = amnt
	self.add_mqueue(c,e.target,'karma set.')
	save_bdata(self)
	
def cmd_b_refreshkarma(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) != 2:
		self.add_mqueue(c,e.target,'Syntax: .%s <nick>' % (cmd,))
		return
	target = parms[1].lower()
	if 'karma' not in BDATA or target not in BDATA['karma']:
		self.add_mqueue(c,e.target,'%s not in karma database.' % (target,))
		return
	BDATA['karma'][target]['next'] = 0
	save_bdata(self)
	self.add_mqueue(c,e.target,'karma cooldown refreshed for %s.' % (target,))
	
def cmd_d_karmasearch(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	me = e.source.nick.lower()
	target = me if len(parms) == 1 else parms[1]
	if 'karma' not in BDATA:
		self.add_mqueue(c,e.target,'No karma entries in BDATA.')
		return
	for eachkarma in BDATA['karma']:
		if target.lower() in eachkarma.lower():
			self.add_mqueue(c,e.target,'Match: %s => %s' % (eachkarma,BDATA['karma'][eachkarma],))
			
def cmd_b_karmafix(self,c,e):
	if 'karma' not in BDATA:
		self.add_mqueue(c,e.target,'No karma entries in BDATA.')
		return
	fixthese = BDATA['karma'].copy()
	for eachkarma in BDATA['karma']:
		status = []
		if eachkarma != eachkarma.lower():
			status.append('%s => %s' % (eachkarma,eachkarma.lower()))
			if eachkarma.lower() in BDATA['karma']:
				status.append('Conflicting karma found, combining both entries')
				fixthese[eachkarma.lower()]['count'] = fixthese[eachkarma]['count']+fixthese[eachkarma.lower()]['count']
			del fixthese[eachkarma]
		if len(status):
			self.add_mqueue(c,e.target,'. '.join(status))
	
	BDATA['karma'] = fixthese
	save_bdata(self)
	self.add_mqueue(c,e.target,'Repair complete?')
	
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
					try:
						frank = ' (Rank: %s)' % (BDATA['ranks'][e.target][rank],)
					except KeyError:
						frank = ' (Rank: %s)' % (BDATA['ranks'][e.target][int(rank)],)
				else:
					break
	if len(parms) == 1 or target == me:
		self.add_mqueue(c,e.target,'%s, you have %s karma.%s' % (e.source.nick,'no' if amnt == 0 else amnt,frank))
	elif target == c.get_nickname().lower():
		self.add_mqueue(c,e.target,'I have all the karma. (Rank: Karma Chameleon)')
	else:
		self.add_mqueue(c,e.target,'%s has %s karma.%s' % (target,'no' if amnt == 0 else amnt,frank))
		
def cmd_b_ignore(self,c,e):
	#BDATA['mods'] = []
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	chan = e.source.nick if e.target == c.get_nickname() else e.target
	if len(parms) == 1 or len(parms) != 3:
		if 'ignore' in BDATA and len(BDATA['ignore']) and len(parms) == 1:
			self.add_mqueue(c,chan,'%s being ignored: %s' % (len(BDATA['ignore']),', '.join(BDATA['ignore']),))
		else:
			self.add_mqueue(c,chan,'Syntax: %s [<add/del> <nick/pattern>]' % (cmd,))
	elif parms[1].lower() == 'add':
		target = parms[2].lower()
		if 'ignore' not in BDATA:
			BDATA['ignore'] = []
		if self.fnmatch(e.source.nick.lower(),target):
			self.add_mqueue(c,chan,'Cannot add yourself to ignore list.')
		elif target not in BDATA['ignore']:
			BDATA['ignore'].append(target)
			save_bdata(self)
			self.add_mqueue(c,chan,'%s added to ignore list.' % (target,))
		else:
			self.add_mqueue(c,chan,'%s is already being ignored.' % (target,))
	elif parms[1].lower() in ('del','remove','delete','rem','kill'):
		target = parms[2].lower()
		if 'ignore' not in BDATA or target not in BDATA['ignore']:
			self.add_mqueue(c,chan,'%s is not ignored.' % (target,))
		else:
			BDATA['ignore'].remove(target)
			save_bdata(self)
			self.add_mqueue(c,chan,'%s removed from ignore list.' % (target,))
		
def cmd_b_devs(self,c,e):
	#BDATA['mods'] = []
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()	
	if len(parms) == 1 or len(parms) != 3:
		if 'devs' in BDATA and len(BDATA['devs']) and len(parms) == 1:
			self.add_mqueue(c,e.target,'%s devs: %s' % (len(BDATA['devs']),', '.join(BDATA['devs']),))
		else:
			self.add_mqueue(c,e.target,'Syntax: %s [<add/del> <nick>]' % (cmd,))
	elif parms[1].lower() == 'add':
		target = parms[2].lower()
		if 'devs' not in BDATA:
			BDATA['devs'] = []
		if target not in BDATA['devs']:
			BDATA['devs'].append(target)
			save_bdata(self)
			self.add_mqueue(c,e.target,'%s added to dev list.' % (target,))
		else:
			self.add_mqueue(c,e.target,'%s is already a dev.' % (target,))
	elif parms[1].lower() in ('del','remove','delete','rem','kill'):
		target = parms[2].lower()
		if 'devs' not in BDATA or target not in BDATA['devs']:
			self.add_mqueue(c,e.target,'%s is not a dev.' % (target,))
		else:
			BDATA['devs'].remove(target)
			save_bdata(self)
			self.add_mqueue(c,e.target,'%s removed from dev list.' % (target,))
		
def cmd_v_mods(self,c,e):
	self.add_mqueue(c,e.target,'%s %s mods: %s' % (e.target,len(BDATA['mods'][e.target]),', '.join(BDATA['mods'][e.target])))
	
def cmd_o_addmod(self,c,e):
	#BDATA['mods'] = []
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()	
	if len(msg.split(' ')) != 2:
		self.add_mqueue(c,e.target,'Syntax: %s <nick>' % (cmd,))
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
		
def cmd_v_watchfor(self,c,e):
	global BDATA
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	nick = e.source.nick.lower()
	if 'watchfor' not in BDATA:
		BDATA['watchfor'] = {}
	if nick not in BDATA['watchfor']:
		BDATA['watchfor'][nick] = []
	if len(parms) == 1:
		if not len(BDATA['watchfor'][nick]):
			self.add_mqueue(c,e.target,'%s: You have no watchfor entries. To add one, say %s09.%s add <hostmask>%s' % (e.source.nick,chr(3),cmd,chr(3),))
		else:		
			self.add_mqueue(c,e.target,'%s: %s entr%s: %s' % (e.source.nick,len(BDATA['watchfor'][nick]),'y' if len(BDATA['watchfor'][nick]) == 1 else 'ies',', '.join(BDATA['watchfor'][nick]),))
	elif len(parms) != 3 or parms[1].lower() not in ('add','del','delete','rem','remove'):
		self.add_mqueue(c,e.target,'Syntax: %s [add|del <hostmask>]' % (cmd,))
	else:
		dosave = False
		if parms[1].lower() == 'add':
			host = parms[2].lower()
			taken = None
			for mask in BDATA['watchfor'][nick]:
				if self.fnmatch(host,mask) or self.fnmatch(mask,host):
					taken = mask
					break
			if taken:
				self.add_mqueue(c,e.target,'%s already matches existing entry "%s"' % (host,taken))
				return
			BDATA['watchfor'][nick].append(host)
			self.add_mqueue(c,e.target,'watchfor entry added. To delete this entry, use the command %s09.%s del %s%s' % (chr(3),cmd,host,chr(3),))
			dosave = True
		else:
			host = parms[2].lower()
			if host not in BDATA['watchfor'][nick]:
				self.add_mqueue(c,e.target,'watchfor entry not found. To view your entries, use the command %s09.%s%s' % (chr(3),cmd,chr(3),))
				return
			BDATA['watchfor'][nick].remove(host)
			self.add_mqueue(c,e.target,'watchfor entry deleted.')
			dosave = True
		if dosave:
			save_bdata(self)
		
def cmd_b_mode(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) < 3:
		self.add_mqueue(c,e.target,'Syntax: %s <target> <mode>' % (cmd,))
	else:
		c.mode(parms[1],' '.join(parms[2:]))
		
def cmd_1_tell(self,c,e):
	msg = e.arguments[0].strip()
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) < 3:
		self.add_mqueue(c,e.target,'Syntax: %s <target[<chan>]> <term>' % (cmd,))
	else:
		target = msg.split(' ')[1]
		chan = e.target
		if len(target.split('#')) == 2:
			target,chan = target.split('#')
			chan = '#%s' % (chan,)
		if not self.channels[chan].has_user(target):
			self.add_mqueue(c,e.target,'That user is not in the channel.')
		else:
			term = msg.split(' ')[2].lower()		
			if term not in VOCAB:
				self.add_mqueue(c,e.target,'Term does not exist. Use .addterm to add new terms.')
			else:
				oterm = term_macro(self,term,target)
				voc_add(self,e.source.nick,term)
				self.add_mqueue(c,chan,'%s, %s: %s' % (target,term,oterm))
		
def on_join(self,c,e):
	nick = e.source.nick
	if nick != c.get_nickname():
		last_seen(self,c,e,nick,e.source,self.tyme.time(),'join',e.target)
		if e.target == '#theredpill':
			found = find_host(self,nick)
			clones = fetch_clones(self,c,e,nick.lower(),1)
			if 'clients.kiwiirc.com' in found[0] or len(clones) > 1:
				cloneinfo = '%s clones detected.' % (len(clones),) if len(clones) > 1 else ''					
				self.add_mqueue(c,'#trpbot','%s joined #theredpill (%s). %s' % (nick,found[-1],cloneinfo,))
			#else:
			#	self.add_mqueue(c,'#trpbot','%s joined #theredpill (%s) with no historical matches.' % (nick,found[-1]))
		if 'watchfor' in BDATA:
			for wnick in BDATA['watchfor']:
				for mask in BDATA['watchfor'][wnick]:
					if self.fnmatch(e.source,mask):
						found = find_host(self,nick)
						clones = fetch_clones(self,c,e,nick.lower(),1)
						cloneinfo = ' %s clones detected.' % (len(clones),) if len(clones) > 1 else ''					
						self.add_mqueue(c,wnick,'%s (matching %s) joined %s.%s' % (nick,mask,e.target,cloneinfo,))
		# a.clients.kiwiirc.com
		if e.source.host == 'a.clients.kiwiirc.com':
			self.add_mqueue(c,nick,"You are connecting from an unstable web client. Use https://tinyurl.com/TRPirc or https://www.irccloud.com/ to avoid random disconnections. This is an automated message.")
			uprint('Sent a.client.kiwiirc.com warning to %s.' % (nick,))
		# You are connecting from an unstable web client. Use https://tinyurl.com/TRPirc or https://www.irccloud.com/ to avoid random disconnections. This is an automated message.
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
	global BDATA
	#self.channels[e.target].has_user(BDATA['votekick'][e.target]['nick']
	do_save = False
	before,after = e.source.nick.lower(),e.target.lower()
	if 'karma' in BDATA and before in BDATA['karma'] and after in BDATA['karma']:
		if BDATA['karma'][before]['next'] >= BDATA['karma'][after]['next']:
			BDATA['karma'][after]['next'] = BDATA['karma'][before]['next']
			do_save = True
	if before.lower() in self.cbots:
		self.cbots[after.lower()] = self.cbots[before.lower()]
		del self.cbots[before.lower()]
	for cname in self.channels:
		ch = self.channels[cname]
		if 'votekick' in BDATA and cname in BDATA['votekick'] and BDATA['votekick'][cname]['nick'] == before.lower():
			BDATA['votekick'][cname]['nick'] = after.lower()
			do_save = True
	if do_save:
		save_bdata(self)
	
def on_quit(self,c,e):
	nick = e.source.nick
	if nick != c.get_nickname():
		last_seen(self,c,e,nick,e.source,self.tyme.time(),'quit',e.arguments[0])

def on_endofnames(self,c,e):
	chan = e.arguments[0]
	for each_nick in self.channels[chan].users():
		nick_mask = each_nick if 'seen' not in BDATA or each_nick.lower() not in BDATA['seen'] else BDATA['seen'][each_nick.lower()][0]
		last_seen(self,c,e,each_nick,nick_mask,self.tyme.time(),'idle',chan)
	
def cmd_d_boss(self,c,e):
	self.add_mqueue(c,e.target,'Boss: %s' % self.boss)

def cmd_d_join(self,c,e):
	msg = e.arguments[0].strip()
	cmd = msg.split(' ')[0].replace('.','').lower()
	if len(msg.split(' ')) != 2:
		self.add_mqueue(c,e.target,'Syntax: %s <channel>' % (cmd,))
	else:
		joinchan = msg.split(' ')[1]
		self.add_mqueue(c,e.target,'Attempting to join %s...' % (joinchan,))
		c.join(joinchan)
		
		
def cmd_d_part(self,c,e):
	if (e.target != self.channel and e.target not in self.AUTOJOIN):
		c.part(e.target)
	else:
		self.add_mqueue(c,e.target,"Not allowed to leave %s." % (e.target,))

def cmd_15_addterm(self,c,e):
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
			
def cmd_d_modterm(self,c,e):
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
			
			
def cmd_d_delterm(self,c,e):
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
			
def cmd_d_termraw(self,c,e):
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
			
def cmd_b_termowner(self,c,e):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	if len(parms) != 3:
		self.add_mqueue(c,e.target,'Syntax: %s <term> <nick>' % (cmd,))
		return
	term = parms[1].lower()
	nick = parms[2].lower()
	if term not in BDATA['vhistory']:
		self.add_mqueue(c,e.target,'Term does not exist.')
		return
	add_nick,add_time,req_count,mod_nick,mod_time,mod_count,del_nick,del_time = BDATA['vhistory'][term]
	BDATA['vhistory'][term] = nick,add_time,req_count,mod_nick,mod_time,mod_count,del_nick,del_time
	save_bdata(self)
	self.add_mqueue(c,e.target,'Term owner updated.')
	
			
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
	
def cmd_r_allterms(self,c,e,full=False):
	msg = e.arguments[0].strip()
	parms = msg.split(' ')
	cmd = parms[0].replace('.','').lower()
	cachename = 'alltermscache' if not full else 'fulltermcache'
	if not len(VOCAB):
		self.add_mqueue(c,e.target,'There are no existing terms. Use .addterm to add new terms.')
		return
	if cachename in BDATA:
		oldcache,oldurl = BDATA[cachename]
		newcache = dict_hash(self,VOCAB)
		if newcache == oldcache:
			self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,oldurl,))
			return
	terms = []
	for term in VOCAB.keys():
		terms.append(term)
	terms.sort()
	if self.pbkey:
		pbterms = []
		for term in terms:
			info = term
			if full:
				info = u'%s: %s' % (info,term_macro(self,term,'you'),)
				#info = '%s [%s hits][Added by %s (%s ago)]' % (info,req_count,add_nick,time_ago(self.tyme.time()-add_time),)
				#if mod_count:
				#	info = '%s[%s edits][Last edit %s ago by %s]' % (info,mod_count,time_ago(self.tyme.time()-mod_time),mod_nick,)
			if 'vhistory' in BDATA and term in BDATA['vhistory']:
				add_nick,add_time,req_count,mod_nick,mod_time,mod_count,del_nick,del_time = BDATA['vhistory'][term]
				# time_ago(s)
			pbterms.append(info)
		# pb go for launch
		try:
			pasteurl = self.pb.paste(
				self.botconfig['pb_devkey'],
				u'\r\n'.join(pbterms).encode('utf-8'),
				api_user_key=self.pbkey,
				paste_name='.allterms (%s entries)' % (len(VOCAB.keys()),),
				paste_format='text',
				paste_private='unlisted',
				paste_expire_date='N'
			)
		except:
			pasteurl = None
		if pasteurl:
			self.add_mqueue(c,e.target,'%s: %s' % (e.source.nick,pasteurl,))
			if cachename in BDATA:
				oldcache,oldurl = BDATA[cachename]
				paste_key = oldurl.split('/')[-1]
				try:
					result = self.pb.delete_paste(
						self.botconfig['pb_devkey'],
						self.pbkey,
						paste_key
					)
				except:
					pass
			BDATA[cachename] = (dict_hash(self,VOCAB),pasteurl)
			save_bdata(self)
		else:
			self.add_mqueue(c,e.target,'%s: Unable to post to pastebin.' % (e.source.nick,))
		return
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
		
def cmd_r_alltermsfull(self,c,e):
	cmd_r_allterms(self,c,e,full=True)
	
def cmd_r_help(self,c,e):
	me = e.source.nick.lower()
	karma = 0 if me not in BDATA['karma'] else BDATA['karma'][me]['count']	
	boss,oper,voiced = is_mod(self,c,e)
	dev = is_dev(self,c,e)
	cmds = []
	for cmd in self.chatcmds.keys():
		if 'cmd_d_' in cmd and dev:
			cmds.append(cmd.replace('cmd_d_','*'))
		elif 'cmd_b_' in cmd and boss:
			cmds.append(cmd.replace('cmd_b_','$'))
		elif 'cmd_o_' in cmd and oper:
			cmds.append(cmd.replace('cmd_o_','@'))
		elif 'cmd_v_' in cmd and voiced:
			cmds.append(cmd.replace('cmd_v_','+'))
		elif 'cmd_r_' in cmd:
			cmds.append(cmd.replace('cmd_r_',''))
		elif 'cmd_' in cmd and is_int(cmd.split('_')[1]) and int(cmd.split('_')[1]) <= karma:
			cmds.append('^'+cmd.split('_')[2])
			
	cmds.sort()	
	self.add_mqueue(c,e.target,'Commands: %s' % (', '.join(cmds),))
	
