#!/usr/bin/env python
import sys, os, md5, re, time, tempfile
import bumpy, trk

bumpy.config(cli = True)

CONFIG = {
	'config': '~/.trkrc',
	'file': '~/.todo',
	'editor': 'vim',

	'id_size': 4,
	'indent': '    ',
	'priority': '*',
	'soon': 86400,
	}

COLORS = {
	'id': 8,
	'count': 8,

	'plus': 12,
	'at': 2,
	'hash': 14,

	'priority': 1,
	'low_priority': 8,

	'due': 6,
	'due_soon': 4,
	'overdue': 1,
	}

RE = {
	'hash': re.compile(r'(^|\s)(\#([\w\/]+))'),
	'plus': re.compile(r'(^|\s)(\+([\w\/]+))'),
	'at':   re.compile(r'(^|\s)(\@([\w\/]+))'),
	'priority': re.compile(r'(^|\s)(\!(\d))'),
	'due': re.compile(r'(\[*(\d{1,2})/(\d{1,2})(/(\d{2,4}))*([@ ](\d{1,2})(:(\d{1,2}))*(am|pm)*)*\]*)'),
	'whitespace': re.compile(r'\s+'),

	'setting': re.compile(r'(\w+)\s*\=\s*(.*)')
	}

## functions
def highlight(string, color):
	color = int(color)

	if color < 8:
		return '\033[%dm%s\033[0m' % (color + 30, string)
	else:
		return '\033[%dm%s\033[0m' % (color + 82, string)

def date_to_mktime(datestring):
	match = RE['due'].search(datestring)

	if match is not None:
		month = match.group(2)
		day = match.group(3)

		year = match.group(5) or time.strftime('%Y')

		if len(year) == 3:
			year = time.strftime('%Y')
		elif len(year) == 2:
			year = '20'+year

		hour = match.group(7) or '11'
		minute = match.group(9) or '59'
		meridiem = (match.group(10) or 'pm').upper()

		# convert it to a tm_struct and then into a unix timestamp
		time_tuple = (month, day, year, hour, minute, meridiem)
		timestamp = time.strptime(' '.join(time_tuple), '%m %d %Y %I %M %p')
		return time.mktime(timestamp)

def format_date(obj):
	ret = obj.group(2) + '/' + obj.group(3)

	if obj.group(5): # /year
		ret += '/' + obj.group(5)

	if obj.group(7): # hour
		ret += ' '+obj.group(7)

		if obj.group(8): # :minutes
			ret += obj.group(8)

		if obj.group(10): # (am|pm)
			ret += obj.group(10)

	if date_to_mktime(ret) < time.time():
		color = 'overdue'
	elif date_to_mktime(ret) < time.time() + CONFIG['soon']:
		color = 'due_soon'
	else:
		color = 'due'

	return highlight(ret, COLORS[color])

## classes
class File:
	def __init__(self, filename):
		self.filename = filename
		self.lines = None

	def read(self):
		try:
			temp = open(self.filename)
		except IOError:
			# FIXME
			print "File.read() IOError"
		else:
			with temp:
				self.lines = [Line(line) for line in temp if line.strip()]

	def write(self):
		try:
			temp = open(self.filename, 'w')
		except IOError:
			# FIXME
			print "File.write() IOError"
		else:
			with temp:
				for line in self.lines:
					temp.write(line.source + '\n')

	def add(self, source):
		if type(source) is str:
			self.lines.append(Line(source))
		else:
			self.lines.append(source)

	def edit_each(self):
		for line in self.lines:
			line.edit()

	def edit(self):
		os.system('{} "{}"'.format(CONFIG['editor'], self.filename))

	def display(self):
		if self.lines is None:
			# FIXME
			print "Nothing to File.display() here"
			return

		for line in self.lines:
			print line

	def find_id(self, search):
		return [line for line in self.lines if (line.uid.startswith(search))]
	def find_xid(self, search):
		return [line for line in self.lines if (not line.uid.startswith(search))]
	def find_se(self, search):
		return [line for line in self.lines if (search in line.source)]
	def find_xse(self, search):
		return [line for line in self.lines if (search not in line.source)]
	def find_re(self, search):
		return [line for line in self.lines if (re.search(search, line.source))]
	def find_xre(self, search):
		return [line for line in self.lines if (not re.search(search, line.source))]

	def filter_id(self, search):
		self.lines = self.find_id(search)
	def filter_xid(self, search):
		self.lines = self.find_xid(search)
	def filter_se(self, search):
		self.lines = self.find_se(search)
	def filter_xse(self, search):
		self.lines = self.find_xse(search)
	def filter_re(self, search):
		self.lines = self.find_re(search)
	def filter_xre(self, search):
		self.lines = self.find_xre(search)


class Line:
	uid = None
	sid = None
	priority = None
	due = None
	source = None

	def __init__(self, source):
		self.source = source.strip()
		self.update()

	def __repr__(self):
		return self.format()

	def update(self):
		self.uid = md5.new(self.source).hexdigest()
		self.sid = self.uid[:CONFIG['id_size']]

		priority = RE['priority'].search(self.source)
		if priority is not None:
			self.priority = int(priority.group(3))
		else:
			self.priority = None

		self.due = date_to_mktime(self.source)

	def format(self):
		pretty = self.source
		pretty = RE['whitespace'].sub(' ', pretty)
		pretty = RE['hash'].sub(r'\1' + highlight(r'\3', COLORS['hash']), pretty)
		pretty = RE['plus'].sub(r'\1' + highlight(r'\3', COLORS['plus']), pretty)
		pretty = RE['at'].sub(r'\1' + highlight(r'\3', COLORS['at']), pretty)
		pretty = RE['priority'].sub('', pretty)
		pretty = RE['due'].sub(format_date, pretty)

		if self.priority:
			pretty = highlight(CONFIG['priority'] * self.priority, COLORS['priority']) + pretty
		elif self.priority is not None:
			pretty = highlight(CONFIG['priority'], COLORS['low_priority']) + pretty

		return highlight(self.sid, COLORS['id']) + ' ' + pretty

	def edit(self):
		(temp, name) = tempfile.mkstemp(prefix = 'trk-', suffix = '.todo', text = True)
		try:
			with os.fdopen(temp, 'w') as temp2:
				temp2.write(self.source)

			os.system('{} "{}"'.format(CONFIG['editor'], name))

			with open(name) as temp2:
				self.source = temp2.read().strip()
				self.update()
				print "Saving {}".format(self)

		finally:
			os.unlink(name)

## manipulation tasks
@bumpy.task
def add(*items):
	for item in items:
		line = Line(item)

		print 'Added {}'.format(line)
		temp.add(line)
	temp.write()

@bumpy.task
def edit(*items):
	# FIXME
	if items:
		for item in items:
			for line in temp.find_id(item):
				line.edit()
		temp.write()
	else:
		temp.edit()

@bumpy.task
# FIXME @bumpy.alias('finish', 'complete', 'done', 'hide', 'x')
def delete(*items):
	for item in items:
		for line in temp.find_id(item):
			print 'Deleted {}'.format(line)

		temp.filter_xid(item)
	temp.write()

# FIXME @bumpy.task 'editsearch'
# FIXME @bumpy.task 'deletesearch'

## search tasks
@bumpy.task
# FIXME @bumpy.alias('#')
def hash(*args):
	if args:
		temp.filter_re(r'(^|\s)(\#([\w\/]*)(%s))' % '|'.join(args))
		temp.display()
	else:
		# FIXME
		trk.print_tags(filename, trk.RE['hash'])

@bumpy.task
# FIXME @bumpy.alias('+')
def plus(*args):
	if args:
		temp.filter_re(r'(^|\s)(\+([\w\/]*)(%s))' % '|'.join(args))
		temp.display()
	else:
		# FIXME
		trk.print_tags(filename, trk.RE['plus'])

@bumpy.task
# FIXME @bumpy.alias('@')
def at(*args):
	if args:
		temp.filter_re(r'(^|\s)(\@([\w\/]*)(%s))' % '|'.join(args))
		temp.display()
	else:
		# FIXME
		trk.print_tags(filename, trk.RE['at'])

@bumpy.task
def search(arg):
	temp.filter_se(arg)
	temp.display()

@bumpy.task
def xsearch(arg):
	temp.filter_xse(arg)
	temp.display()

@bumpy.task
def regex(arg):
	temp.filter_re(arg)
	temp.display()

@bumpy.task
def xregex(arg):
	temp.filter_xre(arg)
	temp.display()

@bumpy.task
# FIXME @bumpy.alias('all', 'list', 'ls')
def show():
	temp.display()


# FIXME @bumpy.setup
def setup():
	global temp
	temp = File(os.path.expanduser(CONFIG['file']))
	temp.read()

@bumpy.default
def default(*args):
	if args:
		add(*args)
	else:
		show()

if __name__ == '__main__':
	setup()
	bumpy.main(sys.argv[1:])
