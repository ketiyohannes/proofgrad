"""Spec for first_non_repeating_character: the earliest character occurring exactly once, else the string "None".

Domain: strings of letters (both cases), digits and symbols; the empty string is included (the unit tests use it).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "first_non_repeating_character"

CLARIFICATIONS = [
    "Return the character as a one-character string; return the string \"None\" (not the None object) when every character repeats, including for an empty string.",
]

texts = st.one_of(
    st.text(alphabet="abcaAB", max_size=20),
    st.text(alphabet="ab", max_size=12),
    st.text(alphabet="abcdefghijABCD0123!@#", max_size=40),
)


@st.composite
def all_repeating(draw):
    chars = draw(st.lists(st.sampled_from("abcAB1!"), max_size=10))
    doubled = [c for c in chars for _ in range(draw(st.integers(2, 3)))]
    return "".join(draw(st.permutations(doubled)))


@prop("If a character is returned, it occurs exactly once in the input.", s=texts)
def returned_is_unique(f, s):
    r = f(s)
    assert isinstance(r, str)
    if r != "None":
        assert len(r) == 1 and s.count(r) == 1


@prop("No character occurring exactly once appears before the returned character.", s=texts)
def returned_is_first(f, s):
    singles = [c for c in s if s.count(c) == 1]
    assert f(s) == (singles[0] if singles else "None")


@prop("When every character repeats, the string \"None\" is returned.", s=all_repeating())
def all_repeat_gives_none(f, s):
    assert f(s) == "None"


@prop("Comparison is case-sensitive: 'a' and 'A' are different characters.",
      c=st.sampled_from("abcxyz"))
def case_sensitive(f, c):
    assert f(c + c.upper()) == c
    assert f(c * 2 + c.upper()) == c.upper()


@prop("Appending a fresh character to a string where everything repeats returns that character.",
      s=all_repeating(), c=st.sampled_from("zZ9#"))
def fresh_char_at_end(f, s, c):
    assert f(s + c) == c


@prop("The empty string gives \"None\".", dummy=st.just(None))
def empty_string(f, dummy):
    assert f("") == "None"
