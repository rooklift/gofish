# gofish: an SGF-based library

Tools for the game of Go:

* `gofish/` - the basic library
* `game_editor.py` - a basic [kifu](https://en.wikipedia.org/wiki/Kifu) editor - reads SGF, UGF, GIB, and NGF; writes SGF ([Smart Game Format](http://www.red-bean.com/sgf/))
* `gtp_relay.py` - a GUI to play against a GTP ([Go Text Protocol](https://www.lysator.liu.se/~gunnar/gtp/)) engine

The game editor has been tested with [Kogo's Joseki Dictionary](http://waterfire.us/joseki.htm) as a fairly pathological test case; it seems to work, after 20-30 seconds of parsing...

As an example of how to use the GTP relay, if you have [GNU Go](https://www.gnu.org/software/gnugo/) installed, you can do:

    python gtp_relay.py gnugo --mode gtp

For programmers looking to do their own Go stuff, the most interesting part of all this is probably the SGF parser, **load_sgf_tree()** in `sgf.py`. There are also rudimentary parsers for GIB, NGF, and UGF formats (but the SGF parser is much more full-featured).

A standalone (single file) script that converts these things to SGF [is available](https://github.com/fohristiwhirl/xyz2sgf).

## Notes on SGF as I understand it

* An SGF file is a tree of nodes
* The start of a node is indicated with a semi-colon **;**
* Each node is a dictionary that maps a key to a list of values
* A key is a string of uppercase letters, usually just 1 or 2 characters long
* Following the key, a value is a string contained within **[]** characters
* An example node is **;B[pd]C[it begins]** - it has 2 keys with 1 value each
* If a key has multiple values, they are given like so: **KY[exa][mple][val][ues]**
* When a node has two or more children, each subtree is contained within parentheses **()**
* A subtree will always have a node right at the start, i.e. **(** is always followed by **;**
* The main tree is also contained in parentheses **()**

## Notes to future me on Tkinter and threading

The GUI should all be in the main thread. If any other threads need to touch the GUI, don't use the messaging system, which allegedly isn't thread-safe. Instead, put a message on a queue and have the GUI poll that queue regularly, e.g. with the .after() method.

On the other hand, if everything's in one thread, just directly calling methods in the target widget seems acceptable. Right?
