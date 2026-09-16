---
name: humanizer-academic
description: Rewrite academic prose to defeat AI detectors (Turnitin, GPTZero, Originality.ai) while preserving formal register. Use when a thesis, journal article, assessment report, or any graduate-level academic text needs to read as human-written without sliding into blog voice. Combines detector-defeating moves (burstiness, perplexity, structural variation) with an allow-list of legitimate academic phrases that general humanizers wrongly strip out.
---

# Humanizer Academic

You rewrite AI-assisted academic prose so it reads as human-written and passes AI detectors *without* sliding into the casual, fragment-heavy, contraction-laden style most humanizers produce.

This skill solves a specific gap. General humanizers (built around Wikipedia's "Signs of AI writing") attack vocabulary and tone but ignore the paragraph silhouette and sentence rhythm detectors actually measure. Detector-focused humanizers (built around burstiness and perplexity) defeat detectors but rewrite into a blog voice that would be marked down in any academic submission. You do both jobs at once.

## The dual constraint

Every rewrite is governed by two non-negotiable rules in tension:

1. **Defeat the detector.** Break sentence-length uniformity. Vary syntactic shape. Cut paragraph silhouettes that read as AI-generated.
2. **Preserve academic register.** No contractions. No fragments unless rhetorically justified. No "And yeah." No "Here's the thing:". No first-person colloquialisms. Citations and formal transitions stay. Domain vocabulary stays.

If a rewrite move would defeat the detector but breach register, find a different move. Both axes have to clear.

## What detectors actually measure

- **Perplexity** — how unsurprising each word choice is statistically. Lower = more AI. Fix by reaching for the second-or-third-likeliest word, not by swapping in casual slang.
- **Burstiness** — variation in sentence length and structure within a paragraph. Flat = AI. Fix by mixing short and long sentences and varying syntactic shape.
- **Paragraph silhouette** — the shape "introduce → gloss parenthetically → list 2–3 examples → tidy summary close" reads as AI even when every word is fine.
- **Transition placement** — sentence-initial "Furthermore", "Moreover", "Additionally" cluster densely in AI prose. Mid-sentence pivots and dropped transitions cluster in human prose.

These four together explain ~80% of why an otherwise clean academic paragraph gets flagged.

## Preserve these — they are not AI tells in academic writing

General humanizers wrongly flag these phrases. In academic writing they are *correct* and stripping them weakens the prose. Only touch them if they cluster excessively or appear without supporting citation.

**Legitimate academic transitions (keep):**

- Notably, ... / Of note, ...
- Importantly, ... / Interestingly, ...
- In contrast, ... / Conversely, ...
- Nevertheless, ... / Nonetheless, ...
- Accordingly, ... / Specifically, ...
- However, ... (sentence-initial is fine in academic prose, despite what blog-voice guides claim)

**Legitimate attribution phrases (keep when followed by citation or specific data):**

- Prior studies have shown that ... [Citation]
- Previous research has demonstrated that ... [Citation]
- A growing body of evidence indicates ... [Citation]
- It has been reported that ... [Citation]

**The rule:** if the phrase is followed by a citation, a number, or a concrete finding, it is legitimate academic writing. Flag only when vague and unsupported ("Studies have shown X is important" with no citation).

## Patterns to fix

### 1. Paragraph silhouette

The classic AI academic paragraph: introduce a concept → gloss it in apposition → list two or three sub-points → close with a tidy summary clause restating the opening.

**Before:**
> LightGBM is a gradient-boosted decision-tree algorithm, in which a sequence of small trees is built such that each tree corrects the errors of the previous one. The model predicts two derived scores: a quality score and a commercial score. In doing so, it provides a useful framework for ranking unreleased game designs.

**After:**
> The model is built on LightGBM. Gradient-boosted trees mean that each tree in the sequence corrects the previous one's errors, with the final prediction being the cumulative sum. Two scores are predicted: a quality score, and a separately constructed commercial score normalised by years on the market.

The "after" still defines LightGBM, still names the targets, still sounds academic. But it opens with a short sentence, runs a longer one, ends with a clause-loaded one that does not summarise.

### 2. Comma-appositive glosses

Inline definitions of the form "LightGBM, a gradient-boosted decision-tree algorithm, …" are correct English but cluster in AI prose at 3–5× human rates. Move definitions to a separate sentence, a footnote, or delete them when the audience is expected to know the term.

### 3. Numbered roadmapping

"Three concrete steps make that real." / "Four related reasons explain this." / "Two questions run through this report."

Roadmapping is acceptable in section-opening positions and in abstracts, but inside body paragraphs it reads as AI. Either start the first item directly without the roadmap sentence, or use a footnote/list rather than prose enumeration.

### 4. Sentence-initial transitions

Move "Furthermore", "Moreover", "Additionally" mid-sentence or drop them. "However" is acceptable sentence-initial in academic prose but not in clusters — if you have three "However" openings in five paragraphs, vary two of them.

### 5. Bold-lead-then-expand subsections

"**Pushing the score too far.** I ran an experiment in which…" — this lead-and-expand pattern flags as AI when used as a structural device across multiple subsections. Either rewrite as prose with the bold phrase folded into the first clause, or use proper subheadings instead of in-line bolded leads.

### 6. Sentence-length uniformity

The single highest-leverage fix. Most flagged academic paragraphs have every sentence sitting in the 18–28 word band.

Target rhythm for an academic paragraph: at least one sentence under 12 words, at least one over 32 words, and no two consecutive sentences within 5 words of each other. This is harder to do in formal register than in casual register, so verify with a word count on every sentence.

## Word-swap rules — academic register only

Casual humanizers' swap tables ("utilize → use, lean on, pull from, reach for") are wrong for academic prose. Use this academic-register table:

| AI default | Academic alternatives |
|---|---|
| utilise / utilize | use, employ, apply |
| implement | carry out, apply, put in place |
| demonstrate | show, indicate, establish, reveal |
| significant (figurative) | meaningful, marked, substantial, notable |
| various | several, multiple, a range of |
| ensure | guarantee, secure, establish |
| facilitate | enable, allow, support |
| leverage (verb) | use, draw on, apply |
| comprehensive | thorough, complete, full |
| in order to | to |
| due to the fact that | because |
| at this point in time | currently, presently, now |
| play a key/pivotal role | matter, contribute, determine |
| robust | reliable, well-supported, strong |
| seamless | continuous, integrated |
| underscore | confirm, support, indicate |

**Rules:**

- Swap roughly 30% of default choices, not 100%. Uniformly swapped vocabulary reads as a different AI tell.
- Do NOT introduce contractions ("don't", "it's") in formal academic prose.
- Do NOT introduce blog-voice connectives ("And yeah", "Here's the thing:", "Honestly,"). These will be flagged by a marker even if Turnitin passes.
- Restore classical academic phrasing AI tends to avoid: "percentage of" (instead of "proportion of"), "purpose of" (instead of "aim of"), "was measured" (instead of "we measured"), "With respect to", "to determine".

## Audit checklist

Before delivering, verify the rewritten paragraph against ALL of these:

- [ ] No two consecutive sentences within 5 words of each other
- [ ] At least one sentence under 12 words OR one over 32 words
- [ ] No more than one sentence-initial "Furthermore", "Moreover", or "Additionally" per page
- [ ] No comma-appositive gloss unless the term genuinely needs defining inline
- [ ] No numbered roadmap sentence ("Three steps", "Two reasons") mid-paragraph
- [ ] No closing summary sentence that restates the opening
- [ ] All legitimate academic transitions preserved (Notably, In contrast, etc.)
- [ ] All citations and attributions to specific sources intact
- [ ] Zero contractions in formal-register text
- [ ] Zero blog-voice connectives ("And yeah", "Here's the thing:")
- [ ] At least 3 word swaps from defaults to less-frequent academic alternatives
- [ ] Domain vocabulary (LightGBM, SHAP, regression, etc.) preserved verbatim

## Worked example

**Input (flagged at 60% AI by Turnitin):**
> The model's two targets are built, not borrowed. `quality_score = BayesAvgRating × 10` uses BGG's Bayesian average so that three perfect reviews from three accounts cannot outrank Pandemic. `commercial_score = log1p(NumOwned / clamp(years_active, 1, 10))` normalises ownership by years on the market so a 2003 hit and a 2023 hit can sit on the same scale. These are my stand-ins for "quality" and "commercial success", and they are narrower than either word in plain English.

**Output:**
> Both targets are constructed rather than borrowed. The first, `quality_score = BayesAvgRating × 10`, draws on BGG's Bayesian average; this prevents three perfect reviews from three accounts outranking established titles such as Pandemic. The second, `commercial_score = log1p(NumOwned / clamp(years_active, 1, 10))`, normalises ownership by years of market presence, so that a 2003 hit and a 2023 hit can be compared on a common scale. These are constructed proxies for "quality" and "commercial success", and each is narrower than its plain-English counterpart.

**What changed and why:**

- Opening sentence shortened to 7 words (under-12 target met)
- Second and third sentences extended with semicolons and embedded clauses (over-32 target met in the third)
- "uses" replaced with "draws on" (perplexity raise, academic register)
- Comma-appositive "BGG's Bayesian average" left in place because it genuinely needs defining
- "my stand-ins" replaced with "constructed proxies" — passive academic phrasing replaces first-person possessive
- "in plain English" replaced with "than its plain-English counterpart" — restores classical academic phrasing
- Code blocks preserved verbatim
- Domain terms preserved
- No contractions, no fragments, no blog-voice connectives

## Common failure modes

- **Don't slip into casual register.** "Lean on", "pull from", "reach for" are wrong here. Stay academic.
- **Don't strip legitimate transitions.** "Notably, …" with a citation is correct academic writing.
- **Don't introduce passive voice mechanically.** Burstiness moves should vary syntax, not just swap active for passive.
- **Don't add personality.** Academic writing has voice, but it is voice through argument and specificity, not through opinions or asides.
- **Don't change citations.** Author names, years, page numbers, DOIs — all preserved verbatim.
- **Don't change numbers.** Reported statistics, R² values, sample sizes — all preserved verbatim.

## Process

1. Read the input text. Identify register (graduate thesis, journal article, assessment report, etc.).
2. Run the audit checklist mentally against the input — which items are failing?
3. Rewrite paragraph by paragraph, addressing the failing items.
4. After rewriting, run the checklist against the output. Every box checked.
5. Present the rewrite with a brief "What changed and why" block (3–6 bullets).
6. If the user asks for a second pass: prompt yourself "What in this rewrite still reads as AI to a Turnitin classifier?" — answer briefly, then revise.

## Reference

Combines techniques from:

- Wikipedia: Signs of AI writing (vocabulary patterns, structural tells)
- Paragraph-humanizer (burstiness numbers, detector-targeted moves)
- humanizer_academic by @matsuikentaro1 (academic transitions allow-list, classical vocab restoration)
- Empirical observation from Turnitin AI scan reports on graduate-level work
