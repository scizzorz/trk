#!/usr/bin/python
import sys, os, getopt, md5, re, time, tempfile
from os.path import expanduser

# configuration
# hopefully all of these will be ported to a .trkrc
# and have command-line flags as well
CONFIG=dict()

# size of the md5 sum substring used as the task id
CONFIG['id_size']=4

# highlighting on
CONFIG['hi_on']=True

# highlight colors (ANSI palette) used to highlight each part of a task
CONFIG['hi_id']=4
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

# RegExes used to highlight colors
RE_PROJECT=re.compile(r'(^|\s)(\+\w+)')
RE_CONTEXT=re.compile(r'(^|\s)(\@\w+)')
RE_PRIORITY=re.compile(r'\s*(\((\d)\))\s*')
RE_DUE=re.compile(r'(\[(\d{1,2})/(\d{1,2})(/(\d{2,4}))*(@(\d{1,2})(:(\d{1,2}))*(am|pm)*)*\])')
RE_DONE=re.compile(r'(^x\s*)')

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
	return md5.new(line).hexdigest()[0:CONFIG['id_size']]

# highlights a string with the given color
def hi(string,color):
	if(CONFIG['hi_on']!=True):
		return string
	elif color<8:
		return "\033[%dm%s\033[0m" % (color+30,string)
	else:
		return "\033[%dm%s\033[0m" % (color+82,string)
	
# read tasks
def readLines(filename, match='',regex=None):
	count = 0

	temp=open(filename,'r')
	lines=[line for line in temp if line.strip()]
	lines.sort(key=K)
	temp.close()

	if regex=='eval':
		match=match.replace('se(','eval_s(line,')
		match=match.replace('xre(','eval_x(line,')
		match=match.replace('re(','eval_r(line,')

	for line in lines:
		if regex=='eval' and eval(match):
			print formatLine(line)
			count+=1
		if regex=="re" and re.search(match,line)!=None:
			print formatLine(line)
			count+=1
		elif regex=="xre" and re.search(match,line)==None:
			print formatLine(line)
			count+=1
		elif match in line:
			print formatLine(line)
			count+=1
	
	print "%s tasks" % hi(count,CONFIG['hi_priority'])

def eval_s(line,match=''):
	return match in line
def eval_r(line,match=''):
	return re.search(match,line)!=None
def eval_x(line,match=''):
	return re.search(match,line)==None

# format a line for printing
def formatLine(line):
	line=line.strip()
	preColorLine=line

	# priority
	matchPriority=RE_PRIORITY.search(line)
	if matchPriority!=None:
		priority=hi(CONFIG['priority_char'] * int(matchPriority.group(2)),CONFIG['hi_priority'])+' '
	else:
		priority=''


	# highlighting subs
	line=RE_PROJECT.sub('\g<1>'+hi('\g<2>',CONFIG['hi_project']),line)
	line=RE_CONTEXT.sub('\g<1>'+hi('\g<2>',CONFIG['hi_context']),line)
	line=RE_PRIORITY.sub('',line)
	line=RE_DUE.sub(hi('\g<0>',CONFIG['hi_due']),line)

	# print them so they're aligned nicely
	if RE_DONE.search(line)!=None:
		line=RE_DONE.sub('',line)
		line=hi("x",CONFIG['hi_done'])+" "+priority+line.strip()
	else:
		line="  "+priority+line.strip()

	return "%s %s" % (hi("["+lineid(preColorLine)+"]",CONFIG['hi_id']),line)

# write lines to the file
def writeLine(filename,line):
	temp=open(filename,'a')
	print "Added %s" % formatLine(line)
	temp.write('%s\n' % line)
	temp.close()

# mark lines as complete
# also used to edit lines
def markLines(filename,match='',edit=None):
	temp=open(filename,'r')
	lines=[line for line in temp if line.strip()]
	lines.sort(key=K)
	temp.close()
	
	temp=open(filename,'w')
	for line in lines:
		line=line.strip()

		# if we're editing, we don't care if it's done or not
		if edit and match in lineid(line):
			line=editLine(line)
			temp.write('%s\n' % line)
			print "Saved new line %s" % formatLine(line)

		# if we're just marking it, we need to make sure it's not already marked
		elif match in lineid(line) and RE_DONE.search(line)==None:
			temp.write('x %s\n' % line)
			print "Marked line %s done" % hi('['+lineid(line)+']',CONFIG['hi_id'])

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

def main(argv):
	task='none'
	filename="%s/%s" % (expanduser("~"),CONFIG['file'])

	if len(argv)>1: # more than one argument
		cmd = argv[0]
		if cmd in ('x','finish','complete','hide'):
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
		if task[0]=='@' and ' ' not in task:
			main(['eval','se("%s") and xre("^x\s*")' % task])

		elif task[0]=='+' and ' ' not in task:
			main(['eval','se("%s") and xre("^x\s*")' % task])

		elif task[0] in ('0','1','2','3','4','5','6','7','8','9'):
			main(['eval','se("(%s)") and xre("^x\s*")' % task])

		elif argv[0] in ('x','completed','finished','hidden'):
			main(['regex','^x\s*'])

		elif argv[0] in ('all'):
			main(['search',''])

		else: # no alias
			writeLine(filename,task)

	else: # no arguments
		main(['xregex','^x\s*'])

if __name__=='__main__':
	main(sys.argv[1:])
