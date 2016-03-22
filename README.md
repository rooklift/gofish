# gofish: an SGF-based library

Tools for the game of Go:

* `gofish/` - the basic library
* `gtp_relay.py` - a GUI to play against a GTP ([Go Text Protocol](https://www.lysator.liu.se/~gunnar/gtp/)) engine
* `sgf_editor.py` - a rudimentary SGF ([Smart Game Format](http://www.red-bean.com/sgf/)) editor

As an example of how to use the relay, if you have [GNU Go](https://www.gnu.org/software/gnugo/) installed, you can run:

    python gtp_relay.py gnugo --mode gtp

For programmers looking to do their own Go stuff, the most interesting part of all this is probably the SGF parser, **load_sgf_tree()** in `sgf.py`. There are also rudimentary parsers for GIB, NGF, and UGI/UGF formats (but the SGF parser is much more full-featured).

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
