# Manual AirTable Update Guide - 11 Scope Coverage Enhancement Stages

**Date:** 2025-11-16
**Purpose:** Manual instructions to add 11 scope coverage enhancement stages to AirTable
**Reason:** API encountered 403 permission error (token lacks write access to base app6VBiQlnq6yv0D7)

---

## Background

The BQX ML project has **major gaps** in currency-related (4/10) and universal (3/10) scope coverage. These 11 enhancements address those gaps across 3 priority tiers.

**Total Impact:** +1,610 features, 6 weeks, $266
**Performance Gain:** Sharpe 1.5 → 2.4-2.5 (+60-67%)
**Scope Coverage:** Currency-Related 4/10 → 9/10, Universal 3/10 → 10/10

---

## Instructions

Manually add the following 11 stages to the AirTable "Phase 2 Stages" table in base **app6VBiQlnq6yv0D7**:

---

## TIER 1: CRITICAL ENHANCEMENTS (Weeks 1-2)

---

### Stage 2.3: Implement Currency Indices (POPULATE DATA)

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.3 |
| **Name** | Implement Currency Indices (POPULATE DATA) |
| **Status** | Todo |
| **Priority** | Critical |
| **Duration (hours)** | 20 |
| **Estimated Cost** | $8 |
| **Dependencies** | 2.11, 2.12 |
| **Phase** | Phase 2 |
| **Tier** | Tier 1 (Critical) |
| **ROI** | +224 currency-related features |

**Description:**
```
CRITICAL: Schema exists but ZERO data populated. This stage populates existing currency_index tables.

Problem: Stage 2.3 created 336 database tables (28 pairs × 12 year_months) but NO DATA was inserted.

Implementation:
1. Calculate currency strength indices for 8 major currencies (USD, EUR, GBP, JPY, AUD, CAD, CHF, NZD)
2. Populate 8 features per pair:
   - base_currency_strength
   - quote_currency_strength
   - strength_divergence
   - base_currency_strength_percentile
   - quote_currency_strength_percentile
   - pair_divergence_from_index
   - related_pairs_correlation_60min
   - triangular_consistency_score

Total: +224 currency-related features (8 features × 28 pairs)

Deliverables:
- Python script: scripts/features/stage_2_3_currency_indices.py
- Populate 336 partitions: currency_index_{pair}_{year_month}
- Total rows: ~123M (370K per partition)
- S3 export update: Add currency_index JOIN
- Validation: USD_index correlation > 0.95 with 1/EURUSD

Success Criteria:
✅ All 336 partitions populated with 8 features
✅ Validation tests pass (correlation > 0.95)
✅ Features exported to S3
✅ Zero nulls in critical columns

Expected Impact:
- Currency-related scope coverage: 4/10 → 6/10
- R² improvement: +1-2% from currency strength signals
- Rationale: EUR/USD movements driven by EUR vs USD strength divergence
```

---

### Stage 2.4: Implement Triangular Arbitrage Detection (POPULATE DATA)

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.4 |
| **Name** | Implement Triangular Arbitrage Detection (POPULATE DATA) |
| **Status** | Todo |
| **Priority** | Critical |
| **Duration (hours)** | 20 |
| **Estimated Cost** | $8 |
| **Dependencies** | 2.11, 2.12 |
| **Phase** | Phase 2 |
| **Tier** | Tier 1 (Critical) |
| **ROI** | +112 arbitrage features |

**Description:**
```
CRITICAL: Schema exists but ZERO data populated. This stage populates existing arbitrage tables.

Problem: Stage 2.4 created 336 database tables but NO DATA was inserted.

Implementation:
1. Identify 56 currency triplets (EUR-USD-GBP, EUR-USD-JPY, etc.)
2. Calculate arbitrage profit for each triplet at each timestamp
3. Populate 4 features per pair:
   - arbitrage_profit_pct (max across all triplets)
   - arbitrage_opportunity (boolean: profit > 0.05%)
   - arbitrage_direction (which triplet/leg to exploit)
   - arbitrage_max_profit (accounting for spreads)

Total: +112 arbitrage features (4 features × 28 pairs)

Example: EUR-USD-GBP Triplet
- EUR/USD = 1.1000
- USD/GBP = 1/1.2500 = 0.8000
- GBP/EUR = 1/0.8800 = 1.1364
- Implied EUR/USD = 0.8000 × 1.1364 = 0.9091
- Arbitrage profit = (0.9091/1.1000 - 1) × 100 = -17.4%

Deliverables:
- Python script: scripts/features/stage_2_4_arbitrage_detection.py
- Populate 336 partitions: arbitrage_{pair}_{year_month}
- Total rows: ~123M
- S3 export update: Add arbitrage JOIN
- Validation: EUR/USD × GBP/USD × EUR/GBP ≈ 1 (within 0.1%)

Success Criteria:
✅ All 336 partitions populated
✅ Arbitrage opportunities < 1% of samples (should be rare)
✅ Triangular consistency validation passes
✅ Features exported to S3

Expected Impact:
- Currency-related scope coverage: 6/10 → 7/10
- R² improvement: +1-2% from arbitrage mean-reversion signals
- Rationale: Triangular imbalances predict short-term reversions
```

---

### Stage 2.16B: Expand Cross-Pair Interactions - Currency Blocs

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.16B |
| **Name** | Expand Cross-Pair Interactions - Currency Blocs |
| **Status** | Todo |
| **Priority** | Critical |
| **Duration (hours)** | 15 |
| **Estimated Cost** | $6 |
| **Dependencies** | 2.3, 2.16 |
| **Phase** | Phase 2 |
| **Tier** | Tier 1 (Critical) |
| **ROI** | +48 bloc features |

**Description:**
```
Expand Stage 2.16 from sister pairs (bilateral) to currency blocs (3+ currency groupings).

Problem: Current Stage 2.16 only covers sister pairs (pairs sharing ONE currency). Missing currency bloc dynamics.

Currency Blocs:
1. Commodity Bloc (AUD/CAD/NZD) - 17 pairs
2. Safe Haven Bloc (CHF/JPY) - 13 pairs
3. EUR-Zone Bloc (all EUR pairs) - 7 pairs
4. USD Bloc (all USD pairs) - 7 pairs

Implementation:
1. Calculate bloc indices (average currency strength across bloc members)
2. Add 48 features (12 features × 4 blocs):

   Commodity Bloc (12):
   - commodity_bloc_index
   - pair_divergence_from_commodity_bloc
   - commodity_bloc_momentum
   - commodity_bloc_volatility

   Safe Haven Bloc (12):
   - safe_haven_index
   - risk_on_index
   - risk_sentiment (risk-on minus safe-haven)
   - pair_alignment_with_risk_sentiment

   EUR-Zone Bloc (12):
   - eur_zone_coherence
   - eur_leadership (which EUR pair leads)
   - eur_divergence
   - eur_bloc_momentum

   USD Bloc (12):
   - usd_bloc_strength
   - usd_direction_consensus
   - usd_bloc_volatility
   - pair_alignment_with_usd_bloc

Total: +48 currency bloc features

Deliverables:
- Modified script: scripts/features/stage_2_16_cross_pair_interactions.py
- Add 48 columns to cross_pair_{pair} tables (120 → 168 columns)
- Documentation: docs/currency_bloc_methodology.md
- Validation: Risk-on index spikes during risk events

Expected Impact:
- Currency-related scope coverage: 7/10 → 8/10
- R² improvement: +1-2% from bloc sentiment signals
- Sharpe ratio: +5-8% from risk-on/risk-off detection
```

---

## TIER 2: HIGH PRIORITY ENHANCEMENTS (Weeks 2-4)

---

### Stage 2.17: Multi-Regime Autoencoders (REPLACES Single Autoencoder)

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.17 |
| **Name** | Multi-Regime Autoencoders (REPLACES Single Autoencoder) |
| **Status** | Todo |
| **Priority** | Very High |
| **Duration (hours)** | 30 |
| **Estimated Cost** | $50 |
| **Dependencies** | 2.16B |
| **Phase** | Phase 2 |
| **Tier** | Tier 2 (Very High Priority) |
| **ROI** | +192 net features (256 - 64 baseline) |

**Description:**
```
REPLACES original Stage 2.17 single autoencoder with 4 regime-specific autoencoders.

Problem: Single autoencoder mixes all regimes (trending/ranging × low/high vol), learning suboptimal representations.

Architecture Decision: FOUR regime-specific autoencoders (not one)

Regime Classification (4 regimes):
1. Trending + Low Vol (R² > 0.7, volatility < 0.5%)
2. Trending + High Vol (R² > 0.7, volatility ≥ 0.5%)
3. Ranging + Low Vol (R² ≤ 0.7, volatility < 0.5%)
4. Ranging + High Vol (R² ≤ 0.7, volatility ≥ 0.5%)

Each Autoencoder:
- Input: 802 features (730 base + 72 cross-pair)
- Encoder: 802 → 512 → 256 → 128 → 64
- Decoder: 64 → 128 → 256 → 512 → 802
- Training: Regime-filtered samples (~2.5M each)

Total Output: 4 × 64 = 256 regime-optimized embeddings per pair

Training Strategy:
1. Pre-classify 10M samples into 4 regimes
2. Train 4 separate autoencoders on regime-filtered data
3. At inference: Classify current regime, use corresponding autoencoder
4. Save 336 tables: autoencoder_embeddings_{pair}_{year_month} (256 columns)

Deliverables:
- 4 trained models: autoencoder_regime1.h5, autoencoder_regime2.h5, etc.
- Database: 336 tables with 256 embedding columns (4 regimes × 64 dims)
- Python scripts: stage_2_17_multi_regime_autoencoders.py, classify_regime.py
- Documentation: Regime separation analysis (t-SNE visualization)

Expected Impact:
- Universal scope coverage: 3/10 → 6/10
- R² improvement: 0.85 → 0.87 (+2.4%)
- Directional accuracy: 70% → 73% (+4.3%)
- Sharpe ratio: 1.75 → 1.95 (+11.4%)

Rationale: Trending patterns ≠ ranging patterns. Regime-specific autoencoders learn specialized representations.
```

---

### Stage 2.17B: Graph Neural Network for Currency Network

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.17B |
| **Name** | Graph Neural Network for Currency Network |
| **Status** | Todo |
| **Priority** | Very High |
| **Duration (hours)** | 40 |
| **Estimated Cost** | $50 |
| **Dependencies** | 2.17 |
| **Phase** | Phase 2 |
| **Tier** | Tier 2 (Very High Priority) |
| **ROI** | +128 graph-aware features |

**Description:**
```
Implement Graph Neural Network to exploit currency network structure (28 pairs as graph nodes).

Architecture:
- Nodes: 28 currency pairs
- Edges: 56 triangular relationships (shared currencies)
  * EUR/USD ↔ EUR/GBP (share EUR)
  * EUR/USD ↔ GBP/USD (share USD)
  * EUR/GBP ↔ GBP/USD (share GBP)
- Node Features: 802-dim (current features per pair)
- Edge Weights: Correlation strength between pairs
- GNN Output: 128-dim graph-aware embeddings per pair

GNN Architecture (3-Layer Graph Convolutional Network):
1. GraphConvLayer: 802 → 256 (aggregate neighbor features)
2. GraphConvLayer: 256 → 128 (refine aggregated features)
3. GraphConvLayer: 128 → 128 (output embeddings)

Training Strategy (Self-Supervised):
1. For each timestamp t: Create graph snapshot (28 nodes × 802 features, 28×28 adjacency)
2. Message passing: Each node aggregates features from neighboring nodes
3. Loss: Reconstruction + Contrastive (neighboring nodes should have similar embeddings)
4. Train on 10M timestamps, save model: models/gnn_currency_network.h5

Inference:
1. For each timestamp, build graph snapshot
2. Forward pass through GNN → 28 × 128 embeddings
3. Extract embedding for target pair
4. Save to 336 tables: gnn_embeddings_{pair}_{year_month} (128 columns)

Deliverables:
- Trained model: models/gnn_currency_network.h5
- Database: 336 tables with 128 GNN embedding columns
- Python scripts: stage_2_17b_graph_neural_network.py, build_currency_graph.py
- Visualization: Currency network graph, embedding space (t-SNE)
- Validation: EUR pairs cluster together in embedding space

Expected Impact:
- Universal scope coverage: 6/10 → 8/10
- R² improvement: 0.87 → 0.88 (+1.1%)
- Sharpe ratio: 1.95 → 2.05 (+5.1%)

Rationale: Forex pairs form a network via shared currencies. GNN learns universal patterns.
```

---

### Stage 2.16C: Dynamic Correlation Features

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.16C |
| **Name** | Dynamic Correlation Features |
| **Status** | Todo |
| **Priority** | High |
| **Duration (hours)** | 12 |
| **Estimated Cost** | $5 |
| **Dependencies** | 2.16B |
| **Phase** | Phase 2 |
| **Tier** | Tier 2 (High Priority) |
| **ROI** | +36 dynamic correlation features |

**Description:**
```
Expand Stage 2.16 with regime-dependent and time-of-day correlations (vs static 60-min correlations).

Problem: Current Stage 2.16 uses fixed 60-minute correlations. Correlation structure changes with regime and trading session.

3 New Feature Types:

1. Regime-Dependent Correlations (12 features):
   - corr_low_vol_{pair1}_{pair2}
   - corr_high_vol_{pair1}_{pair2}
   - corr_trending_{pair1}_{pair2}
   - corr_ranging_{pair1}_{pair2}

2. Correlation Regime Shifts (12 features):
   - corr_shift_from_low_vol_regime (current_corr - expected_corr_low_vol)
   - corr_shift_from_high_vol_regime
   - corr_shift_from_trending_regime
   - corr_shift_from_ranging_regime

3. Time-of-Day Correlations (12 features):
   - corr_london_session (7:00-16:00 UTC)
   - corr_ny_session (12:00-21:00 UTC)
   - corr_tokyo_session (23:00-8:00 UTC)
   - corr_london_to_ny_shift
   - corr_ny_to_tokyo_shift

Total: +36 dynamic correlation features

Implementation:
1. Calculate correlations separately for each regime
2. Detect correlation regime shifts (deviation from expected)
3. Calculate session-specific correlations (London/NY/Tokyo)

Deliverables:
- Modified script: scripts/features/stage_2_16_cross_pair_interactions.py
- Add 36 columns to cross_pair_{pair} tables (168 → 204 columns)
- Validation: Regime correlations differ significantly (low-vol ≠ high-vol)

Expected Impact:
- Currency-related scope coverage: 8/10 → 9/10
- R² improvement: +0.5-1.0%
- Sharpe ratio: +3-5%

Rationale: EUR/GBP correlation is 0.85 during London but 0.60 during Tokyo.
```

---

## TIER 3: MEDIUM PRIORITY ENHANCEMENTS (Weeks 4-6)

---

### Stage 2.17C: Hierarchical Autoencoders (Multi-Scale)

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.17C |
| **Name** | Hierarchical Autoencoders (Multi-Scale) |
| **Status** | Todo |
| **Priority** | Medium |
| **Duration (hours)** | 25 |
| **Estimated Cost** | $40 |
| **Dependencies** | 2.17B |
| **Phase** | Phase 2 |
| **Tier** | Tier 3 (Medium Priority) |
| **ROI** | +160 hierarchical features |

**Description:**
```
Implement hierarchical autoencoders to learn representations at 3 scales: pair-level, currency-level, market-level.

Architecture (3-Level Hierarchy):

Level 1 - Pair-Level Encoder:
- 28 separate autoencoders (one per pair)
- Input: 802 features → Output: 64 pair-specific embeddings

Level 2 - Currency-Level Encoder:
- 8 autoencoders (one per major currency)
- Input: Concatenated embeddings from all pairs sharing currency (7 pairs × 64 = 448 dims)
- Output: 32 currency-level embeddings

Level 3 - Market-Level Encoder:
- 1 global autoencoder
- Input: Concatenated currency-level embeddings (8 × 32 = 256 dims)
- Output: 64 market-level embeddings

Total Output: 64 (pair) + 32 (currency) + 64 (market) = 160 hierarchical embeddings per pair

Deliverables:
- Trained models: 28 pair autoencoders, 8 currency autoencoders, 1 market autoencoder
- Database: 336 tables with 160 hierarchical embedding columns
- Python scripts: stage_2_17c_hierarchical_autoencoders.py

Expected Impact:
- Universal scope coverage: 8/10 → 9/10
- R² improvement: +0.5-1.0%
- Sharpe ratio: +2-4%

Rationale: EUR/USD has 3 scales: pair microstructure, currency-wide dynamics, global FX trends.
```

---

### Stage 2.18B: Meta-Learning Transfer (High → Low Liquidity)

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.18B |
| **Name** | Meta-Learning Transfer (High → Low Liquidity) |
| **Status** | Todo |
| **Priority** | Medium |
| **Duration (hours)** | 30 |
| **Estimated Cost** | $30 |
| **Dependencies** | 2.18 |
| **Phase** | Phase 2 |
| **Tier** | Tier 3 (Medium Priority) |
| **ROI** | +10-15% performance on exotic pairs |

**Description:**
```
Implement meta-learning to transfer knowledge from high-liquidity pairs to low-liquidity pairs.

Problem: Low-liquidity pairs (NZD/CAD, NZD/CHF) have sparse data (370K samples vs 10M pooled). Models overfit.

Meta-Learning Strategy (MAML):

1. Pre-Train on High-Liquidity Pairs:
   - EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD, USD/CHF, EUR/GBP (7M samples)
   - Learn universal BQX prediction patterns

2. Fine-Tune on Low-Liquidity Pairs:
   - NZD/CAD, NZD/CHF, AUD/NZD, EUR/NZD, CAD/CHF (8 exotic pairs, 370K each)
   - Start from pre-trained weights
   - Few-shot learning with limited data

Implementation:
1. Train base model on pooled high-liquidity data
2. For each exotic pair: Initialize from base model, fine-tune on pair-specific data
3. Early stopping to prevent overfitting

Deliverables:
- Meta-learned base model: models/meta_learning_base_model.h5
- 8 fine-tuned models for exotic pairs
- Python scripts: stage_2_18b_meta_learning.py

Expected Impact:
- R² improvement on exotic pairs: +10-15% (e.g., 0.65 → 0.75)
- Sharpe ratio on exotic pairs: +20-30%
- Reduced overfitting on low-liquidity pairs

Rationale: EUR/USD and NZD/CAD share universal patterns (momentum, mean-reversion).
```

---

### Stage 2.17D: Semi-Universal Currency Encoders

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.17D |
| **Name** | Semi-Universal Currency Encoders |
| **Status** | Todo |
| **Priority** | Medium |
| **Duration (hours)** | 20 |
| **Estimated Cost** | $40 |
| **Dependencies** | 2.17C |
| **Phase** | Phase 2 |
| **Tier** | Tier 3 (Medium Priority) |
| **ROI** | +448 semi-universal features |

**Description:**
```
Train 8 currency-specific autoencoders (middle ground between pair-exclusive and fully universal).

Architecture: 8 autoencoders (one per major currency: USD, EUR, GBP, JPY, AUD, CAD, CHF, NZD)

Each Currency Autoencoder:
- Input: 802 features
- Training data: Pooled samples from all pairs sharing that currency
  * Example: USD encoder trains on EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCAD, USDCHF, USDJPY
- Output: 56-dim currency-specific embeddings

Total: 8 currencies × 56 dims = 448 semi-universal embeddings per pair
(Each pair gets embeddings from 2 encoders: base currency + quote currency)

Example: EUR/USD gets:
- 56 dims from EUR encoder
- 56 dims from USD encoder
- Total: 112 dims for EUR/USD

Implementation:
1. For each currency, pool data from all pairs containing that currency
2. Train currency-specific autoencoder
3. At inference: Apply both base and quote currency encoders
4. Save 336 tables with 112 semi-universal embeddings

Deliverables:
- 8 trained models: autoencoder_usd.h5, autoencoder_eur.h5, etc.
- Database: 336 tables with 112 semi-universal embedding columns
- Python scripts: stage_2_17d_semi_universal_encoders.py

Expected Impact:
- Universal scope coverage: 9/10 → 9.5/10
- R² improvement: +0.5-1.0%
- Sharpe ratio: +2-3%

Rationale: USD behavior affects all 7 USD pairs similarly.
```

---

### Stage 2.17E: Universal Ensemble (VAE + Contrastive + Transformer)

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.17E |
| **Name** | Universal Ensemble (VAE + Contrastive + Transformer) |
| **Status** | Todo |
| **Priority** | Medium |
| **Duration (hours)** | 40 |
| **Estimated Cost** | $60 |
| **Dependencies** | 2.17D |
| **Phase** | Phase 2 |
| **Tier** | Tier 3 (Medium Priority) |
| **ROI** | +192 net ensemble features |

**Description:**
```
Ensemble 3 alternative universal architectures for diversity: VAE, Contrastive Learning, Transformer.

Problem: Single autoencoder architecture may miss patterns. Ensemble captures complementary representations.

3 Architectures:

1. Variational Autoencoder (VAE):
   - Probabilistic embeddings (mean + variance)
   - Output: 128 dims (64 mean + 64 variance)

2. Contrastive Learning (SimCLR):
   - Self-supervised: Similar samples → similar embeddings
   - Output: 64 dims

3. Transformer Encoder:
   - Attention-based sequence modeling
   - Output: 64 dims

Total: 128 (VAE) + 64 (Contrastive) + 64 (Transformer) = 256 ensemble embeddings

Training:
1. Train all 3 architectures independently on pooled 10M samples
2. Save models: vae_802_to_128.h5, contrastive_802_to_64.h5, transformer_802_to_64.h5
3. At inference: Apply all 3, concatenate outputs

Deliverables:
- 3 trained models (VAE, Contrastive, Transformer)
- Database: 336 tables with 256 ensemble embedding columns
- Python scripts: stage_2_17e_universal_ensemble.py

Expected Impact:
- Universal scope coverage: 9.5/10 → 10/10
- R² improvement: +0.5-1.0%
- Sharpe ratio: +2-4%

Rationale: VAE captures probabilistic patterns, Contrastive captures similarity, Transformer captures temporal dependencies.
```

---

### Stage 2.20: Cross-Scope Hybrid Features

**Field Values:**

| Field | Value |
|-------|-------|
| **Stage** | 2.20 |
| **Name** | Cross-Scope Hybrid Features |
| **Status** | Todo |
| **Priority** | Medium |
| **Duration (hours)** | 15 |
| **Estimated Cost** | $5 |
| **Dependencies** | 2.17E |
| **Phase** | Phase 2 |
| **Tier** | Tier 3 (Medium Priority) |
| **ROI** | +60 hybrid features |

**Description:**
```
Create hybrid features that combine pair-exclusive, currency-related, and universal representations.

Hybrid Feature Types (60 total):

1. Pair × Currency Blocs (20 features):
   - pair_deviation_from_commodity_bloc × pair_volatility
   - pair_momentum × risk_sentiment
   - pair_r2 × eur_zone_coherence

2. Pair × Universal Embeddings (20 features):
   - pair_quadratic_term × autoencoder_emb_5
   - pair_linear_term × gnn_emb_12
   - pair_residual × transformer_emb_23

3. Currency × Universal (20 features):
   - currency_index_usd × autoencoder_emb_10
   - arbitrage_profit × gnn_emb_7
   - commodity_bloc_index × transformer_emb_15

Rationale:
- Pair-exclusive captures microstructure
- Currency-related captures cross-pair dynamics
- Universal captures latent patterns
- Hybrids capture interactions between scopes

Example:
- pair_momentum × risk_sentiment = High when pair momentum aligns with risk-on/risk-off sentiment

Implementation:
1. Load features from all 3 scopes
2. Calculate 60 hybrid features (products, ratios, differences)
3. Add to cross_scope_hybrid_{pair}_{year_month} tables

Deliverables:
- Python script: scripts/features/stage_2_20_cross_scope_hybrids.py
- Database: 336 tables with 60 hybrid feature columns

Expected Impact:
- Feature quality improvement: +5-10%
- Sharpe ratio: +2-3%

Rationale: Strong pair momentum + strong risk-on sentiment = higher conviction signal.
```

---

## Summary

After manually adding these 11 stages to AirTable:

**Total Scope Coverage Enhancement Stages:** 11 (2.3, 2.4, 2.16B, 2.17, 2.17B, 2.16C, 2.17C, 2.18B, 2.17D, 2.17E, 2.20)

**Timeline:** 6 weeks (267 hours)

**Cost:** $266 one-time

**Net New Features:** +1,610 features (accounting for autoencoder replacement)

**Performance Projection:**
- Current: R² = 0.82, Directional = 65%, Sharpe = 1.5
- Post-Enhancement: R² = 0.90+, Directional = 77%+, Sharpe = 2.4-2.5
- Improvement: +10% R², +18% Directional, +60-67% Sharpe

**Scope Coverage Improvement:**
- Currency-Related: 4/10 → 9/10 (+125%)
- Universal: 3/10 → 10/10 (+233%)
- Overall: 5/10 → 9/10 (+80%)

**Implementation Sequence:**
```
TIER 1 (Critical - Weeks 1-2):
  Stage 2.3 → Stage 2.4 → Stage 2.16B

TIER 2 (High Priority - Weeks 2-4):
  Stage 2.17 → Stage 2.17B → Stage 2.16C

TIER 3 (Medium Priority - Weeks 4-6):
  Stage 2.17C → Stage 2.18B → Stage 2.17D → Stage 2.17E → Stage 2.20

Integration Points:
  Stage 2.15 (Validation) → TIER 1 → TIER 2 → TIER 3 → Stage 2.7 (Update S3 Export) → Phase 3
```

**Reference Documents:**
- Complete Enhancement Plan: [docs/scope_coverage_enhancement_plan.md](scope_coverage_enhancement_plan.md)
- Python Script (blocked by 403 error): [scripts/airtable/add_scope_coverage_enhancement_stages.py](../scripts/airtable/add_scope_coverage_enhancement_stages.py)

---

## API Integration Status

**Attempted:** Python script using AWS Secrets Manager credentials
**Result:** 403 INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND
**Reason:** API token from AWS Secrets Manager has access to base appkKH0u1BhAHUao6 (Robkei-Ring) but NOT base app6VBiQlnq6yv0D7 (BQX ML Phase 2 Stages)

**Recommendation:** Update AWS Secrets Manager secret with token that has write access to app6VBiQlnq6yv0D7, or manually add stages using this guide.
