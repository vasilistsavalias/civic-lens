# Municipal Civic Insights Pipeline

AI-assisted analytics pipeline for municipality proposal feedback.

This project models a two-stage architecture for processing resident comments and reactions on public proposals:

- Frontend layer for resident submissions and municipality dashboards
- Ingestion and queue layer for validation, decoupling, and real-time reaction counting
- Stage 1 parallel per-comment analysis:
  - Sentiment classification
  - Stance detection
  - Irony/sarcasm detection
  - Argument quality scoring
  - Profanity detection
  - Toxicity scoring
  - Civility scoring
  - Argument structure scoring
  - Evidence support scoring
  - Topical relevance scoring
- Stage 2 proposal-level analysis:
  - Topic/theme clustering
  - Trend analysis over time
  - Aggregated natural-language summaries
- Dashboard data store serving municipality-facing insights

## Core Objective

Turn high-volume civic feedback into structured, proposal-level insight that municipalities can monitor in near real time and use for decision support.

Research grounding for Stage-1 agent definitions is documented in [docs/research/agent_rubric.md](./docs/research/agent_rubric.md).

## Architecture (Mermaid)

```mermaid
flowchart TD
    subgraph FRONTEND[" "]
        FT["FRONTEND LAYER"]
        RI["Resident Interface\nSubmit Comments & Reactions"]
        MD["Municipality Dashboard\nBasic Mode / Advanced Mode"]
    end

    subgraph INGESTION[" "]
        IT["INGESTION & QUEUE LAYER"]
        API["API Gateway\nValidates municipality & proposal context"]
        Q["Message Queue\ne.g. Redis / RabbitMQ\nDecouples ingestion from processing"]
        RC["Reaction Counter\nLightweight real-time aggregator"]
    end

    subgraph STAGE1[" "]
        S1T["STAGE 1 - PER-COMMENT ANALYSIS - ALL AGENTS RUN IN PARALLEL"]
        SA["Sentiment Agent\nClassifier\nPositive / Negative / Neutral"]
        STA["Stance Detection Agent\nClassifier\nFor / Against / Neutral"]
        IA["Irony & Sarcasm Agent\nLLM-based"]
        AQA["Argument Quality Agent\nLLM-based"]
    end

    subgraph STORE1[" "]
        ST1T["PER-COMMENT RESULTS STORE"]
        CRS[("sentiment · stance · irony flag · argument quality score\none record per comment")]
    end

    subgraph STAGE2[" "]
        S2T["STAGE 2 - PROPOSAL-LEVEL ANALYSIS"]
        TCA["Topic & Theme Clustering Agent"]
        TA["Trend Analysis Agent"]
        AGG["Aggregation & Summary Agent"]
    end

    subgraph STORE2[" "]
        ST2T["DASHBOARD DATA STORE"]
        DDS[("Aggregated proposal insights per municipality/proposal/time")]
    end

    RI --> API
    API --> Q
    API --> RC
    Q --> SA & STA & IA & AQA
    SA --> CRS
    STA --> CRS
    IA --> CRS
    AQA --> CRS
    RC -.-> DDS
    CRS --> TCA & TA & AGG
    TCA --> DDS
    TA --> DDS
    AGG --> DDS
    DDS --> MD
```
