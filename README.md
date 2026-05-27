# Limit Practice

An interactive three-tab Streamlit module for evaluating square-root limits of
the indeterminate form **0/0**. Built for the Learnvia *Content Technical
Developer* exercise, with a student-first instructional structure modeled on
the zyBooks lesson → participation → practice rhythm.

Each generated problem has the form

$$\lim_{x \to x_0}\;\sqrt{\frac{x - x_0}{x^2 + cx + b}}$$

where the integer coefficients are chosen so the denominator factors as
$(x - x_0)(x + s)$, the radicand cancels to $1/(x + s)$, and the simplified
limit equals **1/a** for some integer *a*.

## Structure

| Tab          | Audience                  | What's there                                                                                          |
|--------------|---------------------------|-------------------------------------------------------------------------------------------------------|
| **Lesson**   | First exposure            | Why-it-matters framing, the four-step solving rhythm, a fully worked guided example, two MCQs.        |
| **Practice** | Building fluency          | Standard difficulty (*a* ∈ 2..9), the canonical $x \to -1$ form.                                       |
| **Review**   | Stretch and consolidation | Challenge difficulty (*a* ∈ 10..12) with **three randomized variants** that shift the limit point and surviving factor. |

## Pedagogical features

- **Progressive hints.** Three escalating hint levels — name the trap, do the
  factoring, then reveal the answer. The hint level also auto-advances on each
  wrong submission so struggling students get more scaffolding without asking.
- **Diagnostic feedback.** Wrong answers are mapped to the most likely
  conceptual slip (missed sqrt, sign error, factoring error, reciprocal flip,
  rounding) and the relevant step is highlighted in the worked solution.
- **"Show explanation" (no credit).** Lets students study the full worked
  solution before moving on, without inflating their solved count.
- **Carry-over coaching.** When the student missed a step on the previous
  problem, the next problem opens with a callout to watch that specific step.
- **Session-wide trends.** A "Watch out for" callout surfaces the most
  recurring slip after it occurs twice in a session.

## Mathematical parsing

Answers are parsed with SymPy and accept any of:

- fractions: `1/3`
- decimals: `0.3333`
- expressions: `sqrt(1/9)`, `(1/2)^0`

Exact rational comparison runs first; a 1e-4 float tolerance covers truncated
decimal entries. Floating-point drift never wrongly flags a correct response.

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlitAppUpdate.py
```

The app opens at `http://localhost:8501`. No external services or API keys
are required.

## Deployment

Drop the repo into [Streamlit Community Cloud](https://streamlit.io/cloud),
point the entry file at `streamlitAppUpdate.py`, and ship.

## Files

| File                      | Purpose                                                 |
|---------------------------|---------------------------------------------------------|
| `streamlitAppUpdate.py`   | The Streamlit application (single file, ~600 lines).    |
| `requirements.txt`        | Minimum runtime dependencies.                           |
| `README.md`               | This file.                                              |
