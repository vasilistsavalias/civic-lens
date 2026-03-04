# Research Ground Truth

## Source
- **Title:** Bassignana et al. - HurtLex: A Multilingual Lexicon of Words to Hurt
- **Link:** https://aclanthology.org/2020.lrec-1.145/

## 1) TLDR
Multilingual hurtful-language lexicons provide practical lexical priors for profanity/offense detection across languages.

## 2) Insights Gained
- Lexicons are strong bootstrapping tools for low-resource moderation setups.
- Category-aware lexicons improve interpretability of offensive-term hits.
- Language coverage matters for civic platforms with bilingual or mixed-language comments.

## 3) Applied To Our Task
- Grow our profanity lexicon with Greek/English category tags and provenance.
- Record lexicon-hit counts as explicit features in toxicity telemetry.
- Use lexicon-first mock rules now, then backfill with model-based disambiguation later.
