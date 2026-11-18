"""Spec for exist: whether word can be traced on the board along a path of horizontally/vertically adjacent, pairwise distinct cells.

Domain: rectangular boards with at least 1 row and 1 column of single-character strings; word is a
non-empty string. Boards are kept small (at most 4x4) so that a brute-force path oracle stays fast.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "exist"

CLARIFICATIONS = [
    "Letters are compared exactly (case-sensitive).",
    "Return a bool (True or False).",
]


@st.composite
def boards(draw, alphabet="ABC"):
    rows = draw(st.integers(1, 4))
    cols = draw(st.integers(1, 4))
    letters = draw(st.sampled_from([alphabet, alphabet[:2], alphabet[:1] + "Z"]))
    return [[draw(st.sampled_from(letters)) for _ in range(cols)] for _ in range(rows)]


def neighbours(board, r, c):
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(board) and 0 <= nc < len(board[0]):
            yield nr, nc


def traceable(board, word):
    """Brute force: try every simple path of adjacent cells spelling the word."""
    def extend(path, i):
        if i == len(word):
            return True
        r, c = path[-1]
        return any(board[nr][nc] == word[i] and (nr, nc) not in path and extend(path + [(nr, nc)], i + 1)
                   for nr, nc in neighbours(board, r, c))

    return any(board[r][c] == word[0] and extend([(r, c)], 1)
               for r in range(len(board)) for c in range(len(board[0])))


@st.composite
def board_and_word(draw):
    board = draw(boards())
    if draw(st.booleans()):
        word = draw(st.text(alphabet="ABCZ", min_size=1, max_size=7))
    else:
        word = draw(walk_word(board))
        if draw(st.booleans()):
            # Perturb one letter so the answer is often False but structurally close.
            i = draw(st.integers(0, len(word) - 1))
            word = word[:i] + draw(st.sampled_from("ABCZ")) + word[i + 1:]
    return board, word


@st.composite
def walk_word(draw, board):
    """Spell a word along a random simple path of adjacent cells."""
    r = draw(st.integers(0, len(board) - 1))
    c = draw(st.integers(0, len(board[0]) - 1))
    path = [(r, c)]
    length = draw(st.integers(1, min(8, len(board) * len(board[0]))))
    while len(path) < length:
        options = [p for p in neighbours(board, *path[-1]) if p not in path]
        if not options:
            break
        path.append(draw(st.sampled_from(options)))
    return "".join(board[r][c] for r, c in path)


@st.composite
def board_with_path(draw):
    board = draw(boards())
    return board, draw(walk_word(board))


@prop("The result is True exactly when some simple path of adjacent cells spells the word.", case=board_and_word())
def matches_bruteforce(f, case):
    board, word = case
    assert f(board, word) == traceable(board, word)


@prop("A word spelled along a simple path of adjacent cells is found (returns True).", case=board_with_path())
def found_when_planted(f, case):
    board, word = case
    assert f(board, word) is True


@prop("A word containing a letter that is not on the board is not found (returns False).",
      board=boards(), prefix=st.text(alphabet="ABC", max_size=4), suffix=st.text(alphabet="ABC", max_size=4))
def missing_letter_false(f, board, prefix, suffix):
    assert f(board, prefix + "Q" + suffix) is False


@prop("A word longer than the number of cells, or needing a cell twice, is not found.", letter=st.sampled_from("AB"),
      rows=st.integers(1, 3), cols=st.integers(1, 3), extra=st.integers(1, 3))
def cannot_reuse_cells(f, letter, rows, cols, extra):
    board = [[letter] * cols for _ in range(rows)]
    assert f(board, letter * (rows * cols)) is True
    assert f(board, letter * (rows * cols + extra)) is False


@prop("Reversing the word, or transposing the board, does not change the answer.", case=board_and_word())
def symmetry(f, case):
    board, word = case
    transposed = [list(col) for col in zip(*board)]
    expected = f(board, word)
    assert f(board, word[::-1]) == expected
    assert f(transposed, word) == expected


@prop("Diagonal neighbours are not adjacent.", a=st.sampled_from("AB"), b=st.sampled_from("CD"))
def no_diagonal_moves(f, a, b):
    board = [[a, "X"], ["Y", b]]
    assert f(board, a + b) is False
    assert f(board, a + "X" + b) is True
