"""
Learnvia — Calculus I · Limit Practice

A three-tab Streamlit module for evaluating square-root limits of the

Tabs
    Lesson     Concept framing, guided example, two participation activities.
    Practice   Standard difficulty (a in 2..9), x -> -1 form.
    Homework   Homework difficulty (a in 10..15), x -> -1 form.

Algebra and answer verification use SymPy; exact rational comparison is
attempted first, with a small float tolerance as a fallback for decimal
entries so floating-point noise does not flag a correct response as wrong.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass
from typing import Optional, Tuple

import streamlit as st
import sympy as sp


# --- Constants ----------------------------------------------------------------

DIFFICULTIES = {
    "Practice":  (2, 9),
    "Homework": (10, 15),
}

ERROR_LABELS = {
    "missed_sqrt":        "Forgot the final square root",
    "sign":               "Sign slip when substituting",
    "direct_sub":         "Substituted before simplifying",
    "factor":             "Mis-factored the denominator",
    "cancelled_too_much": "Cancelled the denominator entirely",
    "reciprocal":         "Flipped the fraction",
    "off":                "Decimal rounded off the answer",
    "unknown":            "Got stuck on the steps",
}

# Maps each error tag to the step in the "How to Solve" walkthrough that
# the student most likely tripped on, so the explanation can highlight it.
ERROR_STEP = {
    "missed_sqrt":        4,
    "sign":               4,
    "direct_sub":         1,
    "factor":             2,
    "cancelled_too_much": 3,
    "reciprocal":         3,
}

MC_QUESTIONS = [
    {
        "prompt": "When direct substitution into a limit produces 0/0, the result is ___.",
        "options": [
            "The limit does not exist.",
            "The limit equals 0.",
            "The expression is indeterminate — simplify the radicand before evaluating.",
            "The function is undefined at every point.",
        ],
        "correct": 2,
        "explain": (
            "0/0 is an <strong>indeterminate form</strong>.<br><br>Both the numerator and denominator "
            "vanish at the limit point, so the ratio is not yet determined. "
            "Factor, cancel the shared root, then re-substitute to recover the actual value."
        ),
        "wrong_explains": {
            0: "0/0 does not automatically mean the limit is missing. "
               "The form is indeterminate — the ratio is unresolved, not absent. "
               "Factoring the denominator often reveals a perfectly finite limit value.",
            1: "0/0 does not equal 0. Both pieces vanish, but the ratio is not "
               "determined by that alone. Always simplify the expression first "
               "before drawing any conclusion.",
            3: "A limit describes what the function approaches near a point, not "
               "at the point itself. The function can be undefined at x0 and still "
               "have a well-defined limit there.",
            },
        },
    {
        "prompt": (
            "Why is the square root the last step when evaluating "
            r"$\lim \sqrt{f(x)/g(x)}$ at an indeterminate point?"
        ),
        "options": [
            "Square roots cannot be applied to fractions.",
            "Take the root last so the radicand is fully simplified — pulling the root "
            "early skips the algebra that resolves the 0/0.",
            "The square root cancels with the limit operation.",
            "Taking the square root first would give a complex number.",
        ],
        "correct": 1,
        "explain": (
            "Until the 0/0 inside the radical is resolved by factoring and cancellation, "
            "the square root has nothing meaningful to act on.<br><br>Simplify the radicand "
            "first, evaluate the resulting finite value, <strong>then</strong> take the root."
        ),
        "wrong_explains": {
            0: "Square roots can be applied to fractions without any problem. "
               "The trouble is that the radicand is still 0/0 and needs to be "
               "simplified before the square root has anything meaningful to act on.",
            2: "The square root and the limit are separate operations and do not "
               "cancel each other. The limit finds the value the expression "
               "approaches, and the square root is applied to that value afterward.",
            3: "After factoring and cancelling, the radicand becomes a positive "
               "number, so complex numbers are not the concern here. The real reason "
               "to wait is that sqrt(0/0) is indeterminate until the algebra is done.",
        },
    },
]


# --- Page setup ---------------------------------------------------------------

st.set_page_config(
    page_title="Limit Practice",
    page_icon="√",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
:root {
  --lv-bg:            #F0F4FF;
  --lv-card:          #FFFFFF;
  --lv-border:        #C7D4F5;
  --lv-text:          #1A1A2E;
  --lv-muted:         #6B7280;
  --lv-primary:       #3B5BDB;
  --lv-primary-dark:  #2F4AC0;
  --lv-primary-soft:  #DBEAFE;
  --lv-success:       #2D8A5E;
  --lv-success-soft:  #D6F5E6;
  --lv-warning:       #B45309;
  --lv-warning-soft:  #FEF3C7;
  --lv-error:         #B91C1C;
  --lv-error-soft:    #FEE2E2;
  --lv-accent:        #7C3AED;
  --lv-accent-soft:   #EDE9FE;
}

html, body, [data-testid="stAppViewContainer"] { background: var(--lv-bg) !important; }
.block-container { padding-top: 2rem; max-width: 820px; }

[data-testid="stSidebar"] { display: none; }

h1.lv-title {
  font-size: 1.9rem; font-weight: 700; color: var(--lv-text);
  margin: 0 0 .25rem 0; letter-spacing: -.015em;
}
.lv-subtitle { color: var(--lv-muted); margin: 0 0 1.25rem 0; font-size: .98rem; }

/* Bordered containers — st.container(border=True) */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 14px !important;
  border: 1px solid var(--lv-border) !important;
  background: var(--lv-card) !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
  padding: 0.65rem 1.25rem !important;
}

/* Feedback callouts */
.lv-feedback {
  border-radius: 12px;
  padding: .9rem 1.1rem;
  margin: .75rem 0 .25rem 0;
  border: 1px solid transparent;
  line-height: 1.5;
}
.lv-feedback h4 { margin: 0 0 .25rem 0; font-size: 1rem; font-weight: 600; }
.lv-feedback p  { margin: 0; color: var(--lv-text); font-size: .95rem; }
.lv-feedback code { background: rgba(15, 23, 42, .06); padding: .05rem .3rem; border-radius: 4px; }

.lv-success { background: var(--lv-success-soft); border-color: #A7F3D0; }
.lv-success h4 { color: var(--lv-success); }
.lv-warn    { background: var(--lv-warning-soft); border-color: #FDE68A; }
.lv-warn h4 { color: var(--lv-warning); }
.lv-err     { background: var(--lv-error-soft);   border-color: #FECACA; }
.lv-err h4  { color: var(--lv-error); }
.lv-hint    { background: #EFF6FF; border-color: #BFDBFE; }
.lv-hint h4 { color: var(--lv-primary); }
.lv-objective {
  background: var(--lv-accent-soft); border-color: #DDD6FE;
  margin-bottom: 1rem;
  margin-top: 0;
}
.lv-objective h4 { color: var(--lv-accent); }

.lv-pill {
  display: inline-block; font-size: .72rem; padding: .15rem .6rem; border-radius: 999px;
  background: var(--lv-primary-soft); color: var(--lv-primary); font-weight: 600;
  letter-spacing: .04em; text-transform: uppercase; margin-bottom: .35rem;
}
.lv-pill-warn { background: var(--lv-warning-soft); color: var(--lv-warning); }
.lv-pill-acc  { background: var(--lv-accent-soft);  color: var(--lv-accent); }
.lv-mini  { color: var(--lv-muted); font-size: .85rem; }
.lv-step-h { color: var(--lv-primary); font-weight: 600; font-size: .95rem; margin-top: .55rem; }

.lv-stats {
  display: flex; gap: 1.25rem; align-items: baseline;
  background: var(--lv-card); border: 1px solid var(--lv-border);
  border-radius: 12px; padding: .55rem 1rem; margin: 0 0 1rem 0;
}
.lv-stat { display: flex; flex-direction: column; line-height: 1.1; }
.lv-stat .v { font-size: 1.15rem; font-weight: 700; color: var(--lv-text); }
.lv-stat .k { font-size: .7rem; text-transform: uppercase; letter-spacing: .07em; color: var(--lv-muted); }

/* Tabs as the top-of-page nav */
button[data-baseweb="tab"] {
  font-size: 1rem !important; font-weight: 600 !important;
  padding-top: .75rem !important; padding-bottom: .75rem !important;
}

/* Primary / secondary buttons */
div.stButton > button[kind="primary"] {
  background: var(--lv-primary); border: 1px solid var(--lv-primary);
  color: white; font-weight: 600;
}
div.stButton > button[kind="primary"]:hover {
  background: var(--lv-primary-dark); border-color: var(--lv-primary-dark);
}
div.stButton > button[kind="secondary"] {
  background: white; color: var(--lv-text); border: 1px solid var(--lv-border);
  font-weight: 500;
}
div.stButton > button[kind="secondary"]:hover {
  border-color: var(--lv-primary); color: var(--lv-primary);
}

ul.lv-options { list-style: disc; padding-left: 1.25rem; margin: 0; color: var(--lv-text); }
ul.lv-options li { margin: .15rem 0; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# --- Domain types -------------------------------------------------------------

@dataclass(frozen=True)
class Problem:
    """One generated limit problem.

    The numerator is (x - x0). The denominator is x^2 + c x + b and factors
    as (x - x0)(x + offset), so the radicand cancels to 1/(x + offset).
    """
    a: int          # integer such that the limit equals 1/a
    x0: int         # limit point
    offset: int     # surviving factor: (x + offset). offset = a^2 - x0.

    @property
    def c(self) -> int:
        return self.offset - self.x0

    @property
    def b(self) -> int:
        return -self.x0 * self.offset

    @property
    def correct(self) -> sp.Rational:
        return sp.Rational(1, self.a)

    @property
    def correct_float(self) -> float:
        return 1.0 / self.a


def numerator_str(x0: int) -> str:
    """Render the numerator factor (x - x0) as a plain string."""
    if x0 > 0:
        return f"x - {x0}"
    return f"x + {-x0}"


def surviving_str(offset: int) -> str:
    """Render the surviving factor (x + offset) as a plain string."""
    if offset >= 0:
        return f"x + {offset}"
    return f"x - {-offset}"


def quadratic_str(c: int, b: int) -> str:
    """Render x^2 + c x + b with proper signs (no '+ -' artifacts)."""
    parts = ["x²"]
    if c == 1:
        parts.append("+ x")
    elif c == -1:
        parts.append("- x")
    elif c > 0:
        parts.append(f"+ {c}x")
    elif c < 0:
        parts.append(f"- {-c}x")
    if b > 0:
        parts.append(f"+ {b}")
    elif b < 0:
        parts.append(f"- {-b}")
    return " ".join(parts)


def quadratic_latex(c: int, b: int) -> str:
    """LaTeX version of the quadratic for st.latex."""
    parts = ["x^{2}"]
    if c == 1:
        parts.append("+ x")
    elif c == -1:
        parts.append("- x")
    elif c > 0:
        parts.append(f"+ {c}x")
    elif c < 0:
        parts.append(f"- {-c}x")
    if b > 0:
        parts.append(f"+ {b}")
    elif b < 0:
        parts.append(f"- {-b}")
    return " ".join(parts)


def problem_latex(p: Problem) -> str:
    num = numerator_str(p.x0)
    denom = quadratic_latex(p.c, p.b)
    return rf"\lim_{{x \to {p.x0}}}\; \sqrt{{\,\dfrac{{{num}}}{{{denom}}}\,}}"


# --- Problem generation -------------------------------------------------------

def make_problem(difficulty: str,
                 avoid: Optional[Tuple[int, int]] = None) -> Problem:
    """Generate a new problem, avoiding the given (a, x0) pair when possible."""
    a_min, a_max = DIFFICULTIES[difficulty]
    for _ in range(60):
        a = random.randint(a_min, a_max)
        x0 = -1
        if (a, x0) != avoid:
            return Problem(a=a, x0=x0, offset=a * a - x0)
    return Problem(a=a, x0=x0, offset=a * a - x0)


# --- Answer parsing and diagnosis --------------------------------------------

def parse_answer(text: str) -> Optional[float]:
    """Return a finite float for a fraction/decimal/sqrt expression, else None."""
    text = text.strip()
    if not text:
        return None
    try:
        expr = sp.sympify(text, rational=True)
    except (sp.SympifyError, SyntaxError, TypeError, ValueError):
        return None
    if getattr(expr, "free_symbols", set()):
        return None
    try:
        val = float(expr.evalf())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(val):
        return None
    return val


def is_correct(val: float, p: Problem) -> bool:
    return abs(val - p.correct_float) < 1e-4


def diagnose(val: float, p: Problem) -> str:
    """Map a wrong numeric answer to the most likely conceptual mistake."""
    target = p.correct_float
    candidates = [
        ("missed_sqrt",       1.0 / (p.a * p.a)),
        ("sign",              -target),
        ("direct_sub",        0.0),
        ("cancelled_too_much", 1.0),
        ("reciprocal",        float(p.a)),
    ]
    if p.a > 1:
        candidates.append(("factor", 1.0 / math.sqrt(p.a * p.a - 1)))
    for label, t in candidates:
        if abs(val - t) < 1e-3:
            return label
    if abs(val - target) < max(0.005, 0.05 * target):
        return "off"
    return "unknown"


# --- Feedback messages --------------------------------------------------------

def feedback_for(kind: str, p: Problem) -> Tuple[str, str]:
    """Return (headline, html_body) for a diagnosed mistake."""
    a, b, x0 = p.a, p.b, p.x0
    a_sq = a * a
    num = numerator_str(x0)
    surv = surviving_str(p.offset)

    if kind == "missed_sqrt":
        return (
            "So close! One step short.",
            f"The value <code>1/{a_sq}</code> is what sits <em>inside</em> the "
            f"radical. The final step is <code>sqrt(1/{a_sq}) = 1/{a}</code>.",
        )
    if kind == "sign":
        return (
            "Almost — check the sign.",
            f"Substituting <code>x = {x0}</code> into <code>{surv}</code> gives "
            f"<code>{x0 + p.offset}</code>, a positive number, so the limit is "
            f"positive too.",
        )
    if kind == "direct_sub":
        return (
            "Substitution returns 0/0, not 0.",
            f"Both the numerator and denominator vanish at <code>x = {x0}</code>, "
            f"so the expression is indeterminate. Factor the denominator, cancel "
            f"<code>({num})</code>, <em>then</em> substitute.",
        )
    if kind == "factor":
        return (
            "Check the factoring of the denominator.",
            f"<code>{quadratic_str(p.c, b)}</code> factors as "
            f"<code>({num})({surv})</code>. The two roots multiply to "
            f"<code>{b}</code>, which forces the second factor to be "
            f"<code>({surv})</code>.",
        )
    if kind == "cancelled_too_much":
        return (
            "One factor cancels — the other survives.",
            f"After cancelling <code>({num})</code>, an <code>({surv})</code> "
            f"factor still sits in the denominator. Substitute <code>x = {x0}</code> "
            f"into <code>({surv})</code> to finish — do not drop the surviving factor.",
        )
    if kind == "reciprocal":
        return (
            "Looks like the fraction got flipped.",
            f"The surviving <code>({surv})</code> stays in the <em>denominator</em>, "
            f"so the answer is <code>1/{a}</code>, not <code>{a}</code>.",
        )
    if kind == "off":
        return (
            "Very close — a decimal lost precision.",
            f"The exact value is <code>1/{a}</code> &asymp; "
            f"<code>{1 / a:.5f}</code>. Try entering the fraction <code>1/{a}</code>.",
        )
    return (
        "Try again!",
        f"Walk the steps in order: substitute <code>x = {x0}</code> &rarr; factor "
        f"&rarr; cancel <code>({num})</code> &rarr; substitute again &rarr; take "
        f"the square root.",
    )


def hint_for(level: int, p: Problem) -> Tuple[str, str]:
    """Progressive hint. Level 1 names the trap, level 2 does the factoring,
    level 3 reveals the answer."""
    num = numerator_str(p.x0)
    surv = surviving_str(p.offset)
    a_sq = p.a * p.a

    if level <= 1:
        return (
            "Hint 1 of 3 — start by substituting.",
            f"Substitute <code>x = {p.x0}</code>: the numerator <code>{num}</code> "
            f"becomes 0, and the denominator <code>{quadratic_str(p.c, p.b)}</code> "
            f"also becomes 0. That is <code>0/0</code> — indeterminate. The presence "
            f"of <code>({num})</code> in the numerator is the clue: the denominator "
            f"must share that factor.",
        )
    if level == 2:
        return (
            "Hint 2 of 3 — factor the denominator.",
            f"Because <code>x = {p.x0}</code> is a root of the denominator, "
            f"<code>({num})</code> divides cleanly. The two roots multiply to give "
            f"the constant term <code>{p.b}</code>, which forces the other factor to "
            f"be <code>({surv})</code>. Cancelling <code>({num})</code> leaves "
            f"<code>sqrt(1 / ({surv}))</code>.",
        )
    return (
        f"Hint 3 of 3 — finish the substitution. The answer is 1/{p.a}.",
        f"Substitute <code>x = {p.x0}</code> into <code>1 / ({surv})</code> to get "
        f"<code>1 / ({p.x0} + {p.offset})</code> = <code>1 / {a_sq}</code>. Take "
        f"the square root: <code>sqrt(1/{a_sq}) = 1/{p.a}</code>. Try entering "
        f"<code>1/{p.a}</code>.",
    )


# --- Step-by-step renderer ----------------------------------------------------

def render_steps(p: Problem, slip_step: Optional[int] = None) -> None:
    num = numerator_str(p.x0)
    surv = surviving_str(p.offset)

    def header(n: int, title: str) -> str:
        marker = " &larr; the step to watch" if n == slip_step else ""
        return f"<div class='lv-step-h'>Step {n} &middot; {title}{marker}</div>"

    with st.container(border=True):
        st.markdown("<span class='lv-pill'>Step-by-step</span>", unsafe_allow_html=True)

        st.markdown(header(1, "Direct substitution"), unsafe_allow_html=True)
        st.markdown(
            f"At $x = {p.x0}$, the numerator $({num})$ equals $0$ "
            f"and the denominator ${quadratic_str(p.c, p.b)}$ also equals "
            f"$0$, so the radicand is $\\frac{{0}}{{0}}$ — indeterminate."
        )

        st.markdown(header(2, "Factor the denominator"), unsafe_allow_html=True)
        st.markdown(
            f"Since $x = {p.x0}$ is a root of the denominator, "
            f"$({num})$ is a factor. The two roots multiply to give the "
            f"constant term ${p.b}$, so the other factor is $({surv})$."
        )
        st.latex(rf"{quadratic_latex(p.c, p.b)} \;=\; ({num})({surv})")

        st.markdown(header(3, "Cancel and simplify"), unsafe_allow_html=True)
        st.latex(
            rf"\sqrt{{\dfrac{{{num}}}{{({num})({surv})}}}} \;=\; "
            rf"\sqrt{{\dfrac{{1}}{{{surv}}}}}"
        )

        st.markdown(header(4, "Substitute, then take the square root"),
                    unsafe_allow_html=True)
        st.latex(
            rf"\sqrt{{\dfrac{{1}}{{{p.x0} + {p.offset}}}}} \;=\; "
            rf"\sqrt{{\dfrac{{1}}{{{p.a * p.a}}}}} \;=\; \dfrac{{1}}{{{p.a}}}"
        )

        st.latex(rf"\boxed{{\,\dfrac{{1}}{{{p.a}}}\,}}")


# --- Session state ------------------------------------------------------------

PRACTICE_PAGES = ("Practice", "Homework")

PROBLEM_KEYS = (
    "problem", "attempts", "hint_level", "mistakes",
    "answered_correctly", "explanation_shown", "counted_attempt",
    "last_result", "just_advanced_from", "input_key",
)


def pk(page: str, key: str) -> str:
    return f"{page}__{key}"


def init_state() -> None:
    ss = st.session_state
    # Shared session-wide stats.
    ss.setdefault("solved", 0)
    ss.setdefault("attempted_problems", 0)
    ss.setdefault("streak", 0)
    ss.setdefault("best_streak", 0)
    ss.setdefault("error_history", [])
    # Lesson MC state.
    for i in range(len(MC_QUESTIONS)):
        ss.setdefault(f"mc_{i}_submitted", False)
        ss.setdefault(f"mc_{i}_correct", False)
    # Per-page problem state.
    for page in PRACTICE_PAGES:
        ss.setdefault(pk(page, "problem"), make_problem(page))
        ss.setdefault(pk(page, "attempts"), 0)
        ss.setdefault(pk(page, "hint_level"), 0)
        ss.setdefault(pk(page, "mistakes"), [])
        ss.setdefault(pk(page, "answered_correctly"), False)
        ss.setdefault(pk(page, "explanation_shown"), False)
        ss.setdefault(pk(page, "counted_attempt"), False)
        ss.setdefault(pk(page, "last_result"), None)
        ss.setdefault(pk(page, "just_advanced_from"), None)
        ss.setdefault(pk(page, "input_key"), 0)


def next_problem(page: str, carry_over: Optional[str] = None) -> None:
    ss = st.session_state
    prev = ss[pk(page, "problem")]
    ss[pk(page, "problem")] = make_problem(page, avoid=(prev.a, prev.x0))
    ss[pk(page, "attempts")] = 0
    ss[pk(page, "hint_level")] = 0
    ss[pk(page, "mistakes")] = []
    ss[pk(page, "answered_correctly")] = False
    ss[pk(page, "explanation_shown")] = False
    ss[pk(page, "counted_attempt")] = False
    ss[pk(page, "last_result")] = None
    ss[pk(page, "just_advanced_from")] = carry_over
    ss[pk(page, "input_key")] += 1


# --- Renderers: shared widgets -----------------------------------------------

def render_objective() -> None:
    st.markdown(
        "<div class='lv-feedback lv-objective'>"
        "<h4>Learning objective</h4>"
        "<p>Evaluate square-root limits of the indeterminate form <strong>0/0</strong> "
        "by factoring the denominator, cancelling the shared root, and applying "
        "the square root as the final step.</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_stats_strip() -> None:
    ss = st.session_state
    st.markdown(
        f"<div class='lv-stats'>"
        f"<div class='lv-stat'><span class='v'>{ss['solved']}</span>"
        f"<span class='k'>Solved</span></div>"
        f"<div class='lv-stat'><span class='v'>{ss['streak']}</span>"
        f"<span class='k'>Streak</span></div>"
        f"<div class='lv-stat'><span class='v'>{ss['best_streak']}</span>"
        f"<span class='k'>Best</span></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_watch_out_for() -> None:
    history = st.session_state["error_history"]
    if not history:
        return
    label_id, count = Counter(history).most_common(1)[0]
    if count < 2:
        return
    label = ERROR_LABELS.get(label_id, "a recurring slip")
    st.markdown(
        f"<div class='lv-feedback lv-warn'>"
        f"<h4>Watch out for</h4>"
        f"<p>This slip has come up <strong>{count}&times;</strong> this session: "
        f"<em>{label}</em>. Read the next problem with that step in mind.</p>"
        f"</div>",
        unsafe_allow_html=True,
    )


# --- Renderers: Lesson tab ----------------------------------------------------

def render_lesson() -> None:
    st.markdown("<h1 class='lv-title'>Solving limits with radicals</h1>",
                unsafe_allow_html=True)
    st.markdown(
        "<div class='lv-subtitle'>Calculus I &middot; "
        "Indeterminate forms with a radical<div>",
        unsafe_allow_html=True,
    )

    render_objective()

    # --- Intro / framing (real-world connection) ---
    st.markdown("### Why this matters")
    st.markdown(
        "Limits are the foundation of calculus — they describe what a function "
        "approaches as the input gets close to a point. In real applications like "
        "computing velocity or reaction rates, plugging in directly often gives "
        r"$\frac{0}{0}$, which is meaningless on its own. This lesson covers a "
        r"specific pattern: how to resolve the $\frac{0}{0}$ when a square root "
        "is involved."
    )

    # --- How to Solve, with a guided worked example ---
    st.markdown("### How to solve")
    st.markdown(
        """
    1. **Substitute** $x = x_0$ into the radicand. When the result is $\\frac{0}{0}$, the
       expression is indeterminate — keep going.
    2. **Factor** the denominator. Because the numerator vanishes at $x_0$,
       $(x - x_0)$ must also divide the denominator.
    3. **Cancel** the shared $(x - x_0)$ factor. The removable discontinuity is
       gone, and what remains is a clean rational expression.
    4. **Substitute** $x = x_0$ into the simplified expression, then **take the
       square root**. The square root is the final step — pulling the root early
       skips the algebra that resolves the $\\frac{0}{0}$.
        """
    )

    st.markdown("**Guided example:**")
    example = Problem(a=3, x0=-1, offset=10)  # x^2 + 11x + 10 = (x+1)(x+10)
    st.latex(problem_latex(example))
    render_steps(example)

    # --- Participation Activity ---
    st.markdown("### Participation activity")
    st.markdown(
        "<div class='lv-mini'>Concept checks.</div>",
        unsafe_allow_html=True,
    )

    for i, q in enumerate(MC_QUESTIONS):
        render_mc_question(i, q)

    if all(st.session_state[f"mc_{i}_correct"] for i in range(len(MC_QUESTIONS))):
        st.markdown(
            "<div class='lv-feedback lv-success'>"
            "<h4>Lesson complete</h4>"
            "<p>Great work! Move on to the <strong>Practice</strong> "
            "tab to try problems on your own, or jump to <strong>Homework</strong>.</p>"
            "</div>",
            unsafe_allow_html=True,
        )


def render_mc_question(i: int, q: dict) -> None:
    with st.container(border=True):
        st.markdown(f"<span class='lv-pill lv-pill-acc'>Question {i + 1}</span>",
                    unsafe_allow_html=True)
        st.markdown(f"**{q['prompt']}**")

        submitted_key = f"mc_{i}_submitted"
        correct_key   = f"mc_{i}_correct"
        radio_key     = f"mc_{i}_radio"

        choice = st.radio(
            "Select one",
            options=list(range(len(q["options"]))),
            format_func=lambda j: q["options"][j],
            key=radio_key,
            label_visibility="collapsed",
            disabled=st.session_state[submitted_key],
        )

        cols = st.columns([1, 3])
        with cols[0]:
            if not st.session_state[submitted_key]:
                if st.button("Submit", key=f"mc_{i}_submit", type="primary",
                             use_container_width=True):
                    st.session_state[submitted_key] = True
                    st.session_state[correct_key] = (choice == q["correct"])
                    st.session_state[f"mc_{i}_choice"] = choice   # store chosen index
                    st.rerun()
            else:
                if st.button("Try again", key=f"mc_{i}_reset", type="secondary",
                             use_container_width=True):
                    st.session_state[submitted_key] = False
                    st.session_state[correct_key]   = False
                    st.rerun()

        if st.session_state[submitted_key]:
            if st.session_state[correct_key]:
                st.markdown(
                    f"<div class='lv-feedback lv-success'>"
                    f"<h4>Correct.</h4><p>{q['explain']}</p></div>",
                    unsafe_allow_html=True,
                )
            else:
                correct_text  = q["options"][q["correct"]]
                chosen_index  = st.session_state.get(f"mc_{i}_choice")
                wrong_explain = q.get("wrong_explains", {}).get(chosen_index, "")
                wrong_block   = (
                    f"<p><em>{wrong_explain}</em></p>" if wrong_explain else ""
                )
                st.markdown(
                    f"<div class='lv-feedback lv-warn'>"
                    f"<h4>Not quite.</h4>"
                    f"{wrong_block}"
                    f"<p>The correct choice is: <em>{correct_text}</em><br>"
                    f"{q['explain']}</p></div>",
                    unsafe_allow_html=True,
                )


# --- Renderers: Practice / Review tabs ---------------------------------------

def render_practice(page: str) -> None:
    ss = st.session_state
    p: Problem = ss[pk(page, "problem")]

    label = "Practice" if page == "Practice" else "Homework"
    st.markdown(f"<h1 class='lv-title'>{label}</h1>", unsafe_allow_html=True)
    if page == "Practice":
        st.markdown(
            "<div class='lv-subtitle'>Practice limit problems at x &rarr; -1.</div>",
            unsafe_allow_html=True,
        )
    render_objective()
    render_stats_strip()
    render_watch_out_for()

    if ss[pk(page, "just_advanced_from")]:
        carry_label = ERROR_LABELS.get(ss[pk(page, "just_advanced_from")], "")
        if carry_label:
            st.markdown(
                f"<div class='lv-feedback lv-hint'>"
                f"<h4>Picking up where you left off</h4>"
                f"<p>Last problem: <em>{carry_label}.</em> The same trap can show "
                f"up here — take the steps in order and watch that moment.</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # --- Problem card ---
    pill_class = "lv-pill-warn" if page == "Homework" else ""
    with st.container(border=True):
        st.markdown(
            f"<span class='lv-pill {pill_class}'>{page} &middot; Problem</span>",
            unsafe_allow_html=True,
        )
        st.markdown("**Solve the limit:**")
        st.latex(problem_latex(p))

    # --- Answer card ---
    with st.container(border=True):
        st.markdown("**Your answer**")
        user_text = st.text_input(
            "Enter the value of the limit",
            placeholder="Ex:  1/3   or   0.3333   or   sqrt(1/9)",
            label_visibility="collapsed",
            disabled=ss[pk(page, "answered_correctly")]
                  or ss[pk(page, "explanation_shown")],
            key=f"{page}_answer_{ss[pk(page, 'input_key')]}",
        )

        b1, b2 = st.columns(2)
        with b1:
            hint_clicked = st.button(
                "Show a hint",
                key=f"{page}_hint_btn",
                type="secondary",
                use_container_width=True,
                disabled=ss[pk(page, "answered_correctly")]
                      or ss[pk(page, "explanation_shown")]
                      or ss[pk(page, "hint_level")] >= 3,
            )
        with b2:
            submit_clicked = st.button(
                "Check answer",
                key=f"{page}_check_btn",
                type="primary",
                use_container_width=True,
                disabled=ss[pk(page, "answered_correctly")]
                      or ss[pk(page, "explanation_shown")],
            )

    # --- Handlers (do all state mutation first, then render below) ---
    if hint_clicked:
        ss[pk(page, "hint_level")] = min(3, ss[pk(page, "hint_level")] + 1)
        st.rerun()

    if submit_clicked:
        handle_submit(page, p, user_text)
        st.rerun()

    # --- Render hint if active ---
    if (ss[pk(page, "hint_level")] > 0
            and not ss[pk(page, "answered_correctly")]
            and not ss[pk(page, "explanation_shown")]):
        head, body = hint_for(ss[pk(page, "hint_level")], p)
        st.markdown(
            f"<div class='lv-feedback lv-hint'><h4>{head}</h4><p>{body}</p></div>",
            unsafe_allow_html=True,
        )

    # --- Render last result ---
    result = ss[pk(page, "last_result")]
    if result is not None:
        render_result_callout(result, p)

    # --- Step-by-step (when correct, show explanation clicked, or final wrong) ---
    if ss[pk(page, "explanation_shown")]:
        slip = ss[pk(page, "mistakes")][-1] if ss[pk(page, "mistakes")] else None
        render_steps(p, slip_step=ERROR_STEP.get(slip))

    # --- Action row: Show explanation / Next problem ---
    c1, c2 = st.columns(2)
    with c1:
        show_expl_clicked = st.button(
            "Show explanation",
            key=f"{page}_show_expl_btn",
            type="secondary",
            use_container_width=True,
            disabled=ss[pk(page, "answered_correctly")]
                  or ss[pk(page, "explanation_shown")],
            help="Reveal the worked solution without credit, then move on.",
        )
    with c2:
        next_clicked = st.button(
            "Next problem  →",
            key=f"{page}_next_btn",
            type="primary",
            use_container_width=True,
        )

    if show_expl_clicked:
        if not ss[pk(page, "counted_attempt")]:
            ss["attempted_problems"] += 1
            ss[pk(page, "counted_attempt")] = True
        ss["streak"] = 0
        ss[pk(page, "explanation_shown")] = True
        ss[pk(page, "last_result")] = ("explanation", None, "")
        st.rerun()

    if next_clicked:
        carry = (ss[pk(page, "mistakes")][-1]
                 if ss[pk(page, "mistakes")]
                 and not ss[pk(page, "answered_correctly")]
                 else None)
        if not ss[pk(page, "answered_correctly")] \
                and not ss[pk(page, "counted_attempt")]:
            ss["attempted_problems"] += 1
            ss["streak"] = 0
        next_problem(page, carry_over=carry)
        st.rerun()


def handle_submit(page: str, p: Problem, text: str) -> None:
    ss = st.session_state
    val = parse_answer(text)
    if val is None:
        ss[pk(page, "last_result")] = ("invalid", None, text)
        return

    if not ss[pk(page, "counted_attempt")]:
        ss["attempted_problems"] += 1
        ss[pk(page, "counted_attempt")] = True
    ss[pk(page, "attempts")] += 1

    if is_correct(val, p):
        ss[pk(page, "answered_correctly")] = True
        ss[pk(page, "explanation_shown")] = True
        ss["solved"] += 1
        ss["streak"] += 1
        ss["best_streak"] = max(ss["best_streak"], ss["streak"])
        ss[pk(page, "last_result")] = ("correct", None, text)
        return

    kind = diagnose(val, p)
    ss[pk(page, "mistakes")].append(kind)
    ss["error_history"].append(kind)
    ss["streak"] = 0
    # Auto-advance the hint level on each wrong submission.
    ss[pk(page, "hint_level")] = min(3, max(ss[pk(page, "hint_level")],
                                            ss[pk(page, "attempts")]))
    if ss[pk(page, "attempts")] >= 2:
        ss[pk(page, "explanation_shown")] = True
        ss[pk(page, "last_result")] = ("wrong_final", kind, text)
    else:
        ss[pk(page, "last_result")] = ("wrong", kind, text)


def render_result_callout(result: Tuple[str, Optional[str], str], p: Problem) -> None:
    status, kind, _raw = result
    if status == "invalid":
        st.markdown(
            "<div class='lv-feedback lv-warn'>"
            "<h4>Invalid input</h4>"
            "<p>Enter a fraction (<code>1/3</code>), a decimal "
            "(<code>0.3333</code>), or an expression like "
            "<code>sqrt(1/9)</code>. No variables.</p></div>",
            unsafe_allow_html=True,
        )
    elif status == "correct":
        st.markdown(
            f"<div class='lv-feedback lv-success'>"
            f"<h4>Correct &mdash; the limit is 1/{p.a}.</h4>"
            f"<p>Nice work. The following walkthrough shows every step.</p></div>",
            unsafe_allow_html=True,
        )
        if st.session_state["streak"] > 0 and st.session_state["streak"] % 3 == 0:
            st.balloons()
            st.markdown(
                f"<div class='lv-feedback lv-success'>"
                f"<h4>{st.session_state['streak']} in a row.</h4>"
                f"<p>That is a serious streak! Awesome job.</p></div>",
                unsafe_allow_html=True,
            )
            if st.session_state["streak"] == 3:
                st.markdown(
                    "<div class='lv-feedback lv-hint'>"
                    "<h4>Ready for a challenge?</h4>"
                    "<p>Head to the <strong>Homework</strong> tab for harder problems.</p>"
                    "</div>",
                    unsafe_allow_html=True,
                )
    elif status == "wrong":
        head, body = feedback_for(kind, p)
        st.markdown(
            f"<div class='lv-feedback lv-warn'><h4>{head}</h4><p>{body}</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='lv-mini'>One more attempt before the solution is "
            "given.</div>",
            unsafe_allow_html=True,
        )
    elif status == "wrong_final":
        head, body = feedback_for(kind, p)
        st.markdown(
            f"<div class='lv-feedback lv-err'>"
            f"<h4>The correct answer is 1/{p.a}.</h4>"
            f"<p><strong>{head}</strong> {body}</p></div>",
            unsafe_allow_html=True,
        )
    elif status == "explanation":
        st.markdown(
            f"<div class='lv-feedback lv-hint'>"
            f"<h4>Read through the following steps.</h4>"
            f"<p>Try again on the next problem.</p></div>",
            unsafe_allow_html=True,
        )


# --- Main ---------------------------------------------------------------------

init_state()

tab_lesson, tab_practice, tab_review = st.tabs(["Lesson", "Practice", "Homework"])

with tab_lesson:
    render_lesson()

with tab_practice:
    render_practice("Practice")

with tab_review:
    render_practice("Homework")
