# Research Ground Truth

## Source
- **Title:** Stab and Gurevych - Parsing Argumentation Structures in Persuasive Essays
- **Link:** https://aclanthology.org/J17-3005/

## 1) TLDR
Argument structure can be operationalized through components (claim, premise) and relations, enabling structured vs unstructured classification.

## 2) Insights Gained
- Claims and premises are separable units and can be detected with explicit cues.
- Relation signals (support/attack/connectives) are central for structural coherence.
- Argument parsing quality improves when discourse markers and span-level features are explicit.

## 3) Applied To Our Task
- Map structuredness to claim markers + reason markers + counter-argument markers + length adequacy.
- Maintain a semi-structured middle class instead of binary labels.
- Later extend to span-level component extraction when we move beyond mock rules.
