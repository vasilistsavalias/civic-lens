# Evaluation Report (Public + Mock)

- Samples: 9
- Sentiment Macro-F1: 0.7091
- Stance Macro-F1: 0.4815
- Toxicity Macro-F1: 0.4706
- Emotion micro-F1: 0.4286
- Quality Pearson: 0.7235
- Quality Spearman: 0.6205
- ECE proxy: 0.3889
- Brier proxy: 0.1944
- Abstain rate: 0.0
- Slice FPR (non-offensive criticism): 0.0

## Limitations
- Public benchmark subset is mapped and reduced for mockup comparability.
- Calibration metrics are proxies without external ground-truth probabilities.
- Quality correlation uses synthetic labels in this phase.