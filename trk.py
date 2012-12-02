#!/usr/bin/env python
import sys, os, getopt, md5, re, time, tempfile
from os.path import expanduser

# configuration
# hopefully all of these will be ported to a .trkrc
# and have command-line flags as well
CONFIG=dict()

# size of the md5 sum substring used as the task id
CONFIG['id_size']=4

# highlighting on
CONFIG['hi_style']='xterm'

# highlight colors (ANSI palette) used to highlight each part of a task
CONFIG['hi_id']=3
CONFIG['hi_project']=10
CONFIG['hi_context']=11
CONFIG['hi_priority']=9
CONFIG['hi_due']=14
CONFIG['hi_done']=8

# which file to use
CONFIG['file']='.todo'

# which character to use for priority
CONFIG['priority_char']='!'

# which editor to use to edit tasks
CONFIG['editor']='vim'

# show tasks count at the end or not?
CONFIG['show_count']=True

# what character to use for indents
# how the heck do you change this in
# a config file...
CONFIG['indent']='      '


# state tracking
STATE=dict()
STATE['show_id']=True
STATE['indent']=0


LOCALE=dict()
LOCALE['ioerror']="Unable to open file '%s' for %s"
LOCALE['marked'] = 'Marked as done: %s'
LOCALE['saved'] = 'Saved new line: %s'
LOCALE['added'] = 'Added new line: %s'
LOCALE['numlines'] = '%s lines'
LOCALE['numlines_single'] = '%s line'
LOCALE['label'] = '%s %s lines'
LOCALE['label_single'] = '%s %s line'
LOCALE['everything'] = 'everything else'

# RegExes used to highlight colors
RE_PROJECT=re.compile(r'(^|\s)(\+[\w\+]+)')
RE_CONTEXT=re.compile(r'(^|\s)(\@[\w\+]+)')
RE_PRIORITY=re.compile(r'\s*(\((\d)\))\s*')
RE_DUE=re.compile(r'(\[(\d{1,2})/(\d{1,2})(/(\d{2,4}))*([@ ](\d{1,2})(:(\d{1,2}))*(am|pm)*)*\])')
RE_DONE=re.compile(r'(^x\s*)')
RE_WHITESPACE=re.compile(r'\s+')

RE_SETTING=re.compile(r'(\w+)\s*\=\s*(.*)')

def linecmp(a,b):
	# these look backwards to me but they work...
	# if a > b, return -
	# if a < b, return +
	# if a = b, return 0

	# doneness

	doneMatchA = RE_DONE.search(a)
	doneMatchB = RE_DONE.search(b)
	if doneMatchA!=None and doneMatchB==None:
		return 1
	elif doneMatchA==None and doneMatchB!=None:
		return -1

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
	
	dateMatchA = RE_DUE.search(a)
	dateMatchB = RE_DUE.search(b)

	# convert dateMatchA into a sortable Unix time
	if dateMatchA != None:
		monthA=dateMatchA.group(2)
		dayA=dateMatchA.group(3)
		yearA=dateMatchA.group(5) or time.strftime("%Y",time.gmtime())
		if len(yearA)==3:
			yearA=time.strftime("%Y",time.gmtime())
		elif len(yearA)==2:
			yearA="20"+yearA
		hourA=dateMatchA.group(7) or "12"
		minuteA=dateMatchA.group(9) or "00"
		pamA = dateMatchA.group(10) or 'am'
		pamA = pamA.upper()

		timeA=time.mktime(time.strptime("%s %s %s %s %s %s" % (monthA,dayA,yearA,hourA,minuteA,pamA),"%m %d %Y %I %M %p"))

	# convert dateMatchB into a sortable Unix time
	if dateMatchB != None:
		monthB=dateMatchB.group(2)
		dayB=dateMatchB.group(3)
		yearB=dateMatchB.group(5) or time.strftime("%Y",time.gmtime())
		if len(yearB)==3:
			yearB=time.strftime("%Y",time.gmtime())
		elif len(yearB)==2:
			yearB="20"+yearB
		hourB=dateMatchB.group(7) or "12"
		minuteB=dateMatchB.group(9) or "00"
		pamB = dateMatchB.group(10) or 'am'
		pamB = pamB.upper()

		timeB=time.mktime(time.strptime("%s %s %s %s %s %s" % (monthB,dayB,yearB,hourB,minuteB,pamB),"%m %d %Y %I %M %p"))
	
	# sort dateMatches
	if dateMatchA == None and dateMatchB != None:
		return 1
	elif dateMatchA != None and dateMatchB == None:
		return -1
	elif dateMatchA != None and dateMatchB != None:
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
	line=RE_DONE.sub('',line)
	return md5.new(line).hexdigest()[0:int(CONFIG['id_size'])]

# highlights a string with the given color
def hi(string,color):
	color = int(color)

	# conky highlighting
	if CONFIG['hi_style']=='conky':
		return "${color%d}%s${color}" % (color%9,string)

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
	
	return hi(ret,CONFIG['hi_due'])

# eval shortcuts
def eval_s(line,match=''):
	return match in line
def eval_r(line,match=''):
	return re.search(match,line)!=None
def eval_x(line,match=''):
	return re.search(match,line)==None

# read tasks
def readLines(filename, match='',regex=None):
	count = 0

	try:
		temp=open(filename,'r+')
	except IOError:
		print LOCALE['ioerror'] % (filename,'reading')
	else:
		lines=[line for line in temp if line.strip()]
		lines.sort(key=K)
		temp.close()

		if regex=='eval':
			match=match.replace('se(','eval_s(line,')
			match=match.replace('xre(','eval_x(line,')
			match=match.replace('re(','eval_r(line,')

		for line in lines:
			if regex=='wipe' and match in line and RE_DONE.search(line)==None:
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
		if CONFIG['show_count']: print LOCALE[loc] % hi(count,CONFIG['hi_priority'])

def countMatches(filename,match=''):
	try:
		temp = open(filename,'r+')
	except IOError:
		print LOCALE['ioerror'] % (filename,'reading')
	else:
		lines=[line for line in temp if line.strip()]
		temp.close()

		counts=dict()


		for line in lines:
			res=match.search(line)
			if res!=None:
				label=res.group(2)
			else:
				label=LOCALE['everything']

			if label not in counts: # label hasn't been encountered yet
				counts[label]=[0,0]

			if RE_DONE.search(line)==None: # task isn't done
				counts[label][0]+=1
			else: # task is done
				counts[label][1]+=1

		sortable=list()
		for label in counts:
			if counts[label][0]!=0:
				temp = label
				sortable.append(temp)

		sortable.sort(key=K)

		for line in sortable:
			STATE['show_id']=False
			if RE_DONE.search(line)!=None: # this group is completed, don't list fancy infos
				print formatLine(line)
				STATE['show_id']=True
			else: # list fancy infos
				loc = ('label','label_single')[counts[line][0]==1];
				print formatLine(LOCALE[loc] % (line,hi(counts[line][0],CONFIG['hi_priority'])))
				STATE['show_id']=True

				# save the show_count setting and indent output
				STATE['show_count']=CONFIG['show_count']
				CONFIG['show_count']=False
				STATE['indent']+=1

				# print
				if line==LOCALE['everything']:
					#readLines(filename,'se(%s) and xre(^x\s*)' % match,'eval')
					main(['eval','xre("%s") and xre("^x\s*")' % match.pattern])
				else:
					readLines(filename,line,'wipe')

				# restore things
				CONFIG['show_count']=STATE['show_count']
				STATE['indent']-=1

# format a line for printing
def formatLine(line,preid=None):
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

	# print them so they're aligned nicely
	if RE_DONE.search(line)!=None:
		line=RE_DONE.sub('',line)
		line=hi("x",CONFIG['hi_done'])+" "+priority+line.strip()
	else:
		line="  "+priority+line.strip()

	if STATE['show_id']:
		if preid==None:
			preid=lineid(preColorLine)	
		return "%s%s %s" % (STATE['indent']*CONFIG['indent'],hi("["+preid+"]",CONFIG['hi_id']),line)
	else:
		return "%s%s" % (STATE['indent']*CONFIG['indent'],line)

# write lines to the file
def writeLine(filename,line):
	try:
		temp=open(filename,'a+')
	except IOError:
		print LOCALE['ioerror'] % (filename,'appending')
	else:
		print LOCALE['added'] % formatLine(line)
		temp.write('%s\n' % line)
		temp.close()

# mark lines as complete
# also used to edit lines
def markLines(filename,match='',edit=None):
	try:
		temp=open(filename,'r+')
	except IOError:
		print LOCALE['ioerror'] % (filename,'reading')
	else:
		lines=[line for line in temp if line.strip()]
		lines.sort(key=K)
		temp.close()
	
	try:
		temp=open(filename,'w+')
	except IOError:
		print LOCALE['ioerror'] % (filename,'writing')
	else:
		for line in lines:
			line=line.strip()

			# if we're editing, we don't care if it's done or not
			if edit and match in lineid(line):
				line=editLine(line)
				temp.write('%s\n' % line)
				print LOCALE['saved'] % formatLine(line)

			# if we're just marking it, we need to make sure it's not already marked
			elif match in lineid(line) and RE_DONE.search(line)==None:
				temp.write('x %s\n' % line)
				print LOCALE['marked'] % formatLine(line)

			# none
			else:
				temp.write('%s\n' % line)
		temp.close()

def editLine(line):
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

def settings():
	# get filename and open it
	settingsname="%s/%s" % (expanduser("~"),".trkrc")
	try:
		lines = open(settingsname,'r')
	except IOError:
		pass
	else:
		# loop through it
		for line in lines:
			# if it matches our settings regex
			match=RE_SETTING.search(line)
			
			# set the configuration option!
			if match!=None:
				CONFIG[match.group(1)] = match.group(2)
		lines.close()


def main(argv):
	task='none'
	filename="%s/%s" % (expanduser("~"),CONFIG['file'])

	if len(argv)>1: # more than one argument
		cmd = argv[0]
		if ('alias_'+cmd) in CONFIG:
			formatted = CONFIG['alias_'+cmd] % tuple(argv[1:])
			main(['eval',formatted])

		elif cmd in ('x','finish','complete','hide'):
			for task in argv[1:]:
				markLines(filename,task)

		elif cmd in ('edit','ed'):
			for task in argv[1:]:
				markLines(filename,task,True)

		elif cmd in ('se','fi','search','find'):
			task=argv[1]
			readLines(filename,task)

		elif cmd in ('regex','re'):
			task=argv[1]
			readLines(filename,task,'re')

		elif cmd in ('xregex','xre'):
			task=argv[1]
			readLines(filename,task,'xre')

		elif cmd in ('add'):
			for task in argv[1:]:
				writeLine(filename,task)

		elif cmd in ('eval','es','ev'):
			task=argv[1]
			readLines(filename,task,'eval')

	elif len(argv)==1: # only one argument, probably an alias
		task=argv[0]

		# user-defined aliases are evaluated first if the user decides they hate mine
		# and want to override them with their own
		if ('alias_'+task) in CONFIG: 
			main(['eval',CONFIG['alias_'+task]])

		elif task[0]=='@' and ' ' not in task and len(task)>1:
			main(['eval','se("%s") and xre("^x\s*")' % task])

		elif task[0]=='+' and ' ' not in task and len(task)>1:
			main(['eval','se("%s") and xre("^x\s*")' % task])

		elif task[0] in ('0','1','2','3','4','5','6','7','8','9'):
			main(['eval','se("(%s)") and xre("^x\s*")' % task])

		elif task in ('x','completed','finished','hidden'):
			main(['regex','^x\s*'])

		elif task in ('projects','proj','prj','+'):
			countMatches(filename,RE_PROJECT)

		elif task in ('contexts','cont','ctx','@'):
			countMatches(filename,RE_CONTEXT)

		elif task in ('all'):
			main(['search',''])

		else: # no alias
			writeLine(filename,task)

	else: # no arguments
		main(['xregex','^x\s*'])

if __name__=='__main__':
	settings()
	main(sys.argv[1:])
