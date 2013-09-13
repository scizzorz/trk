import os, md5, re, time, tempfile
from .var import COLORS, CONFIG, RE, LOCALE

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

		if len(year) == 2:
			year = '20'+year

		hour = match.group(7) or '11'
		minute = match.group(9) or '59'
		meridiem = (match.group(10) or 'pm').upper()

		# convert it to a tm_struct and then into a unix timestamp
		time_tuple = (month, day, year, hour, minute, meridiem)
		timestamp = time.strptime(' '.join(time_tuple), '%m %d %Y %I %M %p')
		return time.mktime(timestamp)

	return 0

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
			print LOCALE['ioerror'].format(self.filename, 'reading')
		else:
			with temp:
				self.lines = [Line(line) for line in temp if line.strip()]

	def write(self):
		try:
			temp = open(self.filename, 'w')
		except IOError:
			print LOCALE['ioerror'].format(self.filename, 'writing')
		else:
			with temp:
				self.sort()
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
		self.write()

	def edit(self):
		os.system('{} "{}"'.format(CONFIG['editor'], self.filename))
		self.read()
		self.write()

	def display(self):
		if self.lines is None:
			return

		for line in self.lines:
			print line

	def display_tags(self, search):
		tags = dict()

		for line in self.lines:
			line_tags = search.findall(line.source)

			if not line_tags:
				line_tags.append(('', 'uncategorized', 'uncategorized'))

			for _, tag, _ in line_tags:
				subtags = tag.split('/')
				root = tags
				btag = ''

				for subtag in subtags:
					if btag:
						btag += '/'
					btag += subtag

					if btag not in root:
						root[btag] = {}
					root = root[btag]

				if '__base' not in root:
					root['__base'] = []

				root['__base'].append(line)

		self._display_tags_aux(tags)

	def _display_tags_aux(self, root, depth=-1, label='__root'):
		if depth >= 0:
			temp = label.split('/')

			if len(temp) > 1:
				display_label = label[0] + temp[-1]

			else:
				display_label = label

			print '{}{}'.format(CONFIG['indent'] * depth, Line(display_label, no_id = True))

		if '__base' in root:
			for line in root['__base']:
				# save the original source
				temp = line.source

				# filter current tag and print (using __repr__()!)
				line.source = line.source.replace(label, '').strip()
				print '{}{}'.format(CONFIG['indent'] * (depth + 1), line)

				# restore original source
				line.source = temp

		tags = sorted(root.keys())
		for tag in tags:
			if tag != '__base':
				self._display_tags_aux(root[tag], depth+1, tag)

	def sort(self):
		self.lines.sort()

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
	source = None
	uid = None
	sid = None
	priority = 0
	due = 0

	def __init__(self, source, no_id = False):
		self.source = source.strip()
		self.no_id = no_id
		self.update()

	def __repr__(self):
		return self.format()

	def update(self):
		self.uid = md5.new(self.source).hexdigest()
		self.sid = self.uid[:CONFIG['id_size']]

		priority = RE['priority'].search(self.source)
		if priority is not None:
			self.priority = int(priority.group(3))
			if self.priority == 0:
				self.priority = -1

		self.due = date_to_mktime(self.source)

	def format(self):
		pretty = self.source
		pretty = RE['whitespace'].sub(' ', pretty)
		pretty = RE['hash'].sub(r'\1' + highlight(r'\3', COLORS['hash']), pretty)
		pretty = RE['plus'].sub(r'\1' + highlight(r'\3', COLORS['plus']), pretty)
		pretty = RE['at'].sub(r'\1' + highlight(r'\3', COLORS['at']), pretty)
		pretty = RE['priority'].sub('', pretty)
		pretty = RE['due'].sub(format_date, pretty)

		if self.priority > 0:
			pretty = highlight(CONFIG['priority'] * self.priority, COLORS['priority']) + pretty
		elif self.priority < 0:
			pretty = highlight(CONFIG['priority'], COLORS['low_priority']) + pretty

		if self.no_id:
			return pretty

		return highlight(self.sid, COLORS['id']) + ' ' + pretty

	def edit(self):
		(desc, name) = tempfile.mkstemp(prefix = 'trk-', suffix = '.todo', text = True)
		try:
			with os.fdopen(desc, 'w') as temp:
				temp.write(self.source)

			os.system('{} "{}"'.format(CONFIG['editor'], name))

			with open(name) as temp:
				self.source = temp.read().strip()
				self.update()
				print LOCALE['saved'].format(self)

		finally:
			os.unlink(name)

	def str_cmp(self, other):
		str_self = RE['priority'].sub('', self.source)
		str_self = RE['due'].sub('', str_self)
		str_self = RE['whitespace'].sub('', str_self)
		str_other = RE['priority'].sub('', other.source)
		str_other = RE['due'].sub('', str_other)
		str_other = RE['whitespace'].sub('', str_other)

		return cmp(str_self, str_other)

	def due_cmp(self, other):
		return other.due - self.due

	def priority_cmp(self, other):
		return other.priority - self.priority

	def cmp(self, other):
		return self.priority_cmp(other) or self.due_cmp(other) or self.str_cmp(other)

	def __lt__(self, other):
		return self.cmp(other) < 0
	def __gt__(self, other):
		return self.cmp(other) > 0
	def __eq__(self, other):
		return self.cmp(other) == 0
	def __le__(self, other):
		return self.cmp(other) <= 0
	def __ge__(self, other):
		return self.cmp(other) >= 0
	def __ne__(self, other):
		return self.cmp(other) != 0
