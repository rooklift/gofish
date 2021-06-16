**Note**: I'm not very happy with the state of the original Gofish, and have started a new version, [Gofish2](https://github.com/rooklift/gofish2).

# gofish: an SGF-based library

Tools for the game of Go:

* `gofish/` - the basic library, can read SGF, UGF, GIB, and NGF; can write SGF ([Smart Game Format](http://www.red-bean.com/sgf/))
* `game_editor.py` - a basic [kifu](https://en.wikipedia.org/wiki/Kifu) editor
* `gtp_relay.py` - a GUI to play against a GTP ([Go Text Protocol](https://www.lysator.liu.se/~gunnar/gtp/)) engine

The parser and game editor have been tested with [Kogo's Joseki Dictionary](http://waterfire.us/joseki.htm) as a fairly pathological test case; it loads in about 5 seconds.

As an example of how to use the GTP relay, if you have [GNU Go](https://www.gnu.org/software/gnugo/) installed, you can do:

    python gtp_relay.py gnugo --mode gtp

For programmers looking to do their own Go stuff, the most interesting part of all this is probably the SGF parser, **load_sgf_tree()** in `sgf.py`. There are also rudimentary parsers for GIB, NGF, and UGF formats (but the SGF parser is much more full-featured).

A standalone (single file) script that converts these things to SGF [is available](https://github.com/rooklift/xyz2sgf).

## Warning

This whole project grew fairly organically. While I do use it for my own projects, it remains a fairly disorganised and confusing mess, not *really* suitable for general use. Also, I made a number of design mistakes at the time, which became obvious later. As a result, my later [sgf library](https://github.com/rooklift/sgf) in Golang is much better than it would have been.

But I'm not very happy with the state of the original Gofish, and have started a new version, [Gofish2](https://github.com/rooklift/gofish2).

## Example library usage

```python
import gofish
from gofish import BLACK, WHITE

# We can create an SGF tree...

node = gofish.new_tree(19)

# We can get and set values...

if node.get_value("PB") is None:
    node.set_value("PB", "Jimmy")

# We can make moves, getting the new node as we go...

node = node.make_move(4, 4, BLACK)  # Intelligently determines colour
                                    # if colour argument missing

# An exception is raised for illegal moves...

try:
    node = node.make_move(4, 4)
except gofish.IllegalMove:
    print("Move was illegal")       # In this case, because the point is not empty

# We can find the move of a node...

move = node.move_coords()
colour = node.move_colour()

# We can set properties such as comments...

colour_text = {WHITE: "W", BLACK: "B", None: "?"}[colour]

if move is not None:
    node.set_value("C", "Move at {}, {} by {}".format(move[0], move[1], colour_text))

# We can create variations...

new_node_1 = node.make_move(16, 4)
new_node_2 = node.make_move(10, 10)

# We can find a node's children...

for n in node.children:
    n.set_value("C", "Iterating through the children works.")

# We can find a node's parent...

node == new_node_1.parent       # True

# We can save...

node.save("example.sgf")        # Saves the whole tree; can call this on any node.

```

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
