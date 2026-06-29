---
name: mop-the-slop
description: Review a target set of code through independent "lenses" — comment quality, dead code, idioms/conventions, error handling, clarity, test quality, spec fidelity, cohesion/placement — each run by its own read-only sub-agent in repeated fresh rounds until findings converge, with the main agent applying fixes autonomously. Use when the user wants to review code from a PR, the working tree, staged changes, code an agent just wrote, or code referenced in the conversation.
---

# Mop the Slop

You orchestrate a code review. You do not review the code yourself — you dispatch one read-only sub-agent per **lens** (a single review dimension), collect their findings, and apply the fixes. The lenses do the looking; you hold the context and make every edit.

Each lens has a sea-monster identity used in everything you show the user — the checklist, the "diving in" announcement, the end-of-round table, the final report. Always render a lens as **emoji + monster name + `(lens-id)`**, e.g. `🐙 The Kraken (dead-code)`:

| Lens | Reviewer |
|:--|:--|
| code-comments | 🎶 The Sirens (code-comments) |
| dead-code | 🐙 The Kraken (dead-code) |
| idiom | 🐍 Jörmungandr (idiom) |
| error-handling | 🌪️ Charybdis (error-handling) |
| clarity | 🧜‍♀️ Little Mermaid (clarity) |
| test-quality | 🦑 Scylla (test-quality) |
| spec-fidelity | 🐋 Cetus (spec-fidelity) |
| cohesion | 🐢 Aspidochelone (cohesion) |

## Interactive vs `--afk`

How you start depends on **who invoked you**, signalled by the `--afk` flag in your arguments:

- **No `--afk` flag** → a human invoked you directly. Run the **interactive first step** below: pose the reviewer checklist and wait for the user to confirm before doing anything else.
- **`--afk` flag present** → another skill invoked you as a sub-step (e.g. close-the-loop). Run **autonomously**: skip the checklist entirely, select the auto-applicable lenses yourself (the heuristics in §2), and proceed straight to the rounds. Never stall on a prompt — the caller's flow depends on it.

Once the lenses are chosen (either way), the rest runs **autonomously.** Don't ask the user "okay to apply?" — just apply the fixes you're confident in and report what you did, the way you'd handle drive-by fixes. When you're *not* confident a fix is right, you don't block on the user either — you surface it in the final report instead of applying it.

The sub-agents stay **independent and context-free.** You never tell a sub-agent what an earlier round decided — that would make it defer to you instead of reviewing the code cold, and a contaminated reviewer is worthless. The memory lives with *you*: you keep a private ledger of what you applied and what you consciously declined, and you use it to tell genuinely new findings apart from re-flags of things you've already settled.

## 1. Interactive first step — pose the checklist (skip entirely if `--afk`)

This is your **very first action** when invoked without `--afk`. Do it from **current conversation context alone — read no files yet.** The human is here now and shouldn't wait on file I/O; resolving the target can happen later (step 3), by which point they're likely AFK.

1. From what's already in the conversation, infer which lenses are relevant: what code was worked on, whether tests were touched, whether a spec/ticket/PRD is in play.
2. Pose a **multi-select checklist** using whatever interactive multi-select prompt your harness offers (e.g. a multi-select question tool). **Always show all eight reviewers** in the `emoji + monster + (lens-id)` format — the user toggles against the full roster, never a pre-filtered subset. **Pre-select the ones your inference flagged as relevant** and label them `(recommended)`; leave the rest shown but unselected. If current context gives you **no signal**, pre-select **all eight**.

   Do **not** hardcode how many options fit in one prompt — that limit belongs to the harness's tool and varies by tool and over time. If the multi-select can't fit all eight in a single prompt, **split across as many prompts as it takes** (e.g. group them into code-quality lenses and behavior/spec lenses) so the user still sees every lens. Never drop a lens just to fit a cap. Interactive TUIs run via the shell (inquirer, gum, fzf, etc.) **don't work** here — they need a terminal wired to the user, which a skill's shell commands don't get; the harness's native question tool is the only thing that renders real choices back to the user.
3. The user toggles and confirms. Their selection is the roster for this run. If they deselect everything, there's nothing to review — say so and stop.
4. **Announce the roster** before proceeding:

   ```
   🌊 Diving in with 3 reviewers:
      🐙 The Kraken (dead-code)
      🐍 Jörmungandr (idiom)
      🎶 The Sirens (code-comments)
   ```

A checked lens **runs at least once**, even if scope later looks thin — the sub-agent itself decides whether it has anything to contribute (e.g. test-quality with no changed tests can still examine relevant existing tests or recommend a missing one, respecting "don't test internals"). If a lens genuinely finds nothing and has nothing to recommend, it simply comes back empty and is marked complete.

## 2. The lenses

Each lens lives in `lenses/` and is a self-contained directive a sub-agent receives:

- **code-comments** (`lenses/code-comments.md`) — 🎶 The Sirens — comment quality, subtractive.
- **dead-code** (`lenses/dead-code.md`) — 🐙 The Kraken — unused/unreachable code, debug leftovers.
- **idiom** (`lenses/idiom.md`) — 🐍 Jörmungandr — house conventions and language idioms.
- **error-handling** (`lenses/error-handling.md`) — 🌪️ Charybdis — failure paths.
- **clarity** (`lenses/clarity.md`) — 🧜‍♀️ Little Mermaid — readability of added functions and logic.
- **test-quality** (`lenses/test-quality.md`) — 🦑 Scylla — tests; auto-selected when the change touches tests.
- **spec-fidelity** (`lenses/spec-fidelity.md`) — 🐋 Cetus — receives the spec; auto-selected when one exists.
- **cohesion** (`lenses/cohesion.md`) — 🐢 Aspidochelone — code placement and ownership: does this code live in the right place, on the right type? Reads wider than its siblings (the change *plus* the existing concepts it should have joined). Auto-selected whenever the change **adds or moves functions, methods, or types** — i.e. any non-trivial code change; same default tier as clarity/idiom. Findings tend to ripple (re-homing touches call sites), so it biases toward **surface**, like idiom.

These auto-selection rules decide what gets **pre-checked** (interactive) or **run** (under `--afk`) — they are heuristics, not hard gates. When invoked with `--afk`, run every auto-selected lens (skip test-quality if no tests changed, spec-fidelity if no spec). When interactive, run exactly the user's selection: a lens the user explicitly checked **always runs at least once** (§1), even against these heuristics — the sub-agent then judges whether it has anything to contribute. This override is **interactive-only**: under `--afk` there's no user selection, so the skip rules apply as-is.

## 3. Resolve the target code

Figure out *what code* to review. The user named a source, or you infer it from the conversation. When interactive, do this **after** the checklist — the human is AFK by now, so taking the time to re-read files here is fine and on you.

- **A PR** → `gh pr diff <n>` (or the branch diff against the base).
- **Staged changes** → `git diff --staged`.
- **What we just worked on** → the working-tree diff (`git diff`) plus whatever was edited in this conversation.
- **Code an agent just wrote** → the files/hunks that agent reported.
- **Code referenced in the conversation** → the specific files or ranges discussed.

Resolve it to a concrete list of files and line ranges before dispatching. If it's ambiguous which source the user means and you're interactive, ask; under `--afk`, make the best inference rather than stalling.

Filter out what isn't worth reviewing: binary files, generated/vendored output, lockfiles, build artifacts — anything not hand-written (`linguist-generated`, regenerated assets, `.usdz`, etc.). If after filtering the target is empty, there's nothing to review — say so and stop before dispatching anything.

Also grab the **spec** if one exists — the ticket, request, or plan this code was meant to satisfy (from the conversation, a linked issue, a PRD). The spec-fidelity lens needs it; without one, that lens is skipped — *unless* the user explicitly selected it, in which case an explicit check overrides this heuristic (§2) and the sub-agent reviews against whatever intent it can infer.

## 4. Run rounds until the reviewers go quiet

The review is a loop. Each **round** is a fresh batch of sub-agents reviewing the *current* state of the code.

**Every round spawns brand-new sub-agents** — never continue a previous round's sub-agent. A fresh sub-agent reads the code cold, with no attachment to earlier findings, so when one finds nothing it means the code itself is clean, not that a reviewer ran out of steam.

**Round 1** dispatches every lens on the roster. **Each later round dispatches only the lenses being re-reviewed** (see the loop rule below) — not the ones already marked complete.

A single round:

1. **Re-resolve the target, then dispatch one sub-agent per active lens, in parallel.** For round 2 onward, **regenerate the diff / re-read the ranges first** so sub-agents see the *current, post-edit* code — not the stale earlier diff. Then use the Agent/Task sub-agent tool, one call per lens, all in a single message. **Don't read the lens files yourself** — give each sub-agent the **path** to its lens directive and tell it to read that file first. That keeps your own context lean (you only hold the ledger, findings, and code). Each sub-agent's prompt is *only*:
   - The path to its lens directive file (it reads the file itself).
   - The current resolved target code (the diff and/or file paths + ranges to read).
   - **For spec-fidelity only:** the spec as well — legitimate task context, not prior-round contamination.

   Nothing about earlier rounds. The sub-agent reviews the current code cold. Sub-agents are **read-only**: instruct them not to edit, and don't rely on edits from them — *you* make every change. Each returns a flat list of findings (each lens defines its own format — broadly `file:line — what — why`, sometimes with a suggested change; spec-fidelity may report `missing` instead of a line; no severity).

   If a lens sub-agent errors, times out, or returns unusable output, **re-dispatch it** (a couple of retries) — never let a failed lens silently count as "found nothing."

2. **Reconcile against your ledger.** Dedupe across lenses. When two lenses flag the **same location with different suggested fixes**, adjudicate them together as one decision — don't apply them independently, or the second edit fights the first. Then sort each finding:
   - **New** (not in your ledger) → decide it, one of three ways: **apply** the fix yourself (when you're confident it's right), **surface** it in the final report (real finding, but the fix is a judgment call you're not confident in), or **decline** it and record *why* in your ledger. When a lens flags that a fix **ripples beyond the reviewed code** (e.g. idiom marking a change that touches call sites), lean toward surface unless you're confident you can update every affected site. Apply edits one at a time, and re-locate each remaining edit against the current file before making it — earlier edits shift everything below them.
   - **Already declined** (a re-flag of something in your ledger) → ignore it by default. But notice the pattern: if independent fresh reviewers keep raising the same declined item round after round, treat that repetition as a serious signal and re-examine your own reasoning honestly — you may have been wrong.

3. **Classify each lens's outcome and announce the round.** For each lens that ran this round, it is one of two states:
   - **Re-review** — the lens caused a **substantive code edit**. It runs again next round so a fresh sub-agent can check your change.
   - **Complete** — the lens made **no edit**, or only a **behavior-neutral** one (a comment/doc tweak, or a cosmetic touch that can't change what the code does). It's done and **dropped** for good — it will not run again, even if other lenses keep editing.

   The boundary is behavior, not line count: **re-review any edit that could change what the code does** — a one-line change still counts if it's logic rather than cosmetics — and when you're genuinely unsure, re-review.

   Then print the end-of-round table. **List every one of the eight lenses, every round** — including ones that were never selected (mark them `⏭️ Skipped`) and ones already marked Complete in an earlier round (carry their last outcome forward). Sort re-review rows on top. The last three columns are **cumulative across all rounds so far**:

   - **Rounds** — how many rounds this reviewer has actually run a sub-agent (skipped lenses stay `0`).
   - **Tokens** — total tokens its sub-agents have used across all rounds (sum the `subagent_tokens` each dispatch reports; skipped = `0`).
   - **Time** — total wall-clock its sub-agents have taken across all rounds (sum the reported `duration_ms`; skipped = `0`).

   **If your sub-agent tool does not report token or duration metrics** (some return plain text only), mark those columns `n/a` and say so once — **never estimate or fabricate plausible-looking numbers.** A confabulated `~40k`/`~30s` dressed in this table's formatting reads as authoritative and is worse than an honest `n/a`.

   Close with a **Totals** footer: total rounds · total **sub-agent dispatches** (the cumulative number of sub-agents launched across all rounds — *not* one-per-lens; a lens re-reviewed twice counts twice) · total tokens · total time.

   **Round 2 complete**

   | Reviewer | Outcome | Detail | Next | Rounds | Tokens | Time |
   |:--|:-:|:--|:-:|:-:|--:|--:|
   | 🐙 The Kraken (dead-code) | ✏️ Edited | Removed an unused helper | 🔁 Re-review | 2 | 44.1k | 18.3s |
   | 🐍 Jörmungandr (idiom) | ✏️ Edited | Normalized 3 call sites | 🔁 Re-review | 2 | 41.7k | 16.9s |
   | 🌪️ Charybdis (error-handling) | 🙅 Declined | 1 intentional swallow left as-is | ✅ Complete | 1 | 22.3k | 9.7s |
   | 🧜‍♀️ Little Mermaid (clarity) | 📤 Surfaced | 1 note sent to report | ✅ Complete | 1 | 21.0k | 8.4s |
   | 🎶 The Sirens (code-comments) | ✨ Clean | Nothing found | ✅ Complete | 1 | 20.1k | 7.5s |
   | 🦑 Scylla (test-quality) | ⏭️ Skipped | Not selected | — | 0 | 0 | 0s |
   | 🐋 Cetus (spec-fidelity) | ⏭️ Skipped | No spec | — | 0 | 0 | 0s |
   | 🐢 Aspidochelone (cohesion) | 📤 Surfaced | 1 mislocated method sent to report | ✅ Complete | 1 | 23.4k | 9.1s |

   > Next round: 🐙 The Kraken (dead-code) · 🐍 Jörmungandr (idiom)
   >
   > **Totals so far:** 2 rounds · 8 sub-agents · 172.6k tokens · 1m 10s

4. **Decide whether to loop again.** If **any lens is in the re-review state**, run another round with **only those lenses**. **The loop ends the first round that leaves no lens in the re-review state** — i.e. no lens made a substantive edit — at which point every remaining reviewer is satisfied and you've converged. There is **no round cap**: the active set shrinks each round (only still-editing lenses survive), so it terminates on its own.

   **Match re-flags by content, not line number.** After you apply a fix, lines shift, so a re-flag of a declined item arrives at a *different* `file:line` and often reworded. Key your ledger on a stable anchor — the symbol, the snippet, the comment text — and match on that. Treat a finding about code that a *prior round's own fix introduced* as already-adjudicated by default (bias to decline/surface), so you and the lenses don't ping-pong over each other's edits.

## 5. Your ledger

The ledger is yours alone — never injected into a sub-agent's prompt. It holds:

- **Applied** — fixes already made (so when you see that issue gone, you know why).
- **Surfaced** — real findings you weren't confident enough to auto-fix and instead put in the report.
- **Declined, with reasoning** — findings you chose not to act on and why ("this comment explains a non-obvious workaround — it earns its place").

You use it purely to classify each incoming finding as new-or-settled. Independence is the whole design: the sub-agents never learn what you decided, so a comment that's genuinely bad gets flagged by every fresh reviewer — and that drumbeat, not an argument handed back to one agent, is what should move you to reconsider.

## 6. Verify, persist, report

**Verify.** Once the loop converges, run the project's build/test gate once — the repo's usual build/test command (some wrap it, e.g. a `./test.sh`; check the project's docs/CLAUDE.md). If a fix you applied broke it, **revert that fix and surface it** instead — never report success on broken code.

**Persist — match the state of the code you reviewed** (the source from step 3):

- Reviewing **unstaged working-tree changes**, or **a piece of existing/committed code** → leave your edits in the working tree, **unstaged**. Same state as what you reviewed; the user stages or commits later if they want.
- Reviewing **staged changes** → stage your edits too, so the cleanup travels with what's already staged. But stage **only the exact hunks you changed** — *never* `git add <file>` a whole file. Other agents may be editing the same files concurrently, and a whole-file add would sweep their unrelated work into the commit. Use hunk-level staging (`git add -p`, or stage specific line ranges) so only your own changes get staged.
- **Never commit.** If the user wants a commit, they'll say so.

**Report.** Tell the user what happened in a few lines: which reviewers ran (by monster name), how many rounds it took, what you changed (call out the higher-stakes edits explicitly — removed code, deleted or rewritten tests, behavior dropped as scope creep), what you reverted, and anything you surfaced or declined (with reasoning). End with an explicit bottom line a caller can act on: **converged clean**, or **converged with N findings still open** (surfaced/reverted). No approval step — just a summary of work already done.
