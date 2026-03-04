# Research-Backed Stage-1 Agent Rubric (Mockup)

## Goal

This mockup stage uses deterministic heuristics, but each heuristic is anchored to open/free primary research so we can iterate in a research -> code -> test loop before production models.

## Agent Inventory (10)

1. `sentiment`
2. `stance`
3. `irony`
4. `argument_quality`
5. `profanity`
6. `toxicity`
7. `civility`
8. `structure`
9. `evidence`
10. `relevance`

## Definitions Used

### What is a quality argument?

For this project, a "quality argument" means the comment is:

- relevant to the proposal/topic
- supported with reasons/evidence
- structurally coherent (claim + reasoning cues)
- civil enough for constructive discourse

This aligns with computational argument-quality work that models quality as a multi-dimensional construct (not one signal only), including logical/rhetorical dimensions and fine-grained quality criteria.

### What counts as cursing / bad language?

We separate:

- `profanity`: explicit swear terms
- `toxicity`: broader offense/abuse (includes insults, aggression, shouting patterns, or profanity)

This follows offensive-language research that distinguishes abusive language types and separates offensive/profane content from narrower hate-speech definitions.

### What counts as structured vs unstructured?

- `structured`: explicit claim position and supporting reasoning markers, usually with enough detail
- `semi_structured`: partial structure (some reasoning but incomplete)
- `unstructured`: mostly assertion/slogan with little or no support

This is aligned with argument-mining literature on argument components (claims/premises) and relations.

## Mockup Scoring Math

All scores are bounded in `[0, 1]`.

- `toxicity_score = 0.45*profanity + 0.35*insults + 0.10*caps_ratio + 0.10*exclamation_burst`
- `civility_score = 0.60*(1 - toxicity_score) + 0.40*politeness_signal`
- `evidence_score = 0.45*reason_markers + 0.35*source_markers + 0.20*numeric_signal`
- `structure_score = mean(claim_signal, reason_signal, counter_argument_signal, length_signal)`
- `relevance_score = proposal/topic keyword hit signal`
- `argument_quality_score = 0.35*relevance + 0.25*evidence + 0.20*structure + 0.20*civility - 0.20*toxicity - 0.10*profanity`

Thresholds:

- `structure`: `structured >= 0.75`, `semi_structured >= 0.50`, else `unstructured`
- `evidence`: `evidence_backed >= 0.60`, `limited_evidence >= 0.30`, else `unsupported`
- `toxicity`: `toxic >= 0.45`, else `non_toxic`
- `argument_quality`: `high >= 0.70`, `medium >= 0.45`, else `low`

## Sources (Open/Free)

- Wachsmuth et al., "Building an Argument Search Engine for the Web" (argument quality dimensions): https://aclanthology.org/E17-1017/
- Stab and Gurevych, "Parsing Argumentation Structures in Persuasive Essays" (argument structure): https://aclanthology.org/J17-3005/
- Mohammad et al., "SemEval-2016 Task 6: Detecting Stance in Tweets": https://aclanthology.org/S16-1003/
- Rosenthal et al., "SemEval-2017 Task 4: Sentiment Analysis in Twitter": https://aclanthology.org/S17-2088/
- Van Hee et al., "SemEval-2018 Task 3: Irony Detection in English Tweets": https://aclanthology.org/S18-1005/
- Zampieri et al., "Predicting the Type and Target of Offensive Posts in Social Media" (OffensEval): https://arxiv.org/abs/1903.08983
- Davidson et al., "Automated Hate Speech Detection and the Problem of Offensive Language": https://arxiv.org/abs/1703.04009
- Danescu-Niculescu-Mizil et al., "A Computational Approach to Politeness with Application to Social Factors": https://aclanthology.org/W13-3905/
- Bassignana et al., "HurtLex: A Multilingual Lexicon of Words to Hurt": https://aclanthology.org/2020.lrec-1.145/
