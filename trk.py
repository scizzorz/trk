#!/usr/bin/python
import sys, getopt, md5, re

'''
I'm not sure how these doc things work yet. I don't use Python much, but for right now I'm just
using it as a basic road map for my ideas.

Add a new task:
	trk.py "task"

Complete a task:
	trk.py finish|complete|delete|hide "some sort of ID / regex?"

List tasks:
(alias for trk.py xregex "^x ")
	trk.py

List all tasks:
	trk.py all

List completed tasks:
(alias for trk.py regex "^x ")
	trk.py x|completed|finished|hidden

List tasks assigned to a +project:
(just an alias for trk.py search "+project")
	trk.py +project

List tasks assigned to a @context:
(just an alias for trk.py search "@context")
	trk.py @context

List tasks given a priority:
(just an alias for trk.py search "p#")
	trk.py p#

Search tasks:
	trk.py search|find "search term"

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

def listLines(todoFile, match='',regex=False):
	for line in todoFile:
		if regex==True and re.search(match,line)!=None:
			printLine(line.strip())
		elif regex==False and re.search(match,line)==None:
			printLine(line.strip())
		elif match in line:
			printLine(line.strip())

def printLine(line):
	lineid = md5.new(line)
	print "[%s] %s" % (lineid.hexdigest()[0:8], line)

def main(argv):
	task='none'
	filename='.todo'
	todoFile=open(filename,'r+')

	if len(argv)>0:
		if argv[0] in ('finish','complete','delete'):
			task=argv[1]
			print "Mark '%s' complete / hidden" % task
		elif argv[0] in ('search','find'):
			task=argv[1]
			print "Search '%s'" % task
			listLines(todoFile,task)
		elif argv[0] in ('regex','re'):
			task=argv[1]
			print "RegEx search '%s'" % task
			listLines(todoFile,task,True)
		elif argv[0] in ('xregex','xre'):
			task=argv[1]
			print "Exclusive RegEx search '%s'" % task
			listLines(todoFile,task,False)
		elif argv[0] in ('x','completed','finished','hidden'):
			print "List completed tasks"
			listLines(todoFile,'^x ',True)
		elif argv[0] in ('all'):
			print "List all tasks"
			listLines(todoFile)
		else:
			task=argv[0]
			if task[0]=='@':
				print "List context '%s'" % task[1:]
				listLines(todoFile,task)
			elif task[0]=='+':
				print "List project '%s'" % task[1:]
				listLines(todoFile,task)
			elif task[0]=='p':
				print "List priority '%s'" % task[1:]
				listLines(todoFile,task)
			else:
				print "Add '%s'" % task
	else:
		print 'List things'
		listLines(todoFile,'^x ',False)

if __name__=='__main__':
	main(sys.argv[1:])
