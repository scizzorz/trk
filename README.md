# trk

A nice little command-line interface for organizing tasks and small notes.

## Usage

Add a new task (alias for `./trk.py add "task"`):

	./trk.py "task"

Add multiple new tasks:

	./trk.py add "task1" "task2"

Complete a task:

	./trk.py x|finish|complete|hide "taskid"

List tasks (alias for `./trk.py xregex "^x\s*"`):

	./trk.py

List all tasks:

	./trk.py all

List all projects:

	./trk.py projects|proj|prj|+

List all contexts:

	./trk.py contexts|cont|ctx|@

List completed tasks (alias for `./trk.py regex "^x\s*"`):

	./trk.py x|completed|finished|hidden

List tasks assigned to a +project (alias for `./trk.py eval "se('+project') and xre('^x\s*')"`):

	./trk.py +project

List tasks assigned to a @context (alias for `./trk.py eval "se('@context') and xre('^x\s*')"`):

	./trk.py @context

List tasks given a priority (alias for `./trk.py eval "se('(#)') and xre('^x\s*')"`):

	./trk.py #

Search tasks:

	./trk.py search|find|se|fi "search term"

Search tasks with regex:

	./trk.py regex|re "pattern"

Search tasks with exclusive regex (ie every task that *doesn't* match the pattern):

	./trk.py xregex|xre "pattern"

Search tasks with an `eval`:  
*(`se(string)`, `re(string)`, and `xre(string)` are shorthand for their respective `trk` commands)*  
*(eg `./trk.py eval "se('text')"` is the same as `./trk.py search text`)*

	./trk.py eval|ev|es "eval"

Edit a task:

	./trk.py edit|ed "taskid"

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

`hi_project = 11`  
...task projects

`hi_context = 10`  
...task contexts

`hi_priority = 9`  
...task priorities

`hi_due = 14`  
...task due dates

`hi_done = 9`  
...task completion checkmarks

`priority_char = !`  
the character used to represent priority

`editor = vim`  
the text editor used to edit tasks

`show_count = True`  
show the number of tasks at the end of each output or not

`alias_XXX = YYY`  
allows you to create custom aliases. Expands `./trk.py XXX` into `./trk.py eval YYY`. Can also use arguments, eg `alias_r = re('%s')` will cause `./trk.py r ^x` to expand to `./trk.py eval "re('^x')"`

## Basic system

Basic task storage/layout:

* stored as a plaintext file
* one task per line
* priority is formatted like this: `(3)` (higher number is higher priority)
* due dates are formatted like this: `[10/31]`, `[10/31/2012]`, etc.
* due dates with a time are formatted like this: `[11/22@10am]`, `[10/25@8:30pm]`, `[10/31 8pm]`, etc.
* projects are formatted like this: `+project`
* subprojects are formatted like this: `+project+subproject`
* contexts are formatted like this: `@context`
* subcontexts are formatted like this: `@context+subcontext`
* finished tasks are formatted like this: `x task` (the lowercase x *must* be the first character and *must* be followed by a space!)
* ideally it should only be one priority / date / time per task, but we'll see if I do anything to enforce that
* no limit to number of projects / contexts a task can have

### Examples

	(2) [10/22] +cs220+lab2 submit @desktop
	(2) [10/15] +cs220+lab2+checkpoint submit @desktop
	(2) [10/14] +cs220+lab2+problem1 solve @desktop
	(2) [10/13] +cs220+lab2+problem2 solve @desktop
	(2) +work finish work for guy @desktop
	(1) [10/31] +halloween+costume make
	(1) [10/31] +halloween+costume buy materials @shopping
	call Mom @phone
