import os
import bumpy
from .func import File, Line
from .var import CONFIG, RE

## manipulation tasks
@bumpy.task
def add(*items):
	'''Add items to the list.'''
	for item in items:
		line = Line(item)

		print 'Added {}'.format(line)
		todo.add(line)
	todo.write()

@bumpy.task
def edit(*items):
	'''Edit items with certain IDs.'''
	if items:
		for item in items:
			for line in todo.find_id(item):
				line.edit()
		todo.write()
	else:
		todo.edit()

@bumpy.alias('esearch')
def editsearch(*items):
	'''Edit items that contain search terms.'''
	for item in items:
		for line in todo.find_se(item):
			line.edit()
	todo.write()

@bumpy.alias('finish', 'complete', 'done', 'hide', 'x')
def delete(*items):
	'''Delete items with certain IDs.'''
	for item in items:
		for line in todo.find_id(item):
			print 'Deleted {}'.format(line)

		todo.filter_xid(item)
	todo.write()


@bumpy.alias('dsearch')
def deletesearch(*items):
	'''Delete items that contain search terms.'''
	for item in items:
		for line in todo.find_se(item):
			print 'Deleted {}'.format(line)

		todo.filter_xse(item)
	todo.write()

## search tasks
@bumpy.alias('#')
def hash(*args):
	'''Filter by hashtags or display as a hashtag tree.'''
	if args:
		todo.filter_re(r'(^|\s)(\#([\w\/]*)(%s)(\s|\/|$))' % '|'.join(args))

	todo.display_tags(RE['hash'])

@bumpy.alias('+')
def plus(*args):
	'''Filter by plustags or display as a plustag tree.'''
	if args:
		todo.filter_re(r'(^|\s)(\+([\w\/]*)(%s)(\s|\/|$))' % '|'.join(args))

	todo.display_tags(RE['plus'])

@bumpy.alias('@')
def at(*args):
	'''Filter by attags or display as an attag tree.'''
	if args:
		todo.filter_re(r'(^|\s)(\@([\w\/]*)(%s)(\s|\/|$))' % '|'.join(args))

	todo.display_tags(RE['at'])

@bumpy.task
def search(arg):
	'''List items that contain a search term.'''
	todo.filter_se(arg)
	todo.display()

@bumpy.task
def xsearch(arg):
	'''List items that do not contain a search term.'''
	todo.filter_xse(arg)
	todo.display()

@bumpy.task
def regex(arg):
	'''List items that match a regular expression.'''
	todo.filter_re(arg)
	todo.display()

@bumpy.task
def xregex(arg):
	'''List items that do not match a regular expression.'''
	todo.filter_xre(arg)
	todo.display()

@bumpy.alias('all', 'list', 'ls')
def show():
	'''List all items.'''
	todo.display()


@bumpy.setup
@bumpy.private
def setup():
	global todo
	todo = File(os.path.expanduser(CONFIG['file']))
	todo.read()


@bumpy.default
@bumpy.private
def default(*args):
	'''Add items to the list or display it.'''
	if args:
		add(*args)
	else:
		show()
