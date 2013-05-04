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

# what character to use for indents
# how the heck do you change this in
# a config file...
CONFIG['indent'] = '   '

CONFIG['file'] = '.todo' # to do filename
CONFIG['id_size'] = 4 # size of md5sum substring used as task id
CONFIG['priority_char'] = '!' # which character to use for priority
CONFIG['editor'] = 'vim' # used for editing tasks
CONFIG['show_count'] = True # show total task count at the end
CONFIG['soon'] = 86400 # how soon to start highlighting upcoming due dates
CONFIG['hi_style'] = 'xterm' # highlighting

# color ID used to highlight each part of a task
CONFIG['hi_id'] = 7
CONFIG['hi_hash'] = 12
CONFIG['hi_plus'] = 11
CONFIG['hi_at'] = 10
CONFIG['hi_priority'] = 9
CONFIG['hi_due'] = 14
CONFIG['hi_due_soon'] = 10
CONFIG['hi_overdue'] = 9
CONFIG['hi_count'] = 7

# called after a successful addition / edit / deletion
CONFIG['writecmd'] = ''
CONFIG['editcmd'] = ''
CONFIG['markcmd'] = ''


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

ALIAS['hash'] = ('hash', '#')
ALIAS['plus'] = ('plus', '+')
ALIAS['at'] = ('at', '@')
ALIAS['list'] = ('all', 'list', 'ls')
ALIAS['search'] = ('search', 'find', 'se', 'fi', 's', 'f')
ALIAS['regex'] = ('regex', 're')
ALIAS['xregex'] = ('xregex', 'xre')

# regexes used to highlight colors
RE_HASH = re.compile(r'(^|\s)(\#([\w\/]+))')
RE_PLUS = re.compile(r'(^|\s)(\+([\w\/]+))')
RE_AT = re.compile(r'(^|\s)(\@([\w\/]+))')
RE_PRIORITY = re.compile(r'(^|\s)(\!(\d))')
RE_DUE = re.compile(r'(\[*(\d{1,2})/(\d{1,2})(/(\d{2,4}))*([@ ](\d{1,2})(:(\d{1,2}))*(am|pm)*)*\]*)')
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
		ret = int(priority_match_b.group(3)) - int(priority_match_a.group(3))
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

	if date_to_mktime(ret) < time.time():
		return highlight(ret, CONFIG['hi_overdue'])
	elif date_to_mktime(ret) < time.time()+CONFIG['soon']:
		return highlight(ret, CONFIG['hi_due_soon'])
	else:
		return highlight(ret, CONFIG['hi_due'])

# format a line for printing
def format_line(line, indent=0, preid = None, show_id = True):
	line = line.strip()
	uncolored_line = line

	# priority
	has_priority = RE_PRIORITY.search(line)
	if has_priority != None:
		priority_chars = CONFIG['priority_char'] * int(has_priority.group(3))
		priority = highlight(priority_chars, CONFIG['hi_priority'])+' '
	else:
		priority = ''

	# strip duplicate whitespace (HTML DOES IT WHY CAN'T I)
	line = RE_WHITESPACE.sub(' ', line)

	# highlighting subs
	line = RE_HASH.sub(r'\1'+highlight(r'\3', CONFIG['hi_hash']), line)
	line = RE_PLUS.sub(r'\1'+highlight(r'\3', CONFIG['hi_plus']), line)
	line = RE_AT.sub(r'\1'+highlight(r'\3', CONFIG['hi_at']), line)
	line = RE_PRIORITY.sub('', line)
	line = RE_DUE.sub(format_date, line)

	# print them with priority
	line = priority+line.strip()

	if show_id:
		if preid == None:
			preid = lineid(uncolored_line)

		return '%s%s %s' % (indent * CONFIG['indent'], highlight(preid, CONFIG['hi_id']), line)

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
			print format_line(line.replace(label, ''), indent = depth+1, preid = lineid(line))

	for tag in root:
		if tag != '__base':
			print_tags_aux(root[tag], depth+1, tag)

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

	# sort the file by using mark_lines
	# 'Z' can never be part of the line ID,
	# so it will never match
	mark_lines(filename, 'Z')

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
			if task[0] == '0':
				read_lines_re(filename, match = '\(\d\)', exclusive = True)
			else:
				read_lines(filename, '(%s)' % task)

		elif task in ALIAS['hash']:
			print_tags(filename, RE_HASH)

		elif task in ALIAS['plus']:
			print_tags(filename, RE_PLUS)

		elif task in ALIAS['at']:
			print_tags(filename, RE_AT)

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
