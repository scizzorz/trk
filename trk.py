#!/usr/bin/python
import sys, getopt, md5, re, fileinput
from os.path import expanduser

CONFIG=dict()

CONFIG['id_size']=4
CONFIG['hi_on']=True
CONFIG['hi_id']=4
CONFIG['hi_project']=10
CONFIG['hi_context']=11
CONFIG['hi_priority']=9
CONFIG['hi_due']=14
CONFIG['hi_done']=8
CONFIG['file']='.todo'
CONFIG['priority_char']='!'

RE_PROJECT=re.compile(r'\s(\+\w+)')
RE_CONTEXT=re.compile(r'\s(\@\w+)')
RE_PRIORITY=re.compile(r'\s*(\((\d)\))\s*')
RE_DUE=re.compile(r'(\[\d{1,2}/\d{1,2}(/\d{2,4})*(@\d{1,2}(:\d{1,2})*(am|pm)*)*\])')
RE_DONE=re.compile(r'(^x\s*)')

def linecmp(a,b):
	# these look backwards to me but they work...
	# if a > b, return -
	# if a < b, return +
	# if a = b, return 0

	doneMatchA = RE_DONE.search(a)
	doneMatchB = RE_DONE.search(b)
	if doneMatchA!=None and doneMatchB==None:
		return 1
	elif doneMatchA==None and doneMatchB!=None:
		return -1

	priorityMatchA = RE_PRIORITY.search(a)
	priorityMatchB = RE_PRIORITY.search(b)
	if priorityMatchA == None and priorityMatchB != None:
		return 1
	elif priorityMatchA != None and priorityMatchB == None:
		return -1
	elif priorityMatchA != None and priorityMatchB != None:
		return int(priorityMatchB.group(2)) - int(priorityMatchA.group(2))
	return cmp(a,b)


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

def lineid(line):
	line=line.strip()
	line=RE_DONE.sub('',line)
	return md5.new(line).hexdigest()[0:CONFIG['id_size']]

def hi(string,color):
	if(CONFIG['hi_on']!=True):
		return string
	elif color<8:
		return "\033[%dm%s\033[0m" % (color+30,string)
	else:
		return "\033[%dm%s\033[0m" % (color+82,string)
	
def readLines(filename, match='',regex=None):
	temp=open(filename,'r')
	lines=[line for line in temp if line.strip()]
	lines.sort(key=K)
	temp.close()

	for line in lines:
		if regex==True and re.search(match,line)!=None:
			print formatLine(line)
		elif regex==False and re.search(match,line)==None:
			print formatLine(line)
		elif match in line:
			print formatLine(line)

def formatLine(line):
	line=line.strip()
	preColorLine=line

	matchPriority=RE_PRIORITY.search(line)
	if matchPriority!=None:
		priority=hi(CONFIG['priority_char'] * int(matchPriority.group(2)),CONFIG['hi_priority'])+' '
	else:
		priority=''


	line=RE_PROJECT.sub(hi('\g<0>',CONFIG['hi_project']),line)
	line=RE_CONTEXT.sub(hi('\g<0>',CONFIG['hi_context']),line)
	line=RE_PRIORITY.sub('',line)
	line=RE_DUE.sub(hi('\g<0>',CONFIG['hi_due']),line)

	if RE_DONE.search(line)!=None:
		line=RE_DONE.sub('',line)
		line=hi("x",CONFIG['hi_done'])+" "+priority+line
	else:
		line="  "+priority+line

	return "%s %s" % (hi("["+lineid(preColorLine)+"]",CONFIG['hi_id']),line)

def writeLines(filename,lines):
	temp=open(filename,'a')
	for line in lines:
		print "Added %s" % formatLine(line)
		temp.write('%s\n' % line)
	temp.close()

def markLines(filename,match=''):
	temp=open(filename,'r')
	lines=[line for line in temp if line.strip()]
	lines.sort(key=K)
	temp.close()
	
	temp=open(filename,'w')
	for line in lines:
		line=line.strip()
		if match in lineid(line) and RE_DONE.search(line)==None:
			print "Marking line %s done" % hi('['+lineid(line)+']',CONFIG['hi_id'])
			temp.write('x %s\n' % line)
		else:
			temp.write('%s\n' % line)
	temp.close()

def main(argv):
	task='none'
	filename="%s/%s" % (expanduser("~"),CONFIG['file'])

	if len(argv)>1: # more than one argument
		if argv[0] in ('x','finish','complete','hide'):
			task=argv[1]
			print "Mark %s complete / hidden" % hi('['+task+']',CONFIG['hi_id'])
			markLines(filename,task)
		elif argv[0] in ('se','fi','search','find'):
			task=argv[1]
			print "Search '%s'" % task
			readLines(filename,task)
		elif argv[0] in ('regex','re'):
			task=argv[1]
			print "RegEx search '%s'" % task
			readLines(filename,task,True)
		elif argv[0] in ('xregex','xre'):
			task=argv[1]
			print "Exclusive RegEx search '%s'" % task
			readLines(filename,task,False)
		elif argv[0] in ('add'):
			print "Batch add %s" % argv[1:]
			writeLines(filename,argv[1:])
	elif len(argv)==1: # only one argument, probably an alias
		task=argv[0]
		if task[0]=='@':
			print "List %s" % hi(task,CONFIG['hi_context'])
			readLines(filename,task)
		elif task[0]=='+':
			print "List %s" % hi(task,CONFIG['hi_project'])
			readLines(filename,task)
		elif task[0] in ('0','1','2','3','4','5','6','7','8','9'):
			print "List %s" % hi('('+task+')',CONFIG['hi_priority'])
			readLines(filename,'('+task+')')
		elif argv[0] in ('x','completed','finished','hidden'):
			print "List completed tasks"
			readLines(filename,'^x\s*',True)
		elif argv[0] in ('all'):
			print "List all tasks"
			readLines(filename)
		else: # no alias
			print "Add '%s'" % task
			writeLines(filename,argv)
	else: # no arguments
		print 'List incomplete tasks'
		readLines(filename,'^x\s*',False)

if __name__=='__main__':
	main(sys.argv[1:])
