#!/usr/bin/env python
import sys, os, getopt, md5, re, time, tempfile
import bumpy, trk

bumpy.config(cli = True)

filename = os.path.expanduser(trk.CONFIG['file'])

## manipulation tasks
@bumpy.task
def add(*items):
	for item in items:
		trk.add_line(filename, item)
	os.system(trk.CONFIG['add_cmd'])

@bumpy.task
def edit(*items):
	for item in items:
		trk.edit_lines(filename, item)
	os.system(trk.CONFIG['edit_cmd'])

@bumpy.task
# FIXME @bumpy.alias('finish', 'complete', 'done', 'hide', 'x')
def delete(*items):
	for item in items:
		trk.delete_lines(filename, item)
	os.system(trk.CONFIG['del_cmd'])

# FIXME @bumpy.task 'editsearch'
# FIXME @bumpy.task 'deletesearch'

## search tasks
@bumpy.task
# FIXME @bumpy.alias('#')
def hash(*args):
	if len(args):
		trk.read_lines_re(filename, match = re.compile(r'(^|\s)(\#([\w\/]*)(%s))' % '|'.join(args)))
	else:
		trk.print_tags(filename, trk.RE['hash'])

@bumpy.task
# FIXME @bumpy.alias('+')
def plus(*args):
	if len(args):
		trk.read_lines_re(filename, match = re.compile(r'(^|\s)(\+([\w\/]*)(%s))' % '|'.join(args)))
	else:
		trk.print_tags(filename, trk.RE['plus'])

@bumpy.task
# FIXME @bumpy.alias('@')
def at(*args):
	if len(args):
		trk.read_lines_re(filename, match = re.compile(r'(^|\s)(\@([\w\/]*)(%s))' % '|'.join(args)))
	else:
		trk.print_tags(filename, trk.RE['at'])

@bumpy.task
def search(arg):
	trk.read_lines(filename, arg)

@bumpy.task
def regex(arg):
	trk.read_lines_re(filename, match = arg)

@bumpy.task
def xregex(arg):
	trk.read_lines_re(filename, match = arg, exclusive = True)

@bumpy.task
# FIXME @bumpy.alias('all', 'list', 'ls')
def show():
	trk.read_lines(filename)

@bumpy.default
def default(*args):
	if len(args):
		add(*args)
	else:
		show()

if __name__ == '__main__':
	options, argv = trk.arg_settings(sys.argv[1:])
	trk.apply_arg_settings(options)
	trk.rc_settings()
	trk.apply_arg_settings(options)

	bumpy.main(argv)
