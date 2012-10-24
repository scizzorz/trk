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

RE_PROJECT=re.compile(r'\s(\+\w+)')
RE_CONTEXT=re.compile(r'\s(\@\w+)')
RE_PRIORITY=re.compile(r'(\(\d\))')
RE_DUE=re.compile(r'(\[\d{1,2}/\d{1,2}(/\d{2,4})*(@\d{1,2}(:\d{1,2})*(am|pm)*)*\])')

def lineid(line):
	line=line.strip()
	if line[0:2]=='x ':
		line=line[2:]
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
	lines.sort()
	temp.close()

	for line in lines:
		if regex==True and re.search(match,line)!=None:
			printLine(line)
		elif regex==False and re.search(match,line)==None:
			printLine(line)
		elif match in line:
			printLine(line)

def printLine(line):
	line=line.strip()
	preColorLine=line

	line=RE_PROJECT.sub(hi('\g<0>',CONFIG['hi_project']),line)
	line=RE_CONTEXT.sub(hi('\g<0>',CONFIG['hi_context']),line)
	line=RE_PRIORITY.sub(hi('\g<0>',CONFIG['hi_priority']),line)
	line=RE_DUE.sub(hi('\g<0>',CONFIG['hi_due']),line)

	if line[0:2]=='x ':
		line=hi("x",CONFIG['hi_done'])+" "+line[2:]
	else:
		line="  "+line
	print "%s %s" % (hi("["+lineid(preColorLine)+"]",CONFIG['hi_id']),line)

def writeLines(filename,lines):
	temp=open(filename,'a')
	for i in lines:
		print "Added %s %s" % (hi("[%s]" % lineid(i),CONFIG['hi_id']),i)
		temp.write('%s\n' % i)
	temp.close()

def markLines(filename,match=''):
	temp=open(filename,'r')
	lines=[line for line in temp if line.strip()]
	lines.sort()
	temp.close()
	
	temp=open(filename,'w')
	for line in lines:
		line=line.strip()
		if match in lineid(line) and line[0:2]!="x ":
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
			readLines(filename,'^x ',True)
		elif argv[0] in ('all'):
			print "List all tasks"
			readLines(filename)
		else: # no alias
			print "Add '%s'" % task
			writeLines(filename,argv)
	else: # no arguments
		print 'List incomplete tasks'
		readLines(filename,'^x ',False)

if __name__=='__main__':
	main(sys.argv[1:])
