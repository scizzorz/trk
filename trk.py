#!/usr/bin/env python
import sys, os, getopt, md5, re, time, tempfile
from os.path import expanduser

# configuration
# hopefully all of these will be ported to a .trkrc
# and have command-line flags as well
CONFIG = dict()

# the configuration file
# this can't really be changed in a config file,
# but it can be changed by a flag
CONFIG['config'] = '%s/%s' % (expanduser('~'), '.trkrc')

# which file to use
CONFIG['file'] = '.todo'

# size of the md5 sum substring used as the task id
CONFIG['id_size'] = 4

# highlighting on
CONFIG['hi_style'] = 'xterm'

# highlight colors (ANSI palette) used to highlight each part of a task
CONFIG['hi_id'] = 7
CONFIG['hi_project'] = 11
CONFIG['hi_context'] = 10
CONFIG['hi_priority'] = 9
CONFIG['hi_due'] = 14
CONFIG['hi_overdue'] = 9
CONFIG['hi_count'] = 7

# which character to use for priority
CONFIG['priority_char'] = '!'

# which editor to use to edit tasks
CONFIG['editor'] = 'vim'

# show tasks count at the end or not?
CONFIG['show_count'] = True

# what character to use for indents
# how the heck do you change this in
# a config file...
CONFIG['indent'] = '   '

# debating use
CONFIG['writecmd'] = ''
CONFIG['editcmd'] = ''
CONFIG['markcmd'] = ''


# state tracking
STATE = dict()
STATE['indent'] = 0


# formatting dictionary
LOCALE = dict()
LOCALE['ioerror'] = 'Unable to open file "%s" for %s'
LOCALE['marked'] = 'Marked as done: %s'
LOCALE['deleted'] = 'Deleted: %s'
LOCALE['saved'] = 'Saved new item: %s'
LOCALE['added'] = 'Added new item: %s'
LOCALE['numlines'] = '%s items'
LOCALE['numlines_single'] = '%s item'
LOCALE['label'] = '%s %s items'
LOCALE['label_single'] = '%s %s item'
LOCALE['everything'] = 'everything else'

# command alias dictionary
ALIAS = dict()
ALIAS['add'] = ('add', 'a')
ALIAS['edit'] = ('edit', 'ed', 'e')
ALIAS['edit_body'] = ('editsearch', 'edits', 'esearch', 'ese', 'es')
ALIAS['mark'] = ('finish', 'complete', 'done', 'hide', 'x')
ALIAS['mark_body'] = ('xsearch', 'xse', 'xs')

ALIAS['projects'] = ('projects', 'proj', 'prj', '+')
ALIAS['contexts'] = ('contexts', 'cont', 'ctx', '@')
ALIAS['list'] = ('all', 'list', 'ls')
ALIAS['search'] = ('search', 'find', 'se', 'fi', 's', 'f')
ALIAS['regex'] = ('regex', 're')
ALIAS['xregex'] = ('xregex', 'xre')

# RegExes used to highlight colors
RE_PROJECT = re.compile(r'(^|\s)(\+([\w\+]+))')
RE_CONTEXT = re.compile(r'(^|\s)(\@([\w\@\+]+))')
RE_PRIORITY = re.compile(r'\s*(\((\d)\))\s*')
RE_DUE = re.compile(r'(\[(\d{1,2})/(\d{1,2})(/(\d{2,4}))*([@ ](\d{1,2})(:(\d{1,2}))*(am|pm)*)*\])')
RE_WHITESPACE = re.compile(r'\s+')

RE_SETTING = re.compile(r'(\w+)\s*\=\s*(.*)')

def date_to_mktime(datestring):
	match = RE_DUE.search(datestring)

	# convert match into a sortable Unix time
	if match != None:
		month = match.group(2)
		day = match.group(3)

		year = match.group(5) or time.strftime('%Y', time.gmtime())
		if len(year) == 3:
			year = time.strftime('%Y', time.gmtime())
		elif len(year) == 2:
			year = '20'+year

		hour = match.group(7) or '12'
		minute = match.group(9) or '00'

		pam = match.group(10) or 'am'
		pam = pam.upper()

		time_tuple = (month, day, year, hour, minute, pam)
		time_string = '%s %s %s %s %s %s' % time_tuple
		timestamp = time.strptime(time_string, '%m %d %Y %I %M %p')
		unix = time.mktime(timestamp)
	else:
		unix = None

	return unix

def line_compare(task_a, task_b):
	# these look backwards to me but they work...
	# if a > b, return -
	# if a < b, return +
	# if a = b, return 0

	# priority
	priority_match_a = RE_PRIORITY.search(task_a)
	priority_match_b = RE_PRIORITY.search(task_b)
	if priority_match_a == None and priority_match_b != None:
		return 1
	elif priority_match_a != None and priority_match_b == None:
		return -1
	elif priority_match_a != None and priority_match_b != None:
		ret = int(priority_match_b.group(2)) - int(priority_match_a.group(2))
		if ret != 0:
			return ret


	# dates
	time_a = date_to_mktime(task_a)
	time_b = date_to_mktime(task_b)

	# sort dateMatches
	if time_a == None and time_b != None:
		return 1
	elif time_a != None and time_b == None:
		return -1
	elif time_a != None and time_b != None:
		ret = time_b - time_a
		if ret != 0:
			return -ret/abs(ret)


	# string order
	return cmp(task_a, task_b)

# sorting key class
class K(object):
	def __init__(self, obj):
		self.obj = obj
	def __lt__(self, other):
		return line_compare(self.obj, other.obj) < 0
	def __gt__(self, other):
		return line_compare(self.obj, other.obj) > 0
	def __eq__(self, other):
		return line_compare(self.obj, other.obj) == 0
	def __le__(self, other):
		return line_compare(self.obj, other.obj) <= 0
	def __ge__(self, other):
		return line_compare(self.obj, other.obj) >= 0
	def __ne__(self, other):
		return line_compare(self.obj, other.obj) != 0

# computes the md5 task id of a line
def lineid(line):
	line = line.strip()
	return md5.new(line).hexdigest()[0:CONFIG['id_size']]

# highlights a string with the given color
def highlight(string, color):
	color = int(color)

	# conky highlighting
	if CONFIG['hi_style'] == 'conky':
		return '${color%d}%s${color}' % (color%10, string)

	# xterm highlighting
	elif CONFIG['hi_style'] == 'xterm':
		if color < 8:
			return '\033[%dm%s\033[0m' % (color + 30, string)
		else:
			return '\033[%dm%s\033[0m' % (color + 82, string)

	# none
	else:
		return string

def format_date(obj):
	ret = '%s/%s' % (obj.group(2), obj.group(3))
	if obj.group(5)!= None: # year
		ret += '/'+obj.group(5)

	if obj.group(7)!= None: # hour / time
		ret += ' '+obj.group(7)
		if obj.group(8)!= None: # minutes
			ret += obj.group(8)
		if obj.group(10)!= None: # am/pm
			ret += obj.group(10)

	if date_to_mktime('['+ret+']') < time.time():
		return highlight(ret, CONFIG['hi_overdue'])
	else:
		return highlight(ret, CONFIG['hi_due'])

# format a line for printing
def format_line(line, preid = None, show_id = True):
	line = line.strip()
	uncolored_line = line

	# priority
	has_priority = RE_PRIORITY.search(line)
	if has_priority != None:
		priority_chars = CONFIG['priority_char'] * int(has_priority.group(2))
		priority = highlight(priority_chars, CONFIG['hi_priority'])+' '
	else:
		priority = ''

	# strip duplicate whitespace (HTML DOES IT WHY CAN'T I)
	line = RE_WHITESPACE.sub(' ', line)

	# highlighting subs
	line = RE_PROJECT.sub(r'\1'+highlight(r'\3', CONFIG['hi_project']), line)
	line = RE_CONTEXT.sub(r'\1'+highlight(r'\3', CONFIG['hi_context']), line)
	line = RE_PRIORITY.sub('', line)
	line = RE_DUE.sub(format_date, line)

	# print them with priority
	line = priority+line.strip()

	if show_id:
		if preid == None:
			preid = lineid(uncolored_line)

		indent = STATE['indent'] * CONFIG['indent']
		return '%s%s %s' % (indent, highlight(preid, CONFIG['hi_id']), line)

	else:
		return '%s%s' % (STATE['indent']*CONFIG['indent'], line)

# read the file and return a list of sorted lines
def read_file(filename):
	try:
		temp = open(filename, 'r+')
	except IOError:
		print LOCALE['ioerror'] % (filename, 'reading')
		return None
	else:
		lines = [line for line in temp if line.strip()]
		lines.sort(key = K)
		temp.close()
		return lines

# read tasks
def read_lines(filename, match = ''):
	count = 0
	lines = read_file(filename)

	for line in lines:
		if match in line:
			print format_line(line)
			count += 1

	print_count(count)

def read_lines_first_match(filename, regex, match):
	count = 0
	lines = read_file(filename)

	for line in lines:
		found = regex.search(line)
		if found != None:
			label = found.group(2)
			if label == match:
				print format_line(line.replace(match, ''), preid = lineid(line))
				count += 1

	print_count(count)


def read_lines_re(filename, match, exclusive = False):
	count = 0
	lines = read_file(filename)

	for line in lines:
		found = False
		if exclusive and re.search(match, line) == None:
			found = True
		elif not exclusive and re.search(match, line) != None:
			found = True

		if found:
			print format_line(line)
			count += 1

	print_count(count)

# print a nice count
def print_count(count):
	if CONFIG['show_count']:
		loc = ('numlines', 'numlines_single')[count == 1]
		count_text = LOCALE[loc] % count
		indent = ' '*(CONFIG['id_size'] + 1)
		print highlight(indent + count_text, CONFIG['hi_count'])


def count_matches(filename, match):
	lines = read_file(filename)

	counts = dict()

	for line in lines:
		found = match.search(line)
		if found == None:
			label = LOCALE['everything']
		else:
			label = found.group(2)

		if label not in counts:
			counts[label] = 0

		counts[label] += 1

	sortable = list()
	for label in counts:
		if counts[label] != 0:
			temp = label
			sortable.append(temp)

	sortable.sort(key = K)

	for label in sortable:
		# list fancy infos
		loc = ('numlines', 'numlines_single')[counts[label] == 1]
		count_text = highlight(LOCALE[loc] % counts[label], CONFIG['hi_count'])
		print format_line(label + ' ' + count_text, show_id = False)

		# save the show_count setting and indent output
		STATE['indent'] += 1
		STATE['show_count'] = CONFIG['show_count']
		CONFIG['show_count'] = False

		# print
		if label == LOCALE['everything']:
			read_lines_re(filename, match = match.pattern, exclusive = True)
		else:
			read_lines_first_match(filename, match, label)

		# restore things
		STATE['indent'] -= 1
		CONFIG['show_count'] = STATE['show_count']

# write lines to the file
def write_line(filename, line):
	try:
		temp = open(filename, 'a+')
	except IOError:
		print LOCALE['ioerror'] % (filename, 'appending')
		sys.exit(1)
	else:
		print LOCALE['added'] % format_line(line)
		temp.write('%s\n' % line)
		temp.close()


# mark lines as complete
# also used to edit lines
def mark_lines(filename, match = '', search_type = 'id'):
	lines = read_file(filename)

	try:
		temp = open(filename, 'w+')
	except IOError:
		print LOCALE['ioerror'] % (filename, 'writing')
		sys.exit(1)
	else:
		for line in lines:
			line = line.strip()

			if search_type == 'id':
				search_body = lineid(line)
			elif search_type == 'body':
				search_body = line

			# delete it
			if match in search_body:
				print LOCALE['deleted'] % format_line(line)

			# don't delete it
			else:
				temp.write('%s\n' % line)
		temp.close()

def edit_lines(filename, match = '', search_type = 'id'):
	lines = read_file(filename)

	try:
		temp = open(filename, 'w+')
	except IOError:
		print LOCALE['ioerror'] % (filename, 'writing')
		sys.exit(1)
	else:
		for line in lines:
			line = line.strip()

			if search_type == 'id':
				search_body = lineid(line)
			elif search_type == 'body':
				search_body = line

			# edit it
			if match in search_body:
				line = launch_line_editor(line)
				temp.write('%s\n' % line)
				print LOCALE['saved'] % format_line(line)

			# don't edit it
			else:
				temp.write('%s\n' % line)
		temp.close()

# creates a temporary file and populates it with some text
# allows the user to edit the text and then returns the new text
def launch_line_editor(line):
	# this code is kinda borrowed from Mercurial...
	text = ''

	(file_desc, name) = tempfile.mkstemp(prefix = 'trk-editor-', suffix = '.txt', text = True)
	try:
		# open the temp file and fill it up with the existing text
		file_stream = os.fdopen(file_desc, 'w')
		file_stream.write(line)
		file_stream.close()

		# open the editor
		os.system('%s "%s"' % (CONFIG['editor'], name))

		# open the file and read the new text
		file_stream = open(name)
		text = file_stream.read()
		file_stream.close()
	finally:
		# remove the temp file
		os.unlink(name)

	# return new text
	return text

# allows the user to edit the entire file at once
def launch_file_editor(filename):
	# open the file in the editor
	os.system('%s "%s"' % (CONFIG['editor'], filename))

	# sort the file by using mark_lines
	# 'Z' can never be part of the line ID,
	# so it will never match
	mark_lines(filename, 'Z')

def arg_settings(args):
	configs = list()
	for key in CONFIG:
		configs.append(key+'=')

	options, remainder = getopt.getopt(args, '', configs)

	for opt, arg in options:
		set_option(opt[2:], arg)

	return remainder

def rc_settings():
	# get filename and open it
	try:
		lines = open(CONFIG['config'], 'r')
	except IOError:
		print LOCALE['ioerror'] % (CONFIG['config'], 'reading')
		sys.exit(1)
	else:
		# loop through it
		for line in lines:
			# if it matches our settings regex
			match = RE_SETTING.search(line)

			# set the configuration option!
			if match != None:
				set_option(match.group(1), match.group(2))
		lines.close()

def set_option(key, val):
	if val.isdigit():
		CONFIG[key] = int(val)
	elif val.lower() == 'true':
		CONFIG[key] = True
	elif val.lower() == 'false':
		CONFIG[key] = False
	else:
		CONFIG[key] = val



def main(args):
	task = 'none'
	filename = '%s/%s' % (expanduser('~'), CONFIG['file'])

	if len(args)>1: # more than one argument
		cmd = args[0]
		if cmd in ALIAS['mark']:
			for task in args[1:]:
				mark_lines(filename, task)
			os.system(CONFIG['markcmd'])

		elif cmd in ALIAS['mark_body']:
			for task in args[1:]:
				mark_lines(filename, task, search_type = 'body')
			os.system(CONFIG['markcmd'])

		elif cmd in ALIAS['edit']:
			for task in args[1:]:
				edit_lines(filename, task)
			os.system(CONFIG['editcmd'])

		elif cmd in ALIAS['edit_body']:
			for task in args[1:]:
				edit_lines(filename, task, search_type = 'body')
			os.system(CONFIG['editcmd'])

		elif cmd in ALIAS['add']:
			for task in args[1:]:
				write_line(filename, task)
			os.system(CONFIG['writecmd'])

		elif cmd in ALIAS['search']:
			read_lines(filename, args[1])

		elif cmd in ALIAS['regex']:
			read_lines_re(filename, match = args[1])

		elif cmd in ALIAS['xregex']:
			read_lines_re(filename, match = args[1], exclusive = True)

	elif len(args) == 1: # only one argument, probably an alias
		task = args[0]

		if task[0] == '@' and ' ' not in task and len(task)>1:
			read_lines(filename, task)

		elif task[0] == '+' and ' ' not in task and len(task)>1:
			read_lines(filename, task)

		elif task[0] in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
			read_lines(filename, '(%s)' % task)

		elif task in ALIAS['projects']:
			count_matches(filename, RE_PROJECT)

		elif task in ALIAS['contexts']:
			count_matches(filename, RE_CONTEXT)

		elif task in ALIAS['edit']:
			launch_file_editor(filename)
			os.system(CONFIG['editcmd'])

		elif task in ALIAS['list']:
			read_lines(filename)

		else: # no alias
			write_line(filename, task)
			os.system(CONFIG['writecmd'])

	else: # no arguments
		read_lines(filename)

if __name__ == '__main__':
	argv = arg_settings(sys.argv[1:])
	rc_settings()
	main(argv)
