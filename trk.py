#!/usr/bin/env python
import sys, os, getopt, md5, re, time, tempfile
from os.path import expanduser

# configuration
# hopefully all of these will be ported to a .trkrc
# and have command-line flags as well
CONFIG = {
	# where to find the config file
	'config': '%s/%s' % (expanduser('~'), '.trkrc'),

	# what character to use for indents
	# how the heck do you change this in
	# a config file...
	'indent': '   ',

	# to do filename
	'file': '.todo',

	# size of md5sum substring used as task id
	'id_size': 4,

	# which character to use for priority
	'priority_char': '!',

	# used for editing tasks
	'editor': 'vim',

	# show total task count at the end
	'show_count': True,

	# how soon to start highlighting upcoming due dates
	'soon': 86400,

	# highlighting
	'hi_style': 'xterm',

	# color ID used to highlight each part of a task
	'hi_id': 7,
	'hi_hash': 12,
	'hi_plus': 11,
	'hi_at': 10,
	'hi_priority': 9,
	'hi_due': 14,
	'hi_due_soon': 10,
	'hi_overdue': 9,
	'hi_count': 7,

	# called after a successful addition / edit / deletion
	'add_cmd': '',
	'edit_cmd': '',
	'del_cmd': ''
}


# formatting dictionary
LOCALE = {
	'ioerror': 'Unable to open file "%s" for %s',
	'deleted': 'Deleted: %s',
	'saved': 'Saved new item: %s',
	'added': 'Added new item: %s',
	'numlines': '%s items',
	'numlines_single': '%s item',
	'label': '%s %s items',
	'label_single': '%s %s item',
	'everything': 'everything else'
}

# command alias dictionary
ALIAS = {
	'add': ('add', 'a'),
	'edit': ('edit', 'ed', 'e'),
	'edit_body': ('editsearch', 'edits', 'esearch', 'ese', 'es'),
	'delete': ('finish', 'complete', 'done', 'hide', 'x'),
	'delete_body': ('xsearch', 'xse', 'xs'),

	'hash': ('hash', '#'),
	'plus': ('plus', '+'),
	'at': ('at', '@'),
	'list': ('all', 'list', 'ls'),
	'search': ('search', 'find', 'se', 'fi', 's', 'f'),
	'regex': ('regex', 're'),
	'xregex': ('xregex', 'xre')
}

# regexes used to highlight colors
RE = {
	'hash': re.compile(r'(^|\s)(\#([\w\/]+))'),
	'plus': re.compile(r'(^|\s)(\+([\w\/]+))'),
	'at': re.compile(r'(^|\s)(\@([\w\/]+))'),
	'priority': re.compile(r'(^|\s)(\!(\d))'),
	'due': re.compile(r'(\[*(\d{1,2})/(\d{1,2})(/(\d{2,4}))*([@ ](\d{1,2})(:(\d{1,2}))*(am|pm)*)*\]*)'),
	'whitespace': re.compile(r'\s+'),

	'setting': re.compile(r'(\w+)\s*\=\s*(.*)')
}

def date_to_mktime(datestring):
	match = RE['due'].search(datestring)

	# convert match into a sortable Unix time
	if match != None:
		month = match.group(2)
		day = match.group(3)

		year = match.group(5) or time.strftime('%Y', time.gmtime())
		if len(year) == 3:
			year = time.strftime('%Y', time.gmtime())
		elif len(year) == 2:
			year = '20'+year

		hour = match.group(7) or '11'
		minute = match.group(9) or '59'

		pam = match.group(10) or 'pm'
		pam = pam.upper()

		time_tuple = (month, day, year, hour, minute, pam)
		time_string = '%s %s %s %s %s %s' % time_tuple
		timestamp = time.strptime(time_string, '%m %d %Y %I %M %p')
		unix = time.mktime(timestamp)
	else:
		unix = None

	return unix

def priority_compare(task_a, task_b):
	priority_a = RE['priority'].search(task_a)
	priority_b = RE['priority'].search(task_b)

	if priority_a is None and priority_b is None:
		return 0
	elif priority_a is None and priority_b is not None:
		return 1
	elif priority_a is not None and priority_b is None:
		return -1

	return int(priority_b.group(3)) - int(priority_a.group(3))

def time_compare(task_a, task_b):
	time_a = date_to_mktime(task_a)
	time_b = date_to_mktime(task_b)

	# sort matches
	if time_a is None and time_b is None:
		return 0
	elif time_a is None and time_b is not None:
		return 1
	elif time_a is not None and time_b is None:
		return -1

	return time_a - time_b

def string_compare(task_a, task_b):
	task_a = RE['priority'].sub('', task_a)
	task_a = RE['due'].sub('', task_a)
	task_a = RE['whitespace'].sub('', task_a)
	task_b = RE['priority'].sub('', task_b)
	task_b = RE['due'].sub('', task_b)
	task_b = RE['whitespace'].sub('', task_b)
	return cmp(task_a, task_b)

def line_compare(task_a, task_b):
	# these look backwards to me but they work...
	# if a > b, return -
	# if a < b, return +
	# if a = b, return 0
	return priority_compare(task_a, task_b) or time_compare(task_a, task_b) or string_compare(task_a, task_b)

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
	ret = '%s/%s' % (obj.group(2), obj.group(3)) # month/day

	if obj.group(5)!= None: # '/' + year
		ret += '/' + obj.group(5)

	if obj.group(7)!= None: # ' ' + hour
		ret += ' '+obj.group(7)

		if obj.group(8)!= None: # :minutes
			ret += obj.group(8)

		if obj.group(10)!= None: # (am|pm)
			ret += obj.group(10)

	if date_to_mktime(ret) < time.time():
		hi = 'hi_overdue'
	elif date_to_mktime(ret) < time.time()+CONFIG['soon']:
		hi = 'hi_due_soon'
	else:
		hi = 'hi_due'

	return highlight(ret, CONFIG[hi])

# format a line for printing
def format_line(line, indent=0, id = None, show_id = True):
	line = line.strip()
	if id is None:
		id = lineid(line)

	# priority
	has_priority = RE['priority'].search(line)
	if has_priority != None:
		priority_chars = CONFIG['priority_char'] * int(has_priority.group(3))
		priority = highlight(priority_chars, CONFIG['hi_priority'])+' '
	else:
		priority = ''

	# strip duplicate whitespace (HTML DOES IT WHY CAN'T I)
	line = RE['whitespace'].sub(' ', line)

	# highlighting subs
	line = RE['hash'].sub(r'\1'+highlight(r'\3', CONFIG['hi_hash']), line)
	line = RE['plus'].sub(r'\1'+highlight(r'\3', CONFIG['hi_plus']), line)
	line = RE['at'].sub(r'\1'+highlight(r'\3', CONFIG['hi_at']), line)
	line = RE['priority'].sub('', line)
	line = RE['due'].sub(format_date, line)

	# print them with priority
	line = priority + line.strip()

	if show_id:
		return '%s%s %s' % (indent * CONFIG['indent'], highlight(id, CONFIG['hi_id']), line)

	else:
		return '%s%s' % (indent * CONFIG['indent'], line)

# read the file and return a list of sorted lines
def read_file(filename):
	if not os.path.isfile(filename):
		return ['add a task with: ./trk.py "my very first task"']

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

def read_lines_re(filename, match, exclusive = False):
	count = 0
	lines = read_file(filename)

	for line in lines:
		found = False
		# (exclusive) == (no match found)
		# when exclusive, print if no match found
		# when inclusive, print if match found
		if exclusive == (re.search(match, line) is None):
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

def print_tags(filename, search):
	lines = read_file(filename)

	tags = dict()

	for line in lines:
		line_tags = search.findall(line)
		if not line_tags:
			line_tags.append(('', 'uncategorized', 'uncategorized'))

		for _, tag, _ in line_tags:
			subtags = tag.split("/")
			root = tags
			btag = ""
			for subtag in subtags:
				if btag:
					btag += "/"
				btag += subtag
				if btag not in root:
					root[btag] = {}
				root = root[btag]
			if '__base' not in root:
				root['__base'] = []
			root['__base'].append(line)

	print_tags_aux(tags)

def print_tags_aux(root, depth=-1, label="__root"):
	if depth >= 0:
		temp = label.split("/")
		if len(temp) > 1:
			display_label = label[0] + temp[-1]
		else:
			display_label = label
		print format_line(display_label, indent = depth, show_id = False)

	if '__base' in root:
		for line in root['__base']:
			print format_line(line.replace(label, ''), indent = depth+1, id = lineid(line))

	for tag in root:
		if tag != '__base':
			print_tags_aux(root[tag], depth+1, tag)

# add a line
def add_line(filename, line):
	try:
		temp = open(filename, 'a+')
	except IOError:
		print LOCALE['ioerror'] % (filename, 'appending')
		sys.exit(1)
	else:
		print LOCALE['added'] % format_line(line)
		temp.write('%s\n' % line)
		temp.close()

# delete lines
def delete_lines(filename, match = '', search_type = 'id'):
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

	(file_desc, name) = tempfile.mkstemp(prefix = 'trk-editor-', suffix = '.todo', text = True)
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

	# sort the file by using delete_lines
	# 'Z' can never be part of the line ID,
	# so it will never match
	delete_lines(filename, 'Z')

def arg_settings(args):
	configs = list()
	for key in CONFIG:
		configs.append(key+'=')

	return getopt.getopt(args, '', configs)

def apply_arg_settings(options):
	for opt, arg in options:
		set_option(opt[2:], arg)

def rc_settings():
	try:
		lines = open(CONFIG['config'], 'r')
	except IOError:
		# there wasn't anything there, no need to worry.
		pass
	else:
		# loop through it
		for line in lines:
			# if it matches our settings regex
			match = RE['setting'].search(line)

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
		if cmd in ALIAS['delete']:
			for task in args[1:]:
				delete_lines(filename, task)
			os.system(CONFIG['del_cmd'])

		elif cmd in ALIAS['delete_body']:
			for task in args[1:]:
				delete_lines(filename, task, search_type = 'body')
			os.system(CONFIG['del_cmd'])

		elif cmd in ALIAS['edit']:
			for task in args[1:]:
				edit_lines(filename, task)
			os.system(CONFIG['edit_cmd'])

		elif cmd in ALIAS['edit_body']:
			for task in args[1:]:
				edit_lines(filename, task, search_type = 'body')
			os.system(CONFIG['edit_cmd'])

		elif cmd in ALIAS['add']:
			for task in args[1:]:
				add_line(filename, task)
			os.system(CONFIG['add_cmd'])

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
			if task[0] == '0':
				read_lines_re(filename, match = '!\d', exclusive = True)
			else:
				read_lines(filename, '!%s' % task)

		elif task in ALIAS['hash']:
			print_tags(filename, RE['hash'])

		elif task in ALIAS['plus']:
			print_tags(filename, RE['plus'])

		elif task in ALIAS['at']:
			print_tags(filename, RE['at'])

		elif task in ALIAS['edit']:
			launch_file_editor(filename)
			os.system(CONFIG['edit_cmd'])

		elif task in ALIAS['list']:
			read_lines(filename)

		else: # no alias
			add_line(filename, task)
			os.system(CONFIG['add_cmd'])

	else: # no arguments
		read_lines(filename)

if __name__ == '__main__':
	# load and apply the command line settings
	# apply before so that the config file is updated
	options, argv = arg_settings(sys.argv[1:])
	apply_arg_settings(options)

	# load and apply the config file settings
	rc_settings()

	# apply the command line settings again
	# apply after so the command line settings override config file
	apply_arg_settings(options)

	main(argv)
