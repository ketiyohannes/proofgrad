"""Spec for is_palindrome: whether the decimal digits of a non-negative integer read the same both ways.

Domain: non-negative integers up to about 10**19 (the unit tests go beyond 2**31 - 1).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "is_palindrome"

CLARIFICATIONS = ["Return the Python booleans True or False."]


@st.composite
def palindromes(draw):
    half = draw(st.text(alphabet="0123456789", min_size=1, max_size=9))
    half = half.lstrip("0") or draw(st.sampled_from("123456789"))
    mid = draw(st.sampled_from(["", "0", "5", "9"]))
    return int(half + mid + half[::-1])


@st.composite
def non_palindromes(draw):
    digits = draw(st.text(alphabet="0123456789", min_size=2, max_size=19))
    digits = draw(st.sampled_from("123456789")) + digits[1:]
    if digits == digits[::-1]:
        last = "1" if digits[-1] != "1" else "2"
        digits = digits[:-1] + last
    return int(digits)


numbers = st.one_of(st.integers(0, 2**31 - 1), st.integers(0, 10**19), palindromes(), non_palindromes(), st.integers(0, 1000))


@prop("Constructed palindromes give True.", n=palindromes())
def palindromes_true(f, n):
    assert f(n) is True


@prop("Numbers whose digits differ from their reverse give False.", n=non_palindromes())
def non_palindromes_false(f, n):
    assert f(n) is False


@prop("The result is True exactly when the digit string equals its reverse.", n=numbers)
def matches_definition(f, n):
    s = str(n)
    assert f(n) is (s == s[::-1])


@prop("Single-digit numbers (including 0) are palindromes.", n=st.integers(0, 9))
def single_digit(f, n):
    assert f(n) is True


@prop("Multiples of 10 greater than 0 are not palindromes.", n=st.integers(1, 10**17).map(lambda x: 10 * x))
def trailing_zero_false(f, n):
    assert f(n) is False
