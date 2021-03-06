# trk

A nice little command-line interface for organizing tasks and small notes.

**(this entire README is currently out of date; I'll update it shortly!)**

## Usage

### Modification commands

Add a new task (equivalent to `./trk.py add "task"`):

	./trk.py "task"

Add multiple new tasks:

	./trk.py add|a "task1" "task2"

Edit a task (locate by task ID):

	./trk.py edit|ed|e "taskid"

Edit a task (locate by task content):

	./trk.py editsearch|edits|esearch|ese|es "search"

Complete/delete a task (locate by task ID):

	./trk.py x|finish|complete|hide "taskid"

Complete/delete a task (locate by task body):

	./trk.py xs|xse|xsearch "search"

### View / search commands

List tasks (equivalent to `./trk.py all`):

	./trk.py

List all tasks:

	./trk.py all|list|ls

List grouped and sorted by +tags:

	./trk.py plus|+

List grouped and sorted by @tags:

	./trk.py at|@

List grouped and sorted by #tags:

	./trk.py hash|#

Search tasks:

	./trk.py search|find|se|fi|s|f "search term"

Search tasks with a regular expression:

	./trk.py regex|re "pattern"

Search tasks with an exclusive regular expression (ie every task that *doesn't* match the pattern):

	./trk.py xregex|xre "pattern"

List tasks with a +tag (equivalent to `./trk.py search "+tag"`):

	./trk.py +tag

List tasks with an @tag (equivalent to `./trk.py search "@tag"`):

	./trk.py @tag

List tasks with an #tag (equivalent to `./trk.py search "#tag"`):

	./trk.py #tag

List tasks given a priority (equivalent to `./trk.py search "(1)"`):

	./trk.py 1

## Settings

`trk` can read its configuration from a file or from command line flags. When writing in a file, put each declaration on its own line and separate the variable from its value with an equals sign. When setting at the command line, each variable's name can be used as a long flag (eg `--config=~/.not-the-default-trkrc`). Here is a list of available options:

`config = ~/.trkrc`  
the default configuration file

`file = .todo`  
the file used to store all your tasks

`id_size = 4`  
the string length for each task's unique identifier

`hi_style = xterm`  
the type of highlighting format `trk` should use. `xterm` and `conky` will print appropriate color escape codes, while any other value with turn off highlighting

`hi_id = 7`  
the palette color for highlighting task identifiers

`hi_plus = 11`  
...task +tags

`hi_at = 10`  
...task @tags

`hi_hash = 10`  
...task #tags

`hi_priority = 9`  
...task priorities

`hi_due = 14`  
...task due dates

`hi_due_soon = 10`  
...tasks due dates that are due "soon" (see the `soon` setting)

`hi_overdue = 9`  
...tasks due dates that are overdue

`soon = 86400`  
the number of the seconds before a task is due to start marking it as "soon". Tasks that are due within the next `soon` seconds will have their due dates highlighted with the `hi_due_soon` color

`priority_char = !`  
the character used to represent priority

`editor = vim`  
the text editor used to edit tasks

`show_count = True`  
show the number of tasks at the end of each output or not

## Basic system

Basic task storage/layout **(this needs to be rewritten)**:


* stored as a plaintext file
* one task per line
* priority is formatted like this: `(3)` (higher number is higher priority)
* due dates are formatted like this: `[10/31]`, `[10/31/2012]`, etc.
* due dates with a time are formatted like this: `[11/22@10am]`, `[10/25@8:30pm]`, `[10/31 8pm]`, etc.
* projects are formatted like this: `+project`
* subprojects are formatted like this: `+project+subproject`
* contexts are formatted like this: `@context`
* subcontexts are formatted like this: `@context@subcontext`
* finished tasks deleted immediately
* ideally it should only be one priority / date / time per task, but we'll see if I do anything to enforce that
* no limit to number of projects / contexts a task can have

## To Do (irony)
* Some sort of syncing system
* Perhaps an Android client as well
* Some sort of Unix-style piping

### Examples

	(2) [10/22] +cs220+lab2 submit @desktop
	(2) [10/15] +cs220+lab2+checkpoint submit @desktop
	(2) [10/14] +cs220+lab2+problem1 solve @desktop
	(2) [10/13] +cs220+lab2+problem2 solve @desktop
	(2) +work finish work for guy @desktop
	(1) [10/31] +halloween+costume make
	(1) [10/31] +halloween+costume buy materials @shopping
	call Mom @phone
