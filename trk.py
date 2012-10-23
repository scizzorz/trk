#!/usr/bin/python
import sys, getopt

'''
I'm not sure how these doc things work yet. I don't use Python much, but for right now I'm just
using it as a basic road map for my ideas.

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
	due date like this: d10/31, d10/31/2012, etc.
	due date + time like this: d{date}@10am, d{date}@8:30pm, d{date}@8:30, d{date}@20, etc.
	projects like this: +project
	contexts like this: @context
	ideally have it limit it to one priority / date / time per task, but we'll see about that
	no limit to number of projects / contexts it can have
	examples:
		p2 d10/22@8pm submit lab 220.2 +cs220 @desktop ## (priority 2, due October 22 at 8pm
		p2 finish work for Jim +msa @desktop
		p1 d10/31 make Halloween costume
		p1 d10/31 buy Halloween costume materials @shopping
		work on +trk
		call Mom @phone
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
