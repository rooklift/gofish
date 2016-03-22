# Internally, everything is stored as SGF (or rather a tree-structure that incorporates properties like SGF's).
# See tree.py for the implementation.

from gofish.gib import *
from gofish.ngf import *
from gofish.sgf import *
from gofish.ugf import *

def load(filename):

    with open(filename, encoding="utf8", errors="replace") as infile:
        contents = infile.read()

    # FileNotFoundError is just allowed to bubble up

    try:
        root = parse_sgf(contents)
    except ParserFail:
        if filename[-4:].lower() == ".gib":
            print("Parsing as SGF failed, trying to parse as GIB")
            root = parse_gib(contents)      # This itself can also raise ParserFail
        elif filename[-4:].lower() == ".ngf":
            print("Parsing as SGF failed, trying to parse as NGF")
            root = parse_ngf(contents)      # This itself can also raise ParserFail
        elif filename[-4:].lower() in [".ugf", ".ugi"]:
            print("Parsing as SGF failed, trying to parse as UGF")
            root = parse_ugf(contents)      # This itself can also raise ParserFail
        else:
            raise

    root.set_value("FF", 4)
    root.set_value("GM", 1)
    root.set_value("CA", "UTF-8")   # Force UTF-8

    if "SZ" in root.properties:
        size = int(root.properties["SZ"][0])
    else:
        size = 19
        root.set_value("SZ", "19")

    if size > 19 or size < 1:
        raise BadBoardSize

    # The parsers just set up SGF keys and values in the nodes, but don't touch the board or other info like
    # main line status and move count. We do that now:

    root.board = Board(size)
    root.is_main_line = True
    root.update_recursive()

    return root
