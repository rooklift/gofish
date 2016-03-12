# sgf

A simple [SGF](http://www.red-bean.com/sgf/sgf4.html) reader in Python. For programmers who stumble upon this, the meat of the parser is in the function **load_tree()** in `sgf.py`. It seems to work well on real SGF files.

The console app `sgf.py` provides a simple ability to view the main variation.
The GUI `sgf_pygame.py` also allows stepping backwards and variations:

* The Arrow Keys, PageUp, PageDown, Home, and End all step forward or back.
* Where a node has siblings (variations), Tab switches between them.
* If the current node is not the main line, Backspace returns to the main line.
