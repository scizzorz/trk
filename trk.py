#!/usr/bin/env python
import sys, os, getopt, md5, re, time, tempfile
from os.path import expanduser

# configuration
# hopefully all of these will be ported to a .trkrc
# and have command-line flags as well
CONFIG=dict()

# the configuration file
# this can't really be changed in a config file,
# but it can be changed by a flag
CONFIG['config']="%s/%s" % (expanduser("~"),".trkrc")

# which file to use
CONFIG['file']='.todo'

# size of the md5 sum substring used as the task id
CONFIG['id_size']=4

# highlighting on
CONFIG['hi_style']='xterm'

# highlight colors (ANSI palette) used to highlight each part of a task
CONFIG['hi_id']=7
CONFIG['hi_project']=11
CONFIG['hi_context']=10
CONFIG['hi_priority']=9
CONFIG['hi_due']=14
CONFIG['hi_overdue']=9
CONFIG['hi_count']=7

# which character to use for priority
CONFIG['priority_char']='!'

# which editor to use to edit tasks
CONFIG['editor']='vim'

# show tasks count at the end or not?
CONFIG['show_count']=True

# what character to use for indents
# how the heck do you change this in
# a config file...
CONFIG['indent']='   '

# debating use
CONFIG['writecmd']=''
CONFIG['editcmd']=''
CONFIG['markcmd']=''


# state tracking
STATE=dict()
STATE['indent']=0


# formatting dictionary
LOCALE=dict()
LOCALE['ioerror']="Unable to open file '%s' for %s"
LOCALE['marked'] = 'Marked as done: %s'
LOCALE['deleted'] = 'Deleted: %s'
LOCALE['saved'] = 'Saved new item: %s'
LOCALE['added'] = 'Added new item: %s'
LOCALE['numlines'] = '%s items'
LOCALE['numlines_single'] = '%s item'
LOCALE['label'] = '%s %s items'
LOCALE['label_single'] = '%s %s item'
LOCALE['everything'] = 'everything else'

# command alias dictionary
ALIAS=dict()
ALIAS['add'] = ('add','a')
ALIAS['edit'] = ('edit','ed','e')
ALIAS['edit_body'] = ('editsearch','edits','esearch','ese','es')
ALIAS['mark'] = ('finish','complete','done','hide','x')
ALIAS['mark_body'] = ('xsearch','xse','xs')

ALIAS['projects'] = ('projects','proj','prj','+')
ALIAS['contexts'] = ('contexts','cont','ctx','@')
ALIAS['list'] = ('all','list','ls')
ALIAS['search'] = ('search','find','se','fi','s','f')
ALIAS['regex'] = ('regex','re')
ALIAS['xregex'] = ('xregex','xre')
ALIAS['eval'] = ('eval','ev')

# RegExes used to highlight colors
RE_PROJECT=re.compile(r'(^|\s)(\+[\w\+]+)')
RE_CONTEXT=re.compile(r'(^|\s)(\@[\w\@]+)')
RE_PRIORITY=re.compile(r'\s*(\((\d)\))\s*')
RE_DUE=re.compile(r'(\[(\d{1,2})/(\d{1,2})(/(\d{2,4}))*([@ ](\d{1,2})(:(\d{1,2}))*(am|pm)*)*\])')
RE_WHITESPACE=re.compile(r'\s+')

RE_SETTING=re.compile(r'(\w+)\s*\=\s*(.*)')

def dateToUnix(datestring):
	match = RE_DUE.search(datestring)

	# convert match into a sortable Unix time
	if match != None:
		month=match.group(2)
		day=match.group(3)

		year=match.group(5) or time.strftime("%Y",time.gmtime())
		if len(year)==3:
			year=time.strftime("%Y",time.gmtime())
		elif len(year)==2:
			year="20"+year

		hour=match.group(7) or "12"
		minute=match.group(9) or "00"

		pam = match.group(10) or 'am'
		pam = pam.upper()

		unix = time.mktime(time.strptime("%s %s %s %s %s %s" % (month,day,year,hour,minute,pam),"%m %d %Y %I %M %p"))
	else:
		unix = None

	return unix

def linecmp(a,b):
	# these look backwards to me but they work...
	# if a > b, return -
	# if a < b, return +
	# if a = b, return 0

	# priority
	priorityMatchA = RE_PRIORITY.search(a)
	priorityMatchB = RE_PRIORITY.search(b)
	if priorityMatchA == None and priorityMatchB != None:
		return 1
	elif priorityMatchA != None and priorityMatchB == None:
		return -1
	elif priorityMatchA != None and priorityMatchB != None:
		ret=int(priorityMatchB.group(2)) - int(priorityMatchA.group(2))
		if ret!=0:
			return ret


	# dates
	timeA = dateToUnix(a)
	timeB = dateToUnix(b)

	# sort dateMatches
	if timeA == None and timeB != None:
		return 1
	elif timeA != None and timeB == None:
		return -1
	elif timeA != None and timeB != None:
		ret=timeB - timeA
		if ret!=0:
			return -ret/abs(ret)


	# string order
	return cmp(a,b)

# sorting key class
class K(object):
	def __init__(self,obj,*args):
		self.obj=obj
	def __lt__(self,other):
		return linecmp(self.obj,other.obj) < 0
	def __gt__(self,other):
		return linecmp(self.obj,other.obj) > 0
	def __eq__(self,other):
		return linecmp(self.obj,other.obj) == 0
	def __le__(self,other):
		return linecmp(self.obj,other.obj) <= 0
	def __ge__(self,other):
		return linecmp(self.obj,other.obj) >= 0
	def __ne__(self,other):
		return linecmp(self.obj,other.obj) != 0

# computes the md5 task id of a line
def lineid(line):
	line=line.strip()
	return md5.new(line).hexdigest()[0:int(CONFIG['id_size'])]

# highlights a string with the given color
def hi(string,color):
	color = int(color)

	# conky highlighting
	if CONFIG['hi_style']=='conky':
		return "${color%d}%s${color}" % (color%10,string)

	# xterm highlighting
	elif CONFIG['hi_style']=='xterm':
		if color<8:
			return "\033[%dm%s\033[0m" % (color+30,string)
		else:
			return "\033[%dm%s\033[0m" % (color+82,string)

	# none
	else:
		return string

def formatDate(obj):
	ret = '%s/%s' % (obj.group(2),obj.group(3))
	if obj.group(5)!=None: # year
		ret += '/'+obj.group(5)

	if obj.group(7)!=None: # hour / time
		ret += ' '+obj.group(7)
		if obj.group(8)!=None: # minutes
			ret += obj.group(8)
		if obj.group(10)!=None: # am/pm
			ret += obj.group(10)

	if dateToUnix('['+ret+']') < time.time():
		return hi(ret, CONFIG['hi_overdue'])
	else:
		return hi(ret, CONFIG['hi_due'])

# format a line for printing
def formatLine(line, preid=None, show_id=True):
	line=line.strip()
	preColorLine=line

	# priority
	matchPriority=RE_PRIORITY.search(line)
	if matchPriority!=None:
		priority=hi(CONFIG['priority_char'] * int(matchPriority.group(2)),CONFIG['hi_priority'])+' '
	else:
		priority=''

	# strip duplicate whitespace (HTML DOES IT WHY CAN'T I)
	line=RE_WHITESPACE.sub(' ',line)

	# highlighting subs
	line=RE_PROJECT.sub(r'\1'+hi(r'\2',CONFIG['hi_project']),line)
	line=RE_CONTEXT.sub(r'\1'+hi(r'\2',CONFIG['hi_context']),line)
	line=RE_PRIORITY.sub('',line)
	line=RE_DUE.sub(formatDate,line)

	# print them with priority
	line=priority+line.strip()

	if show_id:
		if preid==None:
			preid=lineid(preColorLine)
		return "%s%s %s" % (STATE['indent']*CONFIG['indent'],hi(preid,CONFIG['hi_id']),line)
	else:
		return "%s%s" % (STATE['indent']*CONFIG['indent'],line)

# eval shortcuts
def eval_s(line,match=''):
	return match in line
def eval_r(line,match=''):
	return re.search(match,line)!=None
def eval_x(line,match=''):
	return re.search(match,line)==None

# read the file and return a list of sorted lines
def readFile(filename):
	try:
		temp = open(filename, 'r+')
	except IOError:
		print LOCALE['ioerror'] % (filename, 'reading')
		return None
	else:
		lines = [line for line in temp if line.strip()]
		lines.sort(key=K)
		temp.close()
		return lines

# read tasks
def readLines(filename, match='',regex=None):
	count = 0

	lines = readFile(filename)

	if regex=='eval':
		match=match.replace('se(','eval_s(line,')
		match=match.replace('xre(','eval_x(line,')
		match=match.replace('re(','eval_r(line,')

	for line in lines:
		if regex=='wipe' and match in line:
			print formatLine(line.replace(match,''),lineid(line))
			count+=1
		elif regex=='eval' and eval(match):
			print formatLine(line)
			count+=1
		elif regex=="re" and re.search(match,line)!=None:
			print formatLine(line)
			count+=1
		elif regex=="xre" and re.search(match,line)==None:
			print formatLine(line)
			count+=1
		elif regex==None and match in line:
			print formatLine(line)
			count+=1


	loc = ('numlines','numlines_single')[count==1];
	if CONFIG['show_count']:
		print hi((' '*(int(CONFIG['id_size'])+1))+(LOCALE[loc] % count), CONFIG['hi_count'])

def countMatches(filename,match=''):
	lines = readFile(filename);

	counts=dict()

	for line in lines:
		res=match.findall(line)
		if len(res)==0:
			label=LOCALE['everything']

			if label not in counts: # label hasn't been encountered yet
				counts[label] = 0

			counts[label] += 1

		else:
			for i in res:
				label=i[1]

				if label not in counts: # label hasn't been encountered yet
					counts[label]=0

				counts[label]+=1

	sortable=list()
	for label in counts:
		if counts[label]!=0:
			temp = label
			sortable.append(temp)

	sortable.sort(key=K)

	for line in sortable:
		# list fancy infos
		loc = ('numlines','numlines_single')[counts[line]==1];
		#print formatLine(LOCALE[loc] % (line, hi(counts[line], CONFIG['hi_priority'])), show_id=False)
		print formatLine(line + ' ' + hi(LOCALE[loc] % counts[line], CONFIG['hi_count']), show_id=False)

		# save the show_count setting and indent output
		STATE['show_count']=CONFIG['show_count']
		CONFIG['show_count']=False
		STATE['indent']+=1

		# print
		if line==LOCALE['everything']:
			readLines(filename, match.pattern, 'xre')
		else:
			readLines(filename,line,'wipe')

		# restore things
		CONFIG['show_count']=STATE['show_count']
		STATE['indent']-=1

# write lines to the file
def writeLine(filename,line):
	try:
		temp=open(filename,'a+')
	except IOError:
		print LOCALE['ioerror'] % (filename,'appending')
		sys.exit(1)
	else:
		print LOCALE['added'] % formatLine(line)
		temp.write('%s\n' % line)
		temp.close()


# mark lines as complete
# also used to edit lines
def markLines(filename,match='',field="id"):
	lines = readFile(filename)

	try:
		temp=open(filename,'w+')
	except IOError:
		print LOCALE['ioerror'] % (filename,'writing')
		sys.exit(1)
	else:
		for line in lines:
			line=line.strip()

			if field=='id':
				fieldVal = lineid(line)
			elif field=='body':
				fieldVal = line

			# delete it
			if match in fieldVal:
				print LOCALE['deleted'] % formatLine(line)

			# don't delete it
			else:
				temp.write('%s\n' % line)
		temp.close()

def editLines(filename,match='',field="id"):
	lines = readFile(filename)

	try:
		temp=open(filename,'w+')
	except IOError:
		print LOCALE['ioerror'] % (filename,'writing')
		sys.exit(1)
	else:
		for line in lines:
			line=line.strip()

			if field=='id':
				fieldVal = lineid(line)
			elif field=='body':
				fieldVal = line

			# edit it
			if match in fieldVal:
				line=launchLineEditor(line)
				temp.write('%s\n' % line)
				print LOCALE['saved'] % formatLine(line)

			# don't edit it
			else:
				temp.write('%s\n' % line)
		temp.close()

# creates a temporary file and populates it with some text
# allows the user to edit the text and then returns the new text
def launchLineEditor(line):
	# this code is kinda borrowed from Mercurial...
	t=''

	(fd, name) = tempfile.mkstemp(prefix='trk-editor-',suffix='.txt',text=True)
	try:
		# open the temp file and fill it up with the existing text
		f=os.fdopen(fd,'w')
		f.write(line)
		f.close()

		# open the editor
		os.system("%s \"%s\"" % (CONFIG['editor'],name))

		# open the file and read the new text
		f=open(name)
		t=f.read()
		f.close()
	finally:
		# remove the temp file
		os.unlink(name)

	# return new text
	return t

# allows the user to edit the entire file at once
def launchFileEditor(filename):
	# open the file in the editor
	os.system("%s \"%s\"" % (CONFIG['editor'],filename))

	# sort the file by using markLines
	# 'Z' can never be part of the line ID,
	# so it will never match
	markLines(filename,'Z')

def cmdsettings(argv):
	configs = list()
	for key in CONFIG:
		configs.append(key+'=')

	options, remainder = getopt.getopt(argv,'',configs)

	for opt, arg in options:
		setOption(opt[2:], arg)

	return remainder

def settings():
	# get filename and open it
	try:
		lines = open(CONFIG['config'],'r')
	except IOError:
		print LOCALE['ioerror'] % (CONFIG['config'],'reading')
		sys.exit(1)
	else:
		# loop through it
		for line in lines:
			# if it matches our settings regex
			match=RE_SETTING.search(line)

			# set the configuration option!
			if match!=None:
				setOption(match.group(1), match.group(2))
		lines.close()

def setOption(key, val):
	if val.isdigit():
		CONFIG[key] = int(val)
	elif val.lower() == 'true':
		CONFIG[key] = True
	elif val.lower() == 'false':
		CONFIG[key] = False
	else:
		CONFIG[key] = val



def main(argv):
	task='none'
	filename="%s/%s" % (expanduser("~"),CONFIG['file'])

	if len(argv)>1: # more than one argument
		cmd = argv[0]
		if ('alias_'+cmd) in CONFIG:
			formatted = CONFIG['alias_'+cmd] % tuple(argv[1:])
			main(['eval',formatted])

		elif cmd in ALIAS['mark']:
			for task in argv[1:]:
				markLines(filename, task)
			os.system(CONFIG['markcmd'])

		elif cmd in ALIAS['mark_body']:
			for task in argv[1:]:
				markLines(filename, task, field='body')
			os.system(CONFIG['markcmd'])

		elif cmd in ALIAS['edit']:
			for task in argv[1:]:
				editLines(filename, task)
			os.system(CONFIG['editcmd'])

		elif cmd in ALIAS['edit_body']:
			for task in argv[1:]:
				editLines(filename, task, field='body')
			os.system(CONFIG['editcmd'])

		elif cmd in ALIAS['add']:
			for task in argv[1:]:
				writeLine(filename, task)
			os.system(CONFIG['writecmd'])

		elif cmd in ALIAS['search']:
			readLines(filename, argv[1])

		elif cmd in ALIAS['regex']:
			readLines(filename, argv[1], 're')

		elif cmd in ALIAS['xregex']:
			readLines(filename, argv[1], 'xre')

		elif cmd in ALIAS['eval']:
			readLines(filename, argv[1], 'eval')

	elif len(argv)==1: # only one argument, probably an alias
		task=argv[0]

		# user-defined aliases are evaluated first if the user decides they hate mine
		# and want to override them with their own
		if ('alias_'+task) in CONFIG:
			main(['eval',CONFIG['alias_'+task]])

		elif task[0]=='@' and ' ' not in task and len(task)>1:
			readLines(filename, task)

		elif task[0]=='+' and ' ' not in task and len(task)>1:
			readLines(filename, task)

		elif task[0] in ('0','1','2','3','4','5','6','7','8','9'):
			readLines(filename,'(%s)' % task)

		elif task in ALIAS['projects']:
			countMatches(filename,RE_PROJECT)

		elif task in ALIAS['contexts']:
			countMatches(filename,RE_CONTEXT)

		elif task in ALIAS['edit']:
			launchFileEditor(filename)
			os.system(CONFIG['editcmd'])

		elif task in ALIAS['list']:
			readLines(filename)

		else: # no alias
			writeLine(filename,task)
			os.system(CONFIG['writecmd'])

	else: # no arguments
		readLines(filename)

if __name__=='__main__':
	argv = cmdsettings(sys.argv[1:])
	settings()
	main(argv)
