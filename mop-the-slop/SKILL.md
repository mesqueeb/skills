---
name: mop-the-slop
description: Review a target set of code through independent "lenses" — comment quality, dead code, idioms/conventions, error handling, clarity, test quality, spec fidelity — each run by its own read-only sub-agent in repeated fresh rounds until findings converge, with the main agent applying fixes autonomously. Use when the user wants to review code from a PR, the working tree, staged changes, code an agent just wrote, or code referenced in the conversation.
---

# Mop the Slop

You orchestrate a code review. You do not review the code yourself — you dispatch one read-only sub-agent per **lens** (a single review dimension), collect their findings, and apply the fixes. The lenses do the looking; you hold the context and make every edit.

This runs **autonomously.** Don't ask the user "okay to apply?" — just apply the fixes you're confident in and report what you did, the way you'd handle drive-by fixes. The user reaches for this skill to *not* get involved; respect that. (It's also called as a sub-step from other skills — e.g. close-the-loop saying "now run mop-the-slop" — which must not stall on a prompt.) When you're *not* confident a fix is right, you don't block on the user either — you surface it in the final report instead of applying it.

The sub-agents stay **independent and context-free.** You never tell a sub-agent what an earlier round decided — that would make it defer to you instead of reviewing the code cold, and a contaminated reviewer is worthless. The memory lives with *you*: you keep a private ledger of what you applied and what you consciously declined, and you use it to tell genuinely new findings apart from re-flags of things you've already settled.

## 1. Resolve the target code

Figure out *what code* to review. The user names a source, or you infer it from the conversation:

- **A PR** → `gh pr diff <n>` (or the branch diff against the base).
- **Staged changes** → `git diff --staged`.
- **What we just worked on** → the working-tree diff (`git diff`) plus whatever was edited in this conversation.
- **Code an agent just wrote** → the files/hunks that agent reported.
- **Code referenced in the conversation** → the specific files or ranges discussed.

Resolve it to a concrete list of files and line ranges before dispatching. If it's ambiguous which source the user means, ask — don't guess and review the wrong thing.

Filter out what isn't worth reviewing: binary files, generated/vendored output, lockfiles, build artifacts — anything not hand-written (`linguist-generated`, regenerated assets, `.usdz`, etc.). If after filtering the target is empty, there's nothing to review — say so and stop before dispatching anything.

Also grab the **spec** if one exists — the ticket, request, or plan this code was meant to satisfy (from the conversation, a linked issue, a PRD). The spec-fidelity lens needs it; without one, that lens is skipped.

## 2. Pick the lenses

Each lens lives in `lenses/` and is a self-contained directive a sub-agent receives. Lenses available:

- **code-comments** (`lenses/code-comments.md`) — comment quality, subtractive.
- **dead-code** (`lenses/dead-code.md`) — unused/unreachable code, debug leftovers.
- **idiom** (`lenses/idiom.md`) — matches house conventions and language idioms.
- **error-handling** (`lenses/error-handling.md`) — failure paths.
- **clarity** (`lenses/clarity.md`) — readability of added functions and logic.
- **test-quality** (`lenses/test-quality.md`) — runs only when the change touches tests.
- **spec-fidelity** (`lenses/spec-fidelity.md`) — runs only when a spec exists; receives it.

Run all **applicable** lenses (skip test-quality if no tests changed, spec-fidelity if no spec) unless the user asks for a specific one.

## 3. Run rounds until the lenses go quiet

The review is a loop. Each **round** is a fresh batch of sub-agents reviewing the *current* state of the code. You keep running rounds until a round comes back with nothing new.

**Every round spawns brand-new sub-agents** — never continue a previous round's sub-agent. A fresh sub-agent reads the code cold, with no attachment to earlier findings, so when one finds nothing it means the code itself is clean, not that a reviewer ran out of steam. Round 2 is new sub-agents, round 3 is new sub-agents, round 4 is new sub-agents, and so on.

A single round:

1. **Dispatch one sub-agent per applicable lens, in parallel** — use the Agent/Task sub-agent tool, one call per lens, all in a single message. **Don't read the lens files yourself** — give each sub-agent the **path** to its lens directive and tell it to read that file first. That keeps your own context lean (you only hold the ledger, findings, and code). For round 2 onward, **re-resolve the target first** (regenerate the diff / re-read the ranges) so sub-agents see the *current, post-edit* code — not the stale round-1 diff. Each sub-agent's prompt is *only*:
   - The path to its lens directive file (it reads the file itself).
   - The current resolved target code (the diff and/or file paths + ranges to read).

   Nothing about earlier rounds. The sub-agent reviews the current code cold. (The spec-fidelity lens additionally gets the spec — legitimate task context, not prior-round contamination.) Sub-agents are **read-only**: instruct them not to edit, and don't rely on edits from them — *you* make every change. Each returns a flat list of findings (each lens defines its own format — broadly `file:line — what — why`, sometimes with a suggested change; spec-fidelity may report `missing` instead of a line; no severity).

   If a lens sub-agent errors, times out, or returns unusable output, **re-dispatch it** (a couple of retries) — never let a failed lens silently count as "found nothing."

2. **Reconcile against your ledger.** Dedupe across lenses. When two lenses flag the **same location with different suggested fixes** (idiom wants a rewrite, clarity wants a rename on the same line), adjudicate them together as one decision — don't apply them independently, or the second edit fights the first. Then sort each finding:
   - **New** (not in your ledger) → decide it, one of three ways: **apply** the fix yourself (when you're confident it's right), **surface** it in the final report (real finding, but the fix is a judgment call you're not confident in — don't guess, don't block on the user), or **decline** it and record *why* in your ledger. When a lens flags that a fix **ripples beyond the reviewed code** (e.g. idiom marking a change that touches call sites), lean toward surface unless you're confident you can update every affected site. Lens sub-agents never write files; you make every edit. Apply edits one at a time, and re-locate each remaining edit against the current file before making it — earlier edits shift everything below them.
   - **Already declined** (a re-flag of something in your ledger) → ignore it by default. But notice the pattern: if independent fresh reviewers keep raising the same declined item round after round, treat that repetition as a serious signal and re-examine your own reasoning honestly — you may have been wrong.

3. **Decide whether to loop again.** If the round produced *any new* finding (applied, surfaced, or freshly declined), run another round so fresh sub-agents see the new state. If the round produced **nothing you hadn't already adjudicated** — only re-flags of items already in your ledger, or silence — you've converged. Stop.

   **Match re-flags by content, not line number.** After you apply a fix, lines shift, so a re-flag of a declined item arrives at a *different* `file:line` and often reworded. Key your ledger on a stable anchor — the symbol, the snippet, the comment text — and match on that. Treat a finding about code that a *prior round's own fix introduced* as already-adjudicated by default (bias to decline/surface), so you and the lenses don't ping-pong over each other's edits.

   **Hard cap: 3 rounds.** Stop after the third round even if not fully converged, and put whatever's still outstanding in the report. The cap is the runaway backstop; real convergence usually lands sooner.

## 4. Your ledger

The ledger is yours alone — never injected into a sub-agent's prompt. It holds:

- **Applied** — fixes already made (so when you see that issue gone, you know why).
- **Surfaced** — real findings you weren't confident enough to auto-fix and instead put in the report (a fresh round will re-flag them since they're unchanged; that's a re-flag, not new).
- **Declined, with reasoning** — findings you chose not to act on and why ("this comment explains a non-obvious workaround — it earns its place").

You use it purely to classify each incoming finding as new-or-settled. Independence is the whole design: the sub-agents never learn what you decided, so a comment that's genuinely bad gets flagged by every fresh reviewer — and that drumbeat, not an argument handed back to one agent, is what should move you to reconsider.

## 5. Verify, persist, report

**Verify.** Once the loop converges (or hits the round cap), run the project's build/test gate once — the repo's usual build/test command (some wrap it, e.g. a `./test.sh`; check the project's docs/CLAUDE.md). If a fix you applied broke it, **revert that fix and surface it** instead — never report success on broken code.

**Persist — match the state of the code you reviewed** (the source from step 1):

- Reviewing **unstaged working-tree changes**, or **a piece of existing/committed code** → leave your edits in the working tree, **unstaged**. Same state as what you reviewed; the user stages or commits later if they want.
- Reviewing **staged changes** → stage your edits too, so the cleanup travels with what's already staged. But stage **only the exact hunks you changed** — *never* `git add <file>` a whole file. Other agents may be editing the same files concurrently, and a whole-file add would sweep their unrelated work into the commit. Use hunk-level staging (`git add -p`, or stage specific line ranges) so only your own changes get staged.
- **Never commit.** If the user wants a commit, they'll say so.

**Report.** Tell the user what happened in a few lines: which lenses ran, how many rounds it took, what you changed (call out the higher-stakes edits explicitly — removed code, deleted or rewritten tests, behavior dropped as scope creep), what you reverted, and anything you surfaced or declined (with reasoning). End with an explicit bottom line a caller can act on: **converged clean**, or **converged with N findings still open** (surfaced/reverted). No approval step — just a summary of work already done.
