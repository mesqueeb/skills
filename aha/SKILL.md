---
name: aha
description: Debate whether a specific piece of code earns its place as a separate function/variable or reads better inlined — steelmanning the abstraction before any verdict, defending keeps in full, applying clear inlines directly, and proposing re-cuts for confirmation. Named for "Avoid Hasty Abstractions." Use when the user runs /aha, points at a function/method/computed-property/variable and asks whether it should be extracted or inlined, or wonders if something is over-abstracted, a premature helper, or a "wrong abstraction."
---

# AHA — extract or inline?

The user points at one or more things — a function, method, computed property, or a named variable — and you argue whether each earns its separateness or reads better inline.

Run the steelman below as if you had no prior — don't presume the answer. Two rules keep it honest: the **abstraction carries the burden of proof** (unproven indirection is a liability, not a neutral choice), and **ties break toward inline** because of a real asymmetry — a wrong inline is cheap to re-extract, but a wrong extract is sticky (callers couple to the seam, then bolt on params until it's the "wrong abstraction"). A defense that genuinely holds keeps the abstraction; a defense that fails inlines it; a real tie breaks toward inline.

## First: read it in context

Input is a symbol or location (`/aha resizeCollisionToChildren`, `/aha File.swift:210`) or a pasted snippet. **Read the surrounding file, not just the target** — the best findings only exist in context (a duplicate copy elsewhere, a better seam hiding inside the target). If given only a snippet, say what context you're missing.

## Steelman first — the four lenses

Before any verdict, genuinely **defend keeping it AND defend inlining it.** Find the strongest real case for the abstraction, then weigh it against these:

**1. Clarity.** A function is a real **black box** only when its interface — name, signature, ideally doc comment — _honestly conveys what it represents_, so you can skip the body. You can't confirm purity without reading, so the real trust is that the name doesn't lie by omission. Purity is what earns that: a pure function (output from inputs, no side effects) can be fully captured by a name; a side-effecting helper (mutations, `set`/`remove`, I/O) can't — its name hides the effects, so you must open it to call it safely. That's a **shallow module** (Ousterhout), not a black box: the extraction buys no real abstraction, so it's only justified when it declutters a genuinely long caller — and then call it what it is: chunking, not encapsulation. Depth is not line count: a clearly-named pure 3-liner is a box; a 3-line mutator whose name omits what it touches is not.

**2. Check the seam is on the purity line.** Sometimes the answer is neither keep nor inline but **re-cut**: a helper that welds a _computation_ to its _side effects_ can't have an honest name. Split at the purity line — the pure computation becomes a real black box (trustable, unit-testable); the effects stay visible and inline where a reader expects mutations. But a re-cut is itself an extraction, so the pure core must earn it under the other lenses on its own — genuinely fiddly computation worth trusting by name and testing in isolation. If the computation is simple, plain inline still wins, especially for a first version with a single caller; don't let re-cut become a new hasty abstraction.

**3. Reuse is necessary, not sufficient.** Real reuse (2+ actual callers, not speculative — that's YAGNI) is a point in favour, not a verdict. Sometimes **a copy beats a shared function** even at 3+ sites: if callers differ subtly, merging them forces a param/conditional per caller — the exact mechanism of the wrong abstraction. When you find duplication, ask whether the copies _want_ to be one thing or are genuinely diverging.

**4. Shallow-extraction tells (point toward inline).** Interface as complex as the body (5 params for a 1-line body) · name restates the code (`addOne(x)` → `x + 1`) · single caller + speculative reuse · only makes sense given the caller's exact setup (temporal coupling) · fragments a flow you'd otherwise read as one linear block.

Variables get the same test as functions: does the binding **earn** the state it adds (names a non-obvious value, reused enough that inlining would obscure), or is it one more thing to track that reads clearer inlined at its single use?

## Verdict and action

For each target, state the **verdict** (keep / inline / re-cut) and **the tradeoff you're accepting**, in a line — not a rubber stamp. Then act by where it landed:

- **Keep** → **this is the discussion, not a footnote.** When the abstraction genuinely earns its place, laying out that defense _is_ the payload — make the full case and invite pushback. A keep is where the conversation starts.
- **Inline** → **just do it and report it**, even for a target you set out defending. But only on an **honest** failure to defend, never a cave: don't unwrap because the user leaned that way or to seem decisive. If the defense holds, keep it and say so.
- **Re-cut / extract** → **present, then confirm.** Before proposing one, ask **where it would live**: a good extraction names a concept the codebase already talks about — the word was missing, not the concept — so it has an obvious home (an existing extension, an existing helpers file, right next to its caller). If the only home is a junk drawer, or the name is a phrase only this one caller would ever say, the verdict is inline: helpers should accumulate far slower than the domain code around them. When it clears that bar, show the concrete split and be open for user input on placement and naming alongside your suggestions.

Given several names at once, run each independently and act per this policy: end with the honest inlines **already applied**, and spend your words on the keeps you're standing behind and anything awaiting the user's call.
