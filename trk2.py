#!/usr/bin/env python
import sys, os, getopt, md5, re, time, tempfile
import bumpy, trk

bumpy.config(cli = True)

## manipulation tasks
@bumpy.task
def add(*items):
	for i in items:
		print 'Adding {}'.format(i)

@bumpy.task
def edit(*ids):
	for i in ids:
		print 'Editing {}'.format(i)

@bumpy.task
# FIXME @bumpy.alias('finish', 'complete', 'done', 'hide', 'x')
def delete(*ids):
	for i in ids:
		print 'Deleting {}'.format(i)

# FIXME @bumpy.task 'editsearch'
# FIXME @bumpy.task 'deletesearch'

## search tasks
@bumpy.task
# FIXME @bumpy.alias('#')
def hash(*args):
	for i in args:
		print '#{}'.format(i)

@bumpy.task
# FIXME @bumpy.alias('+')
def plus(*args):
	for i in args:
		print '+{}'.format(i)

@bumpy.task
# FIXME @bumpy.alias('@')
def at(*args):
	for i in args:
		print '@{}'.format(i)

@bumpy.task
def search(arg):
	print 'Searching {}'.format(arg)

@bumpy.task
def regex(arg):
	print 'Regexing {}'.format(arg)

@bumpy.task
def xregex(arg):
	print 'Exclusive regexing {}'.format(arg)

@bumpy.task
# FIXME @bumpy.alias('all', 'list', 'ls')
def show():
	print 'Showing'

@bumpy.default
def default(*args):
	if len(args):
		add(*args)
	else:
		show()

if __name__ == '__main__':
	bumpy.main(sys.argv[1:])
