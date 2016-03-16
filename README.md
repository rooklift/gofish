# SGF and GTP examples in Python / Tkinter

Tools for the game of Go. [SGF](http://www.red-bean.com/sgf/) (Smart Game Format) is the standard file format, while [GTP](https://www.lysator.liu.se/~gunnar/gtp/) (Go Text Protocol) is used for communicating with engines, e.g. if you have [GNU Go](https://www.gnu.org/software/gnugo/) installed, you can run:

    python gtp_relay.py gnugo --mode gtp

For programmers, the most interesting part of this is probably the SGF parser, **load_tree()** in `sgf.py`

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
