# trk

A nice little command-line interface for organizing tasks and small notes.

## Usage

Add a new task (alias for `trk.py add "task"`):

	trk.py "task"

Add multiple new tasks:

	trk.py add "task1" "task2"

Complete a task:

	trk.py x|finish|complete|hide "taskid"

List tasks (alias for `trk.py xregex "^x\s*"`):

	trk.py

List all tasks:

	trk.py all

List completed tasks (alias for `trk.py regex "^x\s*"`):

	trk.py x|completed|finished|hidden

List tasks assigned to a +project (alias for `trk.py eval "se('+project') and xre('^x\s*')"`):

	trk.py +project

List tasks assigned to a @context (alias for `trk.py eval "se('@context') and xre('^x\s*')"`):

	trk.py @context

List tasks given a priority (alias for `trk.py eval "se('(#)') and xre('^x\s*')"`):

	trk.py #

Search tasks:

	trk.py search|find|se|fi "search term"

Search tasks with regex:

	trk.py regex|re "pattern"

Search tasks with exclusive regex (ie every task that *doesn't* match the pattern):

	trk.py xregex|xre "pattern"

Search tasks with an `eval`:  
*(`se(string)`, `re(string)`, and `xre(string)` are shorthand for their respective `trk` commands)*  
*(eg `trk.py eval "se('text')"` is the same as `trk.py search text`)*

	trk.py eval|ev|es "eval"

Edit a task:

	trk.py edit|ed "taskid"

## Settings

`trk` reads settings from a `.trkrc` in the user's home directory. So far, here are all the valid options and their defaults:

`id_size = 4`  
the string length for each task's unique identifier

`hi_style = xterm`  
the type of highlighting format `trk` should use. `xterm` and `conky` will print appropriate color escape codes, while any other value with turn off highlighting

`hi_id = 4`  
the palette color for highlighting task identifiers

`hi_project = 10`  
...task projects

`hi_context 11`  
...task contexts

`hi_priority = 9`  
...task priorities

`hi_due = 14`  
...task due dates

`hi_done = 8`  
...task completion checkmarks

`file = .todo`  
the file used to store all your tasks

`priority_char = !`  
the character used to represent priority

`editor = vim`  
the text editor used to edit tasks

`alias_XXX = YYY`  
allows you to create custom aliases. Expands `trk.py XXX` into `trk.py eval YYY`. Can also use arguments, eg `alias_r = re('%s')` will cause `trk.py r ^x` to expand to `trk.py eval "re('^x')"`

## Basic roadmap

Basic task storage/layout:

* plaintext
* one task per line
* priority like this: `(3)` (higher number is higher priority)
* due date like this: `[10/31]`, `[10/31/2012]`, etc.
* due date + time like this: `[11/22@10am]`, `[10/25@8:30pm]`, `[10/31 8pm]`, etc.
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
