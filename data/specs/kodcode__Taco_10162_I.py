"""Spec for total_widgets_produced: total widgets = sum(speeds) * t.

Domain: n == len(speeds) with 1 <= n <= 1000 (kept small here), speeds in 1..100, and t in 0..10000
(t = 0 is exercised by the unit tests).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "total_widgets_produced"

CLARIFICATIONS = [
    "Return the total number of widgets as an int instead of printing it.",
    "t may be 0, in which case no widgets are produced.",
]

speed_lists = st.one_of(
    st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=30),
    st.builds(lambda v, n: [v] * n, st.integers(1, 100), st.integers(1, 30)),
)
times = st.integers(min_value=0, max_value=10000)


@prop("The result equals the sum over machines of speed times minutes.", speeds=speed_lists, t=times)
def total_production(f, speeds, t):
    assert f(len(speeds), speeds, t) == sum(s * t for s in speeds)


@prop("Zero minutes produce zero widgets.", speeds=speed_lists)
def zero_time(f, speeds):
    assert f(len(speeds), speeds, 0) == 0


@prop("A single machine produces speed * t widgets.", s=st.integers(min_value=1, max_value=100), t=times)
def single_machine(f, s, t):
    assert f(1, [s], t) == s * t


@prop("Production is additive over machines: splitting the machines into two groups sums their totals.",
      a=speed_lists, b=speed_lists, t=times)
def additive_over_machines(f, a, b, t):
    assert f(len(a) + len(b), a + b, t) == f(len(a), a, t) + f(len(b), b, t)


@prop("Production grows linearly with time: running t1 + t2 minutes equals the two runs combined.",
      speeds=speed_lists, t1=st.integers(0, 5000), t2=st.integers(0, 5000))
def linear_in_time(f, speeds, t1, t2):
    n = len(speeds)
    assert f(n, speeds, t1 + t2) == f(n, speeds, t1) + f(n, speeds, t2)


@prop("The result is an int.", speeds=speed_lists, t=times)
def returns_int(f, speeds, t):
    assert isinstance(f(len(speeds), speeds, t), int)
