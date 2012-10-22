#!/usr/bin/python
import sys, getopt

'''
I'm not sure how these doc things work yet. I don't use Python much, but for right now I'm just using it as a basic road map for my ideas.

Add a new task:
	trk.py "task"

Complete a task:
	trk.py finish|complete|delete|hide "some sort of ID / regex?"

List tasks:
	trk.py

List tasks assigned to a +project:
	trk.py +project

List tasks assigned to a @context:
	trk.py @context

List tasks given a priority:
	trk.py p#


Basic task storage/layout:
	plaintext
	one task per line
	priority like this: p3
	due dates like this: d10/31, d10/31/2012, etc.
	due time like this: t10:00am, t10am, t10, t3pm, etc.
	projects like this: +project
	contexts like this: @context
'''



def main(argv):
	task='none'
	if len(argv)>0:
		if argv[0] in ('finish','complete','delete'):
			task=argv[1]
			print "Mark '%s' complete / hidden" % task
		else:
			task=argv[0]
			if task[0]=='@':
				print "List context '%s'" % task[1:]
			elif task[0]=='+':
				print "List project '%s'" % task[1:]
			elif task[0]=='p':
				print "List priority '%s'" % task[1:]
			else:
				print "Add '%s'" % task
	else:
		print 'List things'

if __name__=='__main__':
	main(sys.argv[1:])
