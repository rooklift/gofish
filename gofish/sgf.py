from gofish.constants import *
from gofish.tree import *


def parse_sgf(sgf, main_line_only = False):
    sgf = sgf.strip()
    sgf = sgf.lstrip("(")       # the load_sgf_tree() function assumes the leading "(" has already been read and discarded

    if main_line_only:
        root = load_sgf_tree_mainline_only(sgf)
    else:
        root, __ = load_sgf_tree(sgf, None)

    return root


def load_sgf_tree(sgf, parent_of_local_root):   # The caller should ensure there is no leading "("

    root = None
    node = None

    inside = False      # Are we inside a value? i.e. in C[foo] the value is foo
    value = ""
    key = ""
    keycomplete = False
    chars_to_skip = 0

    for i, c in enumerate(sgf):

        if chars_to_skip:
            chars_to_skip -= 1
            continue

        if inside:
            if c == "\\":
                # value += "\\"        # Do not do this. Discard the escape slash.
                try:
                    value += sgf[i + 1]
                except IndexError:
                    raise ParserFail
                chars_to_skip = 1
            elif c == "]":
                inside = False
                if node is None:
                    raise ParserFail
                node.add_value(key, value)      # This adds any escape slashes.
            else:
                value += c
        else:
            if c == "[":
                value = ""
                inside = True
                keycomplete = True
            elif c == "(":
                if node is None:
                    raise ParserFail
                __, chars_to_skip = load_sgf_tree(sgf[i + 1:], node)    # The child function will append the new tree to the node
            elif c == ")":
                if root is None:
                    raise ParserFail
                return root, i + 1          # return characters read
            elif c == ";":
                if node is None:
                    newnode = Node(parent = parent_of_local_root)
                    root = newnode
                    node = newnode
                else:
                    newnode = Node(parent = node)
                    node = newnode
            else:
                if c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":   # Other chars are skipped, e.g. AddWhite becomes AW (saw this once)
                    if keycomplete:
                        key = ""
                        keycomplete = False
                    key += c

    if root is None:
        raise ParserFail

    return root, i + 1          # return characters read


def load_sgf_tree_mainline_only(sgf):   # The caller should ensure there is no leading "("

    root = None
    node = None

    inside = False      # Are we inside a value? i.e. in C[foo] the value is foo
    value = ""
    key = ""
    keycomplete = False
    chars_to_skip = 0

    for i, c in enumerate(sgf):

        if chars_to_skip:
            chars_to_skip -= 1
            continue

        if inside:
            if c == "\\":
                # value += "\\"        # Do not do this. Discard the escape slash.
                try:
                    value += sgf[i + 1]
                except IndexError:
                    raise ParserFail
                chars_to_skip = 1
            elif c == "]":
                inside = False
                if node is None:
                    raise ParserFail
                node.add_value(key, value)      # This adds any escape slashes.
            else:
                value += c
        else:
            if c == "[":
                value = ""
                inside = True
                keycomplete = True
            elif c == "(":              # Ignored when only reading main line
                continue
            elif c == ")":              # First ) character indicates end of main line
                break
            elif c == ";":
                if node is None:
                    newnode = Node(parent = None)
                    root = newnode
                    node = newnode
                else:
                    newnode = Node(parent = node)
                    node = newnode
            else:
                if c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":   # Other chars are skipped, e.g. AddWhite becomes AW (saw this once)
                    if keycomplete:
                        key = ""
                        keycomplete = False
                    key += c

    if root is None:
        raise ParserFail

    return root
