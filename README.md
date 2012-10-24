# trk

A nice little command-line interface for organizing tasks and small notes.

## Usage

Add a new task (alias for `trk.py add "task"`):

	trk.py "task"

Add multiple new tasks:

	trk.py add "task1" "task2"

Complete a task:

	trk.py x|finish|complete|hide "taskid"

List tasks (alias for `trk.py xregex "^x "`):

	trk.py

List all tasks:

	trk.py all

List completed tasks (alias for `trk.py regex "^x "`):

	trk.py x|completed|finished|hidden

List tasks assigned to a +project (alias for `trk.py search "+project"`):

	trk.py +project

List tasks assigned to a @context (alias for `trk.py search "@context"`):

	trk.py @context

List tasks given a priority (alias for `trk.py search "(#)"`):

	trk.py #

Search tasks:

	trk.py search|find|se|fi "search term"

Search tasks with regex:

	trk.py regex|re "pattern"

Search tasks with exclusive regex (ie every task that *doesn't* match the pattern):

	trk.py xregex|xre "pattern"

## Basic roadmap

Basic task storage/layout:

* plaintext
* one task per line
* priority like this: `(3)` (smaller number is higher priority)
* due date like this: `[10/31]`, `[10/31/2012]`, etc.
* due date + time like this: `[11/22@10am]`, `[10/25@8:30pm]`, etc.
* projects like this: `+project`
* contexts like this: `@context`
* finished like this: `x task` (the lowercase x *must* be the first character and *must* be followed by a space!)
* ideally have it limit it to one priority / date / time per task, but we'll see about that
* no limit to number of projects / contexts it can have

### Examples

	(2) [10/22@8pm] submit lab 220.2 +cs220 @desktop
	(2) finish work for Jim +msa @desktop
	(1) [10/31] make Halloween costume
	(1) [10/31] buy Halloween costume materials @shopping
	work on +trk
	call Mom @phone
