from proofgrad.mutants import generate_mutants
from proofgrad.prompts import extract_code
from proofgrad.rewards import spec_rubric_reward, unit_test_reward
from proofgrad.verifier import verify

SPEC = '''
from hypothesis import strategies as st
from proofgrad.spec_runtime import prop

ENTRY_POINT = "my_max"
nonempty = st.lists(st.integers(), min_size=1)

@prop("The result is >= every element.", xs=nonempty)
def is_upper_bound(f, xs):
    m = f(xs)
    assert all(x <= m for x in xs)

@prop("The result is an element of the input.", xs=nonempty)
def is_member(f, xs):
    assert f(xs) in xs

@prop("The input list is not modified.", xs=nonempty)
def input_unchanged(f, xs):
    before = list(xs)
    f(xs)
    assert xs == before
'''

TESTS = '''
from solution import my_max

def test_simple():
    assert my_max([1, 3, 2]) == 3

def test_negative():
    assert my_max([-5, -2]) == -2
'''

CORRECT = "def my_max(xs):\n    return max(xs)\n"


def test_correct_solution_passes_everything():
    verdict = verify(CORRECT, "my_max", spec=SPEC, unit_tests=TESTS)
    assert verdict.spec_passed and verdict.tests_passed
    assert [p.name for p in verdict.properties] == ["is_upper_bound", "is_member", "input_unchanged"]


def test_partial_credit_per_property():
    # Returns an upper bound that is not in the list: fails membership only.
    verdict = verify("def my_max(xs):\n    return max(xs) + 1\n", "my_max", spec=SPEC)
    assert {p.name: p.passed for p in verdict.properties} == {"is_upper_bound": True, "is_member": False, "input_unchanged": True}
    assert abs(verdict.property_score - 2 / 3) < 1e-9


def test_input_mutation_does_not_corrupt_other_checks():
    code = "def my_max(xs):\n    xs.sort()\n    return xs[-1]\n"
    verdict = verify(code, "my_max", spec=SPEC)
    assert verdict.spec_passed  # f deep-copies arguments, so the caller's list is untouched


def test_crashes_timeouts_and_missing_functions_score_zero():
    assert verify("def my_max(xs):\n    while True: pass\n", "my_max", spec=SPEC, property_timeout=0.5).property_score == 0.0
    assert not verify("this is not python", "my_max", spec=SPEC).compiled
    assert not verify("def other(xs):\n    return 0\n", "my_max", spec=SPEC).compiled
    assert verify("import sys\nsys.exit(0)\n", "my_max", spec=SPEC).property_score == 0.0


def test_stdout_noise_does_not_break_results():
    verdict = verify("print('hello')\ndef my_max(xs):\n    print(xs)\n    return max(xs)\n", "my_max", spec=SPEC, unit_tests=TESTS)
    assert verdict.spec_passed and verdict.tests_passed


def test_unit_test_partial_credit():
    verdict = verify("def my_max(xs):\n    return 3\n", "my_max", unit_tests=TESTS)
    assert [t.passed for t in verdict.tests] == [True, False]


def test_mutants_are_distinct_and_differ_from_source():
    source = "def f(xs):\n    best = xs[0]\n    for x in xs[1:]:\n        if x > best:\n            best = x\n    return best\n"
    mutants = generate_mutants(source)
    assert mutants and len(set(mutants)) == len(mutants)
    assert any("x >= best" in m for m in mutants)  # comparison flip
    assert any(m.count("best = ") == 1 for m in mutants)  # statement deletion
    assert "max(" in generate_mutants("def f(xs):\n    return min(xs)\n")[0]  # builtin swap


def test_extract_code_prefers_block_defining_entry_point():
    completion = "Here:\n```python\ndef my_max(xs):\n    return max(xs)\n```\nUsage:\n```python\nprint(my_max([1]))\n```"
    assert extract_code(completion, "my_max").startswith("def my_max")
    assert extract_code("<think>hmm</think>```python\nx = 1\n") == "x = 1\n"


def test_reward_functions_rank_correct_above_wrong():
    completions = [[{"role": "assistant", "content": f"```python\n{code}```"}] for code in (CORRECT, "def my_max(xs):\n    return max(xs) + 1\n", "nope")]
    n = len(completions)
    spec_scores = spec_rubric_reward([None] * n, completions, entry_point=["my_max"] * n, spec=[SPEC] * n)
    test_scores = unit_test_reward([None] * n, completions, entry_point=["my_max"] * n, unit_tests=[TESTS] * n)
    assert spec_scores[0] == 1.0 and 0.0 < spec_scores[1] < 0.5 and spec_scores[2] == 0.0
    assert test_scores[0] == 1.0 and test_scores[2] == 0.0


def test_thinking_mode_answer_extraction():
    from proofgrad.evaluate import split_thinking

    # The chat template opens <think> in the prompt, so only the closing tag is in the completion.
    completion = "Draft:\n```python\ndef f(x):\n    return 0\n```\nWait, wrong.\n</think>\n\n```python\ndef f(x):\n    return x\n```"
    reasoning, answer = split_thinking(completion, thinking=True)
    assert reasoning.endswith("Wait, wrong.")
    assert "return x" in extract_code(completion, "f") and "return 0" not in extract_code(completion, "f")
    # A trace cut off by the token limit has no answer, even if it drafted code.
    assert split_thinking("```python\ndef f(x):\n    return 0\n```", thinking=True)[1] == ""


def test_audit_parses_training_tables(tmp_path):
    from proofgrad.audit import first_tests, split_leakage, training_signal

    def row(own, other, advantage):
        return f"│ │ USER          │ ASSISTANT     │         {own:.2f} │          {other:.2f} │      {advantage:.2f} │ │\n"

    # The tests run prints its own reward first, so the columns are swapped relative to a spec run.
    log = tmp_path / "train.log"
    log.write_text(
        "│ ┃ Prompt        ┃ Completion    ┃ unit_test_r… ┃ spec_rubric_… ┃ Advantage ┃ │\n"
        "╭──── Step 1 ────╮\n" + row(1.0, 0.4, 1.0) + row(0.2, 0.2, -1.0)
        + "╭──── Step 2 ────╮\n" + row(0.1, 0.0, 0.5) + row(0.0, 0.0, -0.5)
    )
    signal = training_signal(log, "tests")
    assert signal["groups"] == 2 and signal["completions"] == 4
    assert signal["groups_without_correct_answer"] == 0.5
    assert signal["tests_pass_spec_fail"] == 1.0  # the one test-passing answer fails the spec
    assert abs(signal["advantage_share_from_groups_without_correct_answer"] - 1 / 3) < 1e-9

    kept = first_tests("from solution import f\n\ndef test_a():\n    assert f(1)\n\ndef test_b():\n    assert f(2)\n", 1)
    assert "test_a" in kept and "test_b" not in kept and "import f" in kept
    problems = [{"entry_point": "trap", "split": "train"}, {"entry_point": "trap", "split": "test"}, {"entry_point": "g", "split": "test"}]
    assert split_leakage(problems) == ["trap"]


def test_judge_rejects_what_thin_tests_accept():
    from proofgrad.judge import attach

    problem = {"id": "p", "entry_point": "my_max", "spec": SPEC, "unit_tests": TESTS, "reference_solution": CORRECT}
    (judged,), dropped = attach([problem], thin=1)
    assert not dropped and judged["judge_cases"] >= 10
    assert "test_simple" in judged["thin_tests"] and "test_negative" not in judged["thin_tests"]

    # Right on both unit tests, wrong in general: only the reference comparison catches it.
    subtle = "def my_max(xs):\n    return xs[1] if len(xs) > 1 else xs[0]\n"
    assert verify(subtle, "my_max", unit_tests=TESTS).tests_passed
    assert not verify(subtle, "my_max", unit_tests=judged["judge_tests"]).tests_passed
    assert verify(CORRECT, "my_max", unit_tests=judged["judge_tests"]).tests_passed


def test_experiment_gates():
    from proofgrad.experiment import h1, h2, select

    def answers(pid, judge, thin, spec=None):
        return [
            {"id": pid, "judge_passed": j, "thin_passed": t, "tests_passed": j, "spec_passed": j if spec is None else spec}
            for j, t in zip(judge, thin)
        ]

    base = (
        answers("a", [1, 1, 0, 0], [1, 1, 1, 0])  # thin tests fooled once
        + answers("b", [1, 0, 0, 0], [1, 0, 0, 0])
        + answers("c", [0, 0, 0, 0], [0, 0, 0, 0])  # never solved: not selectable
    )
    result = h1(base)
    assert result["wrong_answers"] == 9
    assert result["checkers"]["thin"]["false_accept_rate"] == 1 / 9
    assert result["checkers"]["spec"]["false_accept_rate"] == 0

    problems = [{"id": pid, "entry_point": pid} for pid in "abc"]
    chosen = select(base, problems, size=1, exclude=set())
    assert {p["id"]: p["split"] for p in chosen} == {"a": "train", "b": "test"}

    thin_arm = answers("a", [0, 0, 0, 0], [1, 1, 1, 1]) + answers("b", [1, 0, 0, 0], [1, 0, 0, 0])
    spec_arm = answers("a", [1, 1, 1, 1], [1, 1, 1, 1]) + answers("b", [1, 1, 0, 0], [1, 1, 0, 0])
    outcome = h2({"base": base, "spec": spec_arm, "thin": thin_arm}, chosen)
    assert outcome["train"]["arms"]["thin"]["subtly_wrong_rate"] == 1.0
    assert outcome["train"]["differences"]["spec_minus_thin:judge_pass_rate"]["value"] == 1.0
    assert outcome["test"]["arms"]["spec"]["judge_pass_rate"] == 0.5


def test_spec_first_format_roundtrip():
    from proofgrad.experiment import h3, h3_data
    from proofgrad.prompts import extract_code, spec_first_answer, spec_first_prompt, stated_properties
    from proofgrad.sft import example, property_descriptions

    spec = '''from hypothesis import strategies as st
from proofgrad.spec_runtime import prop

ENTRY_POINT = "double"


@prop("The result is twice the input.", x=st.integers())
def doubles(f, x):
    assert f(x) == 2 * x


@prop("Zero maps to zero.", x=st.just(0))
def zero(f, x):
    assert f(x) == 0
'''
    assert property_descriptions(spec) == ["The result is twice the input.", "Zero maps to zero."]
    problem = {"id": "a", "entry_point": "double", "prompt": "Double it.", "spec": spec, "reference_solution": "def double(x):\n    return 2 * x\n"}
    prompt, target = example(problem, "props")
    assert prompt == spec_first_prompt("Double it.") and prompt.startswith("Double it.")
    assert stated_properties(target) == property_descriptions(spec)
    assert extract_code(target, "double").strip() == "def double(x):\n    return 2 * x"
    assert example(problem, "code")[1].startswith("```python") and stated_properties(example(problem, "code")[1]) == []
    assert stated_properties("Properties:\n1. first\n* second\nnot a bullet\n```python\n- not this\n```") == ["first", "second"]

    data = h3_data([problem, {**problem, "id": "b", "entry_point": "other"}, {**problem, "id": "c"}], [{**problem, "id": "c"}], exclude=set())
    assert [p["id"] for p in data["warmup"]] == ["b"]  # "a" shares the evaluated entry point
    assert data["problems_props"][0]["prompt"] == prompt

    records = [
        {"id": "p", "judge_passed": True, "completion": spec_first_answer(["one", "two"], "x")},
        {"id": "p", "judge_passed": False, "completion": "```python\nx\n```"},
    ]
    result = h3(records)
    assert result["state_properties"] == 0.5
    assert result["judge_pass_rate_with_properties"] == 1.0 and result["judge_pass_rate_without_properties"] == 0.0
