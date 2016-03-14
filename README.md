# sgf

A simple [SGF](http://www.red-bean.com/sgf/sgf4.html) editor in Python. For programmers who stumble upon this, the meat of the parser is in the function **load_tree()** in `sgf.py`. It seems to work well on real SGF files.

The console app `sgf.py` provides a simple ability to view the main variation.

The GUI also allows loading, saving, variations, *et cetera*. I'm not actually sure what version of Python and Tk it needs.

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
