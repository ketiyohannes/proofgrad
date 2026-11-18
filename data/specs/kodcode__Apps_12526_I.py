"""Spec for convert_to_12_hour_format: "HH:MM" (24-hour) to "hh:MM AM/PM" (12-hour, zero-padded hour).

Domain: valid times "00:00" .. "23:59" with two-digit hours and minutes.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "convert_to_12_hour_format"

CLARIFICATIONS = [
    "The output hour is always two digits (e.g. \"02:30 PM\"), followed by a single space and \"AM\" or \"PM\".",
]

hours = st.one_of(st.integers(0, 23), st.sampled_from([0, 1, 11, 12, 13, 23]))
minutes = st.one_of(st.integers(0, 59), st.sampled_from([0, 1, 59]))


def fmt(h, m):
    return f"{h:02d}:{m:02d}"


@prop("The result is a string of the form 'hh:mm AM' or 'hh:mm PM' with a two-digit hour in 01..12.", h=hours, m=minutes)
def well_formed(f, h, m):
    r = f(fmt(h, m))
    assert isinstance(r, str) and len(r) == 8
    assert r[2] == ":" and r[5] == " " and r[6:] in ("AM", "PM")
    assert r[:2].isdigit() and 1 <= int(r[:2]) <= 12 and r[3:5].isdigit()


@prop("The minutes are copied unchanged.", h=hours, m=minutes)
def minutes_preserved(f, h, m):
    assert f(fmt(h, m))[3:5] == f"{m:02d}"


@prop("The period is AM for hours 00..11 and PM for hours 12..23.", h=hours, m=minutes)
def period_correct(f, h, m):
    assert f(fmt(h, m))[6:] == ("AM" if h < 12 else "PM")


@prop("The 12-hour clock hour is the 24-hour hour modulo 12, with 0 shown as 12.", h=hours, m=minutes)
def hour_correct(f, h, m):
    assert int(f(fmt(h, m))[:2]) == (h % 12 or 12)


@prop("Midnight hour maps to 12 AM and noon hour maps to 12 PM.", m=minutes)
def midnight_and_noon(f, m):
    assert f(fmt(0, m)) == f"12:{m:02d} AM"
    assert f(fmt(12, m)) == f"12:{m:02d} PM"


@prop("The full output matches the expected 12-hour string exactly.", h=hours, m=minutes)
def exact_output(f, h, m):
    assert f(fmt(h, m)) == f"{h % 12 or 12:02d}:{m:02d} {'AM' if h < 12 else 'PM'}"
