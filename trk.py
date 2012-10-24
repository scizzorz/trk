#!/usr/bin/python
import sys, getopt, md5, re, fileinput

'''
I'm not sure how these doc things work yet. I don't use Python much, but for right now I'm just
using it as a basic road map for my ideas.

Add a new task:
(alias for trk.py add "task")
	trk.py "task"

Add multiple new tasks:
	trk.py add "task1" "task2"

Complete a task:
	trk.py x|finish|complete|hide "taskid"

List tasks:
(alias for trk.py xregex "^x ")
	trk.py

List all tasks:
	trk.py all

List completed tasks:
(alias for trk.py regex "^x ")
	trk.py x|completed|finished|hidden

List tasks assigned to a +project:
(alias for trk.py search "+project")
	trk.py +project

List tasks assigned to a @context:
(alias for trk.py search "@context")
	trk.py @context

List tasks given a priority:
(alias for trk.py search "p#")
	trk.py p#

Search tasks:
	trk.py search|find|se|fi "search term"

Search tasks with regex:
	trk.py regex|re "pattern"

Search tasks with exclusive regex (ie every task that *doesn't* match the pattern):
	trk.py xregex|xre "pattern"

Basic task storage/layout:
	plaintext
	one task per line
	priority like this: p3
	due date like this: d10/31, d10/31/2012, etc.
	due date + time like this: d{date}@10am, d{date}@8:30pm, d{date}@8:30, d{date}@20, etc.
	projects like this: +project
	contexts like this: @context
	finished like this: x task (the lowercase x *must* be the first character and *must* be followed by a space!)
	ideally have it limit it to one priority / date / time per task, but we'll see about that
	no limit to number of projects / contexts it can have
	examples:
		p2 d10/22@8pm submit lab 220.2 +cs220 @desktop
		p2 finish work for Jim +msa @desktop
		p1 d10/31 make Halloween costume
		p1 d10/31 buy Halloween costume materials @shopping
		work on +trk
		call Mom @phone
'''

ID_SIZE=4

def lineid(line):
	line=line.strip()
	if line[0:2]=='x ':
		line=line[2:]
	return md5.new(line).hexdigest()[0:ID_SIZE]
	
def readLines(filename, match='',regex=None):
	temp=open(filename,'r+')
	for line in temp:
		if regex==True and re.search(match,line)!=None:
			printLine(line)
		elif regex==False and re.search(match,line)==None:
			printLine(line)
		elif match in line:
			printLine(line)

def printLine(line):
	line=line.strip()
	print "[%s] %s" % (lineid(line), line)

def writeLines(filename,lines):
	temp=open(filename,'a')
	for i in lines:
		print "Added [%s] %s" % (lineid(i),i)
		temp.write('%s\n' % i)

def markLines(filename,match=''):
	for line in fileinput.input(filename,inplace=1):
		line=line.strip()
		if match in lineid(line):
			# now how do I print that it was actually marked...?
			print line.replace(line,'x %s' % line)
		else:
			print line

def main(argv):
	task='none'
	filename='.todo'

	if len(argv)>1: # more than one argument
		if argv[0] in ('x','finish','complete','hide'):
			task=argv[1]
			print "Mark '%s' complete / hidden" % task
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
			print "List context '%s'" % task[1:]
			readLines(filename,task)
		elif task[0]=='+':
			print "List project '%s'" % task[1:]
			readLines(filename,task)
		elif task[0]=='p':
			print "List priority '%s'" % task[1:]
			readLines(filename,task)
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
