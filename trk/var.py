import re

CONFIG = {
	'config': '~/.trkrc',
	'file': '~/.todo',

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
	'due': re.compile(r'((\d{1,2})/(\d{1,2})(/(\d{2}))*([@ ](\d{1,2})(:(\d{1,2}))*(am|pm)*)*)'),
	'whitespace': re.compile(r'\s+'),

	'setting': re.compile(r'(\w+)\s*\=\s*(.*)')
	}

LOCALE = {
	'ioerror': 'Unable to open file "{}" for {}',
	'added': 'Added {}',
	'deleted': 'Deleted {}',
	'saved': 'Saved {}',
	'uncategorized': 'uncategorized',
	}

