# ML Feature Maximization Strategy
**Date:** 2025-11-15
**Purpose:** Robust correlation and triangulation for maximum learning effectiveness
**Approach:** Cross-Feature × Cross-Pair × Cross-Window × Cross-Domain

---

## Executive Summary

**Feature Matrix Dimensions:**
- **Features:** 730+ (after remediation)
- **Pairs:** 28 forex pairs
- **Windows:** 6 (w60, w90, w150, w240, w390, w630)
- **Domains:** 2 (rate_index, BQX)
- **Time:** 12 months (Jul 2024 - Jun 2025)

**Correlation Strategy:**
- **Cross-Feature:** Correlate different feature types (regression × technical × arbitrage)
- **Cross-Pair:** Correlate same feature across pairs (EURUSD w60_r2 × GBPUSD w60_r2)
- **Cross-Window:** Correlate same feature across windows (w60_r2 × w90_r2)
- **Cross-Domain:** Correlate rate_index features × BQX features

**Triangulation Strategy:**
- **Multi-Domain Confirmation:** Signal confirmed when both rate_index AND BQX domains agree
- **Multi-Pair Confirmation:** Signal confirmed when correlated pairs agree
- **Multi-Window Confirmation:** Signal confirmed across multiple time horizons
- **Multi-Feature Confirmation:** Signal confirmed by multiple feature types

---

## Part 1: Feature Integration Architecture

### Layer 1: Base Features (Direct Measurements)

**Source Tables:**
- m1_{pair} - OHLCV, rate_index, spread
- reg_rate_{pair} - Rate index regression terms
- reg_bqx_{pair} - BQX regression terms

**Features:**
```python
base_features = {
    # Price-based (rate_index domain)
    'rate_index': rate_index,
    'high_index': high_index,
    'low_index': low_index,
    'open_index': open_index,

    # Regression terms (rate_index)
    'rate_w60_quadratic': w60_quadratic_term,
    'rate_w60_linear': w60_linear_term,
    'rate_w60_constant': w60_constant_term,
    'rate_w60_residual': w60_residual,
    'rate_w60_r2': w60_r2,
    'rate_w60_rmse': w60_rmse,

    # Regression terms (BQX domain)
    'bqx_w60_quadratic': w60_quadratic_term,
    'bqx_w60_linear': w60_linear_term,
    'bqx_w60_constant': w60_constant_term,
    'bqx_w60_residual': w60_residual,
    'bqx_w60_r2': w60_r2,
    'bqx_w60_rmse': w60_rmse,
}
```

**Total:** ~200 base features per pair

### Layer 2: Derived Features (Cross-Feature Combinations)

**Ratios and Differences:**
```python
derived_features = {
    # Cross-domain ratio
    'domain_alignment_w60': rate_w60_r2 / bqx_w60_r2,

    # Cross-window ratio
    'window_consistency_w60_w90': w60_r2 / w90_r2,

    # Term ratios
    'curvature_strength_w60': abs(w60_quadratic) / abs(w60_linear),

    # Error magnitude
    'normalized_error_w60': w60_residual / w60_rmse,

    # Fit quality score
    'fit_quality_w60': w60_r2 * (1 - w60_rmse),
}
```

**Total:** ~100 derived features per pair

### Layer 3: Technical Indicators

**Source Tables:**
- technical_indicators_{pair}

**Features:**
```python
technical_features = {
    # Momentum
    'rsi_14': rsi_14_period,
    'macd': macd_line,
    'macd_signal': macd_signal_line,
    'macd_histogram': macd_histogram,

    # Volatility
    'atr_14': average_true_range_14,
    'bollinger_width': bollinger_upper - bollinger_lower,

    # Oscillators
    'stochastic_k': stochastic_k,
    'stochastic_d': stochastic_d,
    'cci_20': commodity_channel_index_20,
}
```

**Total:** ~180 technical indicators per pair

### Layer 4: Currency Strength Indices

**Source Tables:**
- currency_index_{pair}

**Features:**
```python
currency_features = {
    'base_currency_index': base_currency_strength_index,
    'quote_currency_index': quote_currency_strength_index,
    'currency_differential': base_index - quote_index,
    'base_percentile': base_currency_strength_percentile,
    'quote_percentile': quote_currency_strength_percentile,
}
```

**Total:** ~8 currency features per pair

### Layer 5: Arbitrage Features

**Source Tables:**
- arbitrage_{pair}

**Features:**
```python
arbitrage_features = {
    'arbitrage_profit_pct': triangular_arbitrage_profit,
    'arbitrage_opportunity': boolean_flag,
    'arbitrage_direction': clockwise_or_counterclockwise,
    'arbitrage_max_profit': maximum_profit_both_directions,
}
```

**Total:** ~4 arbitrage features per pair

### Layer 6: Correlation Features

**Source Tables:**
- correlation_bqx_{pair}

**Features:**
```python
correlation_features = {
    # Cross-pair correlations (45 features)
    'corr_base_pairs_15min': correlation_with_base_currency_pairs,
    'corr_quote_pairs_15min': correlation_with_quote_currency_pairs,
    # ... 43 more cross-pair correlations

    # Term covariances (6 features) - NEW
    'cov_quad_lin_bqx_60min': covariance_quadratic_linear,
    'cov_resid_quad_bqx_60min': covariance_residual_quadratic,
    'cov_resid_lin_bqx_60min': covariance_residual_linear,
    'corr_quad_lin_bqx_60min': correlation_quadratic_linear,
    'corr_resid_quad_bqx_60min': correlation_residual_quadratic,
    'corr_resid_lin_bqx_60min': correlation_residual_linear,
}
```

**Total:** ~51 correlation features per pair

### Layer 7: Regime Detection Features

**Source Tables:**
- regime_{pair}

**Features:**
```python
regime_features = {
    # Rate domain (15 features)
    'trend_regime_rate': trending_up_down_ranging,
    'volatility_regime_rate': high_medium_low,
    'momentum_regime_rate': strong_bullish_to_bearish_5_levels,
    'mean_reversion_regime_rate': reverting_vs_trending,
    'composite_regime_rate': combined_score_0_to_10,
    # ... 10 more regime metrics

    # BQX domain (15 features)
    'trend_regime_bqx': trending_up_down_ranging,
    'volatility_regime_bqx': high_medium_low,
    # ... 13 more regime metrics
}
```

**Total:** ~30 regime features per pair

### Layer 8: Enhanced RMSE Features

**Source Tables:**
- enhanced_rmse_{pair}

**Features:**
```python
enhanced_rmse_features = {
    # Per window (6 windows × 10 metrics = 60 features)
    'w60_rmse_improvement': rmse_improvement_vs_linear,
    'w60_r2_rank': percentile_rank_among_windows,
    'w60_term_consistency': correlation_with_adjacent_windows,
    'w60_resid_autocorr': residual_autocorrelation_lag1,
    'w60_pred_error_ratio': normalized_prediction_error,
    'w60_fit_quality': combined_quality_score,
    'w60_overfitting_risk': high_r2_but_increasing_rmse,
    'w60_quad_strength': quadratic_to_linear_ratio,
    'w60_trend_curv_ratio': inflection_point_indicator,
    'w60_model_stability': coefficient_of_variation,
}
```

**Total:** ~60 enhanced RMSE features per pair

---

## Part 2: Cross-Feature Correlation Strategy

### 2.1 Feature Correlation Matrix

**Objective:** Identify which features are most predictive when combined

**Method:**
```python
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

def calculate_cross_feature_correlations(df, target='w60_bqx_return'):
    """
    Calculate correlations between all features and target.

    Args:
        df: DataFrame with all features
        target: Target variable (future BQX return)

    Returns:
        DataFrame: Correlation matrix
    """
    # Select all feature columns
    feature_cols = [col for col in df.columns
                   if col not in ['ts_utc', 'pair', target]]

    # Calculate Spearman correlation (handles non-linear relationships)
    correlations = {}
    for col in feature_cols:
        if df[col].notna().sum() > 100:  # Need sufficient data
            corr, pval = spearmanr(df[col].dropna(), df[target].loc[df[col].notna()])
            correlations[col] = {
                'correlation': corr,
                'p_value': pval,
                'significant': pval < 0.01
            }

    # Convert to DataFrame
    corr_df = pd.DataFrame(correlations).T
    corr_df = corr_df.sort_values('correlation', key=abs, ascending=False)

    return corr_df
```

**Example Output:**
```
Feature                          Correlation  P-Value    Significant
-------------------------------- -----------  ---------  -----------
corr_resid_lin_bqx_60min         0.847       < 0.001    True
bqx_w60_linear                   0.823       < 0.001    True
momentum_regime_bqx              0.801       < 0.001    True
cov_quad_lin_bqx_60min          -0.789       < 0.001    True (negative)
rate_w60_r2                      0.654       < 0.001    True
rsi_14                           0.612       < 0.001    True
```

**Interpretation:**
- **Top 10 features** have highest individual predictive power
- **Negative correlations** indicate inverse relationships (e.g., trend exhaustion)
- **Combine features** with different correlation signs for robustness

### 2.2 Feature Interaction Analysis

**Objective:** Find feature combinations that are more predictive together than individually

**Method:**
```python
def analyze_feature_interactions(df, target='w60_bqx_return', top_n=20):
    """
    Analyze 2-way feature interactions.

    Args:
        df: DataFrame with features
        target: Target variable
        top_n: Number of top features to analyze

    Returns:
        DataFrame: Interaction effects
    """
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.linear_model import Ridge

    # Get top N features
    top_features = calculate_cross_feature_correlations(df, target).head(top_n).index

    # Create polynomial features (interactions)
    poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
    X_interactions = poly.fit_transform(df[top_features].fillna(0))

    # Fit Ridge regression
    model = Ridge(alpha=1.0)
    model.fit(X_interactions, df[target])

    # Get feature names
    feature_names = poly.get_feature_names_out(top_features)

    # Get coefficients
    interactions_df = pd.DataFrame({
        'feature_pair': feature_names,
        'coefficient': model.coef_
    })

    # Filter to interaction terms only (not individual features)
    interactions_df = interactions_df[interactions_df['feature_pair'].str.contains(' ')]
    interactions_df = interactions_df.sort_values('coefficient', key=abs, ascending=False)

    return interactions_df
```

**Example Output:**
```
Feature Pair                                              Coefficient
-------------------------------------------------------- -----------
corr_resid_lin_bqx_60min × momentum_regime_bqx          0.523
bqx_w60_linear × rate_w60_linear                        0.489
cov_quad_lin_bqx_60min × trend_regime_bqx              -0.467
rate_w60_r2 × bqx_w60_r2                                0.445
```

**Interpretation:**
- **High coefficient:** Feature pair has strong combined effect
- **Positive coefficient:** Features amplify each other
- **Negative coefficient:** Features have opposing effects (useful for regime detection)

---

## Part 3: Cross-Pair Correlation Strategy

### 3.1 Correlated Pair Detection

**Objective:** Identify which pair movements predict other pairs

**Method:**
```python
def calculate_cross_pair_correlations(pairs, feature='w60_bqx_return', window=60):
    """
    Calculate rolling correlations between pairs.

    Args:
        pairs: List of currency pairs
        feature: Feature to correlate
        window: Rolling window size (minutes)

    Returns:
        DataFrame: Cross-pair correlation matrix
    """
    # Load data for all pairs
    data = {}
    for pair in pairs:
        df = load_pair_data(pair)
        data[pair] = df[feature]

    # Create DataFrame
    df_all = pd.DataFrame(data)

    # Calculate rolling correlations
    corr_matrix = df_all.rolling(window=window).corr()

    return corr_matrix
```

**Currency Group Analysis:**
```python
# EUR-based pairs
EUR_PAIRS = ['euraud', 'eurcad', 'eurchf', 'eurgbp', 'eurjpy', 'eurnzd', 'eurusd']

# USD-based pairs
USD_PAIRS = ['audusd', 'eurusd', 'gbpusd', 'nzdusd', 'usdcad', 'usdchf', 'usdjpy']

# GBP-based pairs
GBP_PAIRS = ['eurgbp', 'gbpaud', 'gbpcad', 'gbpchf', 'gbpjpy', 'gbpnzd', 'gbpusd']

# Calculate intra-group correlations
eur_corr = calculate_cross_pair_correlations(EUR_PAIRS)
usd_corr = calculate_cross_pair_correlations(USD_PAIRS)
gbp_corr = calculate_cross_pair_correlations(GBP_PAIRS)
```

**Expected Patterns:**
- **EUR pairs:** High positive correlation (share EUR exposure)
- **USD pairs:** Moderate correlation (USD as quote currency)
- **Cross-currency:** Lower correlation (independent movements)

### 3.2 Lead-Lag Relationships

**Objective:** Find which pairs lead or lag others

**Method:**
```python
def calculate_lead_lag_correlations(pair1, pair2, feature='w60_bqx_return', max_lag=15):
    """
    Calculate correlations at different time lags.

    Args:
        pair1: Leading pair
        pair2: Lagging pair
        feature: Feature to analyze
        max_lag: Maximum lag in minutes

    Returns:
        DataFrame: Correlations at each lag
    """
    df1 = load_pair_data(pair1)[feature]
    df2 = load_pair_data(pair2)[feature]

    lags = range(-max_lag, max_lag + 1)
    correlations = []

    for lag in lags:
        if lag < 0:
            # pair1 leads pair2
            corr = df1.iloc[:lag].corr(df2.iloc[-lag:])
        elif lag > 0:
            # pair2 leads pair1
            corr = df1.iloc[lag:].corr(df2.iloc[:-lag])
        else:
            # No lag
            corr = df1.corr(df2)

        correlations.append({
            'lag_minutes': lag,
            'correlation': corr,
            'interpretation': 'pair1 leads' if lag < 0 else 'pair2 leads' if lag > 0 else 'simultaneous'
        })

    return pd.DataFrame(correlations)
```

**Example Output:**
```
Lag (minutes)  Correlation  Interpretation
-------------- -----------  ----------------
-5             0.823        EURUSD leads GBPUSD by 5 min
0              0.789        Simultaneous
+5             0.645        GBPUSD leads EURUSD by 5 min
```

**Interpretation:**
- **Negative lag (pair1 leads):** Use pair1 movement to predict pair2
- **Positive lag (pair2 leads):** Use pair2 movement to predict pair1
- **ML Feature:** Add lagged features (e.g., eurusd_w60_return_lag5)

---

## Part 4: Cross-Window Correlation Strategy

### 4.1 Multi-Horizon Analysis

**Objective:** Understand how short-term features relate to long-term outcomes

**Method:**
```python
def calculate_cross_window_feature_matrix(df, feature_base='quadratic_term'):
    """
    Create matrix of same feature across different windows.

    Args:
        df: DataFrame with multi-window features
        feature_base: Base feature name (e.g., 'quadratic_term', 'r2')

    Returns:
        DataFrame: Feature values across all windows
    """
    windows = [60, 90, 150, 240, 390, 630]

    feature_matrix = {}
    for window in windows:
        col_name = f'w{window}_{feature_base}'
        if col_name in df.columns:
            feature_matrix[f'w{window}'] = df[col_name]

    return pd.DataFrame(feature_matrix)
```

**Correlation Analysis:**
```python
def analyze_window_consistency(df, feature_base='quadratic_term'):
    """
    Analyze how consistent features are across windows.

    Args:
        df: DataFrame with features
        feature_base: Feature to analyze

    Returns:
        dict: Consistency metrics
    """
    feature_matrix = calculate_cross_window_feature_matrix(df, feature_base)

    # Calculate correlation matrix
    corr_matrix = feature_matrix.corr()

    # Calculate consistency score (average correlation)
    consistency_score = corr_matrix.mean().mean()

    # Find most stable window (highest avg correlation with others)
    most_stable_window = corr_matrix.mean(axis=1).idxmax()

    # Find divergent windows (low correlation with others)
    divergent_windows = corr_matrix.mean(axis=1).nsmallest(2).index.tolist()

    return {
        'consistency_score': consistency_score,
        'most_stable_window': most_stable_window,
        'divergent_windows': divergent_windows,
        'correlation_matrix': corr_matrix
    }
```

**Example Output:**
```
Consistency Score: 0.87 (high - features align across windows)
Most Stable Window: w150 (2.5 hours - good balance)
Divergent Windows: ['w60', 'w630'] (too short/long)

Correlation Matrix:
       w60   w90   w150  w240  w390  w630
w60    1.00  0.92  0.85  0.78  0.71  0.63
w90    0.92  1.00  0.94  0.89  0.82  0.74
w150   0.85  0.94  1.00  0.96  0.91  0.84
w240   0.78  0.89  0.96  1.00  0.95  0.89
w390   0.71  0.82  0.91  0.95  1.00  0.94
w630   0.63  0.74  0.84  0.89  0.94  1.00
```

**Interpretation:**
- **High consistency (>0.80):** Feature is stable across time horizons
- **Low consistency (<0.60):** Feature changes significantly with window size
- **ML Strategy:** Use multiple windows for robust predictions

### 4.2 Window Weighting Strategy

**Objective:** Determine optimal weights for different windows

**Method:**
```python
def calculate_optimal_window_weights(df, target='w60_bqx_return'):
    """
    Calculate optimal weights for multi-window prediction.

    Args:
        df: DataFrame with multi-window features
        target: Target variable

    Returns:
        dict: Optimal weights for each window
    """
    from sklearn.linear_model import ElasticNet

    # Create feature matrix (same feature across all windows)
    windows = [60, 90, 150, 240, 390, 630]
    X = df[[f'w{w}_quadratic_term' for w in windows]].fillna(0)
    y = df[target]

    # Fit ElasticNet (combines L1 and L2 regularization)
    model = ElasticNet(alpha=0.1, l1_ratio=0.5)
    model.fit(X, y)

    # Extract weights
    weights = dict(zip([f'w{w}' for w in windows], model.coef_))

    # Normalize to sum to 1
    total = sum(abs(w) for w in weights.values())
    normalized_weights = {k: v/total for k, v in weights.items()}

    return normalized_weights
```

**Example Output:**
```
Window Weights (for BQX prediction):
w60:  0.35  (35% - most recent, highest weight)
w90:  0.25  (25% - second highest)
w150: 0.18  (18% - medium-term)
w240: 0.12  (12% - longer-term)
w390: 0.07  (7% - very long-term)
w630: 0.03  (3% - lowest weight, too distant)
```

**ML Application:**
```python
# Weighted feature
df['weighted_quadratic_term'] = (
    0.35 * df['w60_quadratic_term'] +
    0.25 * df['w90_quadratic_term'] +
    0.18 * df['w150_quadratic_term'] +
    0.12 * df['w240_quadratic_term'] +
    0.07 * df['w390_quadratic_term'] +
    0.03 * df['w630_quadratic_term']
)
```

---

## Part 5: Cross-Domain Correlation Strategy

### 5.1 Domain Alignment Analysis

**Objective:** Determine when rate_index and BQX domains agree or diverge

**Method:**
```python
def calculate_domain_alignment(df):
    """
    Calculate alignment between rate_index and BQX domains.

    Args:
        df: DataFrame with both domain features

    Returns:
        DataFrame: Alignment metrics
    """
    # R² alignment (both domains have good fit)
    df['domain_r2_alignment'] = df['rate_w60_r2'] * df['bqx_w60_r2']

    # Trend agreement (both domains show same trend direction)
    df['domain_trend_agreement'] = np.sign(df['rate_w60_linear']) == np.sign(df['bqx_w60_linear'])

    # Curvature agreement
    df['domain_curv_agreement'] = np.sign(df['rate_w60_quadratic']) == np.sign(df['bqx_w60_quadratic'])

    # Overall domain confidence
    df['domain_confidence'] = (
        df['domain_r2_alignment'] *
        df['domain_trend_agreement'].astype(float) *
        df['domain_curv_agreement'].astype(float)
    )

    return df
```

**Signal Strength Classification:**
```python
def classify_signal_strength(df):
    """
    Classify signal strength based on domain alignment.

    Args:
        df: DataFrame with domain alignment metrics

    Returns:
        DataFrame: Signal strength classification
    """
    conditions = [
        # Strong signal (both domains agree, high R²)
        (df['domain_confidence'] > 0.7) & (df['domain_trend_agreement']),

        # Medium signal (domains agree, moderate R²)
        (df['domain_confidence'] > 0.4) & (df['domain_trend_agreement']),

        # Weak signal (domains disagree or low R²)
        (df['domain_confidence'] > 0.2),

        # No signal (very low confidence)
        (df['domain_confidence'] <= 0.2)
    ]

    choices = ['STRONG', 'MEDIUM', 'WEAK', 'NONE']

    df['signal_strength'] = np.select(conditions, choices, default='NONE')

    return df
```

**Example Output:**
```
Timestamp              Rate_R²  BQX_R²  Trend_Agree  Curv_Agree  Confidence  Signal
--------------------- -------- ------- ------------ ----------- ----------- --------
2024-07-01 10:00:00   0.92     0.88    True         True        0.81        STRONG
2024-07-01 10:01:00   0.87     0.82    True         False       0.71        STRONG
2024-07-01 10:02:00   0.65     0.58    True         True        0.38        MEDIUM
2024-07-01 10:03:00   0.45     0.72    False        True        0.32        WEAK
```

**ML Application:**
- **STRONG signals:** High weight in prediction model
- **WEAK signals:** Low weight or filter out
- **Disagreement:** Indicates regime change or uncertainty

### 5.2 Domain-Specific Feature Selection

**Objective:** Identify which features work best in each domain

**Method:**
```python
def analyze_domain_specific_features(df, target='w60_bqx_return'):
    """
    Analyze which features are most predictive in each domain.

    Args:
        df: DataFrame with both domain features
        target: Target variable

    Returns:
        dict: Top features per domain
    """
    # Rate domain features
    rate_features = [col for col in df.columns if 'rate_' in col]

    # BQX domain features
    bqx_features = [col for col in df.columns if 'bqx_' in col]

    # Calculate correlations
    rate_corr = calculate_cross_feature_correlations(df[rate_features + [target]], target)
    bqx_corr = calculate_cross_feature_correlations(df[bqx_features + [target]], target)

    return {
        'rate_top_10': rate_corr.head(10).index.tolist(),
        'bqx_top_10': bqx_corr.head(10).index.tolist(),
        'rate_avg_corr': rate_corr['correlation'].abs().mean(),
        'bqx_avg_corr': bqx_corr['correlation'].abs().mean()
    }
```

**Example Output:**
```
Rate Domain Top Features:
1. rate_w60_linear (0.823)
2. rate_w60_r2 (0.789)
3. rate_w90_linear (0.756)

BQX Domain Top Features:
1. bqx_w60_linear (0.891)
2. corr_resid_lin_bqx_60min (0.847)
3. bqx_w60_residual (0.823)

Average Correlation:
Rate: 0.543
BQX: 0.612 (BQX features are more predictive!)
```

**Interpretation:**
- **BQX features stronger:** BQX domain directly measures momentum
- **Rate features complementary:** Provide different perspective
- **ML Strategy:** Use both domains, weight BQX higher

---

## Part 6: Triangulation Strategy

### 6.1 Multi-Signal Confirmation

**Objective:** Require multiple independent signals before making prediction

**Method:**
```python
def triangulate_signals(df):
    """
    Triangulate signals across domains, pairs, windows, and features.

    Args:
        df: DataFrame with all features

    Returns:
        DataFrame: Triangulated signal strength
    """
    # Signal 1: Domain Agreement
    domain_signal = (
        (df['rate_w60_linear'] > 0) & (df['bqx_w60_linear'] > 0)
    ).astype(int)  # 1 if both positive, 0 otherwise

    # Signal 2: Window Consistency
    window_signal = (
        (df['w60_linear'] > 0) & (df['w90_linear'] > 0) & (df['w150_linear'] > 0)
    ).astype(int)  # 1 if trend consistent across windows

    # Signal 3: Covariance Confirmation
    covariance_signal = (
        (df['corr_resid_lin_bqx_60min'] > 0.5)  # Breakout signal
    ).astype(int)

    # Signal 4: Regime Confirmation
    regime_signal = (
        (df['momentum_regime_bqx'] >= 3)  # Bullish regime
    ).astype(int)

    # Signal 5: Technical Confirmation
    technical_signal = (
        (df['rsi_14'] > 50) & (df['macd_histogram'] > 0)
    ).astype(int)

    # Triangulated Strength (0-5)
    df['triangulation_score'] = (
        domain_signal + window_signal + covariance_signal +
        regime_signal + technical_signal
    )

    # Classification
    df['triangulation_class'] = pd.cut(
        df['triangulation_score'],
        bins=[-1, 1, 2, 3, 5],
        labels=['WEAK', 'MEDIUM', 'STRONG', 'VERY_STRONG']
    )

    return df
```

**Decision Rules:**
```python
def make_ml_prediction_with_triangulation(df):
    """
    Make predictions only when triangulation score is sufficient.

    Args:
        df: DataFrame with triangulation scores

    Returns:
        DataFrame: Predictions with confidence levels
    """
    # Prediction strength based on triangulation
    conditions = [
        df['triangulation_score'] >= 4,  # Very strong (4-5 signals)
        df['triangulation_score'] >= 3,  # Strong (3 signals)
        df['triangulation_score'] >= 2,  # Medium (2 signals)
        df['triangulation_score'] >= 1,  # Weak (1 signal)
    ]

    # Prediction confidence
    confidence_levels = [0.95, 0.80, 0.60, 0.40]

    df['prediction_confidence'] = np.select(conditions, confidence_levels, default=0.20)

    # Only predict when confidence > threshold
    CONFIDENCE_THRESHOLD = 0.60
    df['make_prediction'] = df['prediction_confidence'] >= CONFIDENCE_THRESHOLD

    return df
```

**Example Output:**
```
Timestamp              Domain  Window  Covar  Regime  Technical  Score  Class       Confidence  Predict
--------------------- ------- ------- ------ ------- --------- ------ ----------- ----------- --------
2024-07-01 10:00:00   1       1       1      1       1         5      VERY_STRONG 0.95        YES
2024-07-01 10:01:00   1       1       1      0       1         4      VERY_STRONG 0.95        YES
2024-07-01 10:02:00   1       1       0      1       0         3      STRONG      0.80        YES
2024-07-01 10:03:00   1       0       1      0       0         2      MEDIUM      0.60        YES
2024-07-01 10:04:00   1       0       0      0       0         1      WEAK        0.40        NO
```

**Interpretation:**
- **Score 4-5:** Very strong signal (95% confidence, make prediction)
- **Score 3:** Strong signal (80% confidence, make prediction)
- **Score 2:** Medium signal (60% confidence, borderline)
- **Score 0-1:** Weak signal (don't predict, wait for clearer signal)

---

## Part 7: ML Model Integration

### 7.1 Feature Engineering Pipeline

**Complete Pipeline:**
```python
class BQXFeatureEngineer:
    """
    Complete feature engineering pipeline for BQX ML.
    """

    def __init__(self):
        self.windows = [60, 90, 150, 240, 390, 630]
        self.pairs = PAIRS  # All 28 pairs

    def create_feature_matrix(self, pair, year_month):
        """
        Create complete feature matrix for one pair/month.

        Args:
            pair: Currency pair
            year_month: Month partition

        Returns:
            DataFrame: Complete feature matrix
        """
        # Layer 1: Base features (regression terms)
        df_rate = self.load_reg_rate_features(pair, year_month)
        df_bqx = self.load_reg_bqx_features(pair, year_month)

        # Layer 2: Technical indicators
        df_technical = self.load_technical_indicators(pair, year_month)

        # Layer 3: Currency indices
        df_currency = self.load_currency_indices(pair, year_month)

        # Layer 4: Arbitrage
        df_arbitrage = self.load_arbitrage_features(pair, year_month)

        # Layer 5: Correlations + covariances
        df_correlation = self.load_correlation_features(pair, year_month)

        # Layer 6: Regime detection
        df_regime = self.load_regime_features(pair, year_month)

        # Layer 7: Enhanced RMSE
        df_enhanced_rmse = self.load_enhanced_rmse_features(pair, year_month)

        # Merge all layers
        df = df_rate.merge(df_bqx, on='ts_utc', suffixes=('_rate', '_bqx'))
        df = df.merge(df_technical, on='ts_utc')
        df = df.merge(df_currency, on='ts_utc')
        df = df.merge(df_arbitrage, on='ts_utc')
        df = df.merge(df_correlation, on='ts_utc')
        df = df.merge(df_regime, on='ts_utc')
        df = df.merge(df_enhanced_rmse, on='ts_utc')

        # Layer 8: Derived features
        df = self.add_derived_features(df)

        # Layer 9: Cross-pair features
        df = self.add_cross_pair_features(df, pair)

        # Layer 10: Triangulation
        df = self.add_triangulation_features(df)

        return df

    def add_derived_features(self, df):
        """Add cross-feature, cross-window, cross-domain features."""

        # Domain alignment
        df['domain_r2_alignment_w60'] = df['w60_r2_rate'] * df['w60_r2_bqx']

        # Window consistency
        for window in [60, 90, 150]:
            next_window = window + 30
            if f'w{next_window}_r2_rate' in df.columns:
                df[f'window_consistency_w{window}'] = (
                    df[f'w{window}_r2_rate'] / (df[f'w{next_window}_r2_rate'] + 0.01)
                )

        # Term ratios
        df['curvature_strength_w60_rate'] = (
            df['w60_quadratic_term_rate'].abs() / (df['w60_linear_term_rate'].abs() + 0.001)
        )

        df['curvature_strength_w60_bqx'] = (
            df['w60_quadratic_term_bqx'].abs() / (df['w60_linear_term_bqx'].abs() + 0.001)
        )

        # Normalized error
        df['normalized_error_w60_rate'] = (
            df['w60_residual_rate'] / (df['w60_rmse_rate'] + 0.001)
        )

        return df

    def add_cross_pair_features(self, df, current_pair):
        """Add features from correlated pairs."""

        # Find correlated pairs
        correlated_pairs = self.find_correlated_pairs(current_pair)

        for other_pair in correlated_pairs[:5]:  # Top 5 correlated
            # Load other pair's features
            df_other = self.load_reg_bqx_features(other_pair, year_month)

            # Add as features
            df[f'{other_pair}_w60_linear'] = df_other['w60_linear_term']
            df[f'{other_pair}_w60_r2'] = df_other['w60_r2']

        return df

    def add_triangulation_features(self, df):
        """Add triangulation scores."""
        return triangulate_signals(df)
```

### 7.2 Model Training Strategy

**Ensemble Approach:**
```python
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
from sklearn.neural_network import MLPRegressor

class BQXMLModel:
    """
    Ensemble ML model for BQX prediction.
    """

    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, max_depth=10),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, max_depth=5),
            'elastic_net': ElasticNet(alpha=0.1, l1_ratio=0.5),
            'neural_net': MLPRegressor(hidden_layers=(100, 50), max_iter=500)
        }
        self.weights = None

    def train(self, X_train, y_train):
        """Train all models in ensemble."""
        for name, model in self.models.items():
            print(f"Training {name}...")
            model.fit(X_train, y_train)

        # Calculate optimal ensemble weights
        self.weights = self.calculate_ensemble_weights(X_train, y_train)

    def predict(self, X):
        """Make ensemble prediction."""
        predictions = {}
        for name, model in self.models.items():
            predictions[name] = model.predict(X)

        # Weighted average
        ensemble_pred = sum(
            self.weights[name] * predictions[name]
            for name in self.models.keys()
        )

        return ensemble_pred

    def calculate_ensemble_weights(self, X_val, y_val):
        """Calculate optimal weights for ensemble."""
        from sklearn.linear_model import Ridge

        # Get predictions from each model
        preds = np.column_stack([
            model.predict(X_val)
            for model in self.models.values()
        ])

        # Fit meta-model to find optimal weights
        meta_model = Ridge(alpha=1.0, positive=True)  # Weights must be positive
        meta_model.fit(preds, y_val)

        # Normalize weights to sum to 1
        weights_raw = meta_model.coef_
        weights_norm = weights_raw / weights_raw.sum()

        return dict(zip(self.models.keys(), weights_norm))
```

### 7.3 Feature Importance Analysis

**Extract Most Important Features:**
```python
def analyze_feature_importance(model, feature_names):
    """
    Analyze which features are most important.

    Args:
        model: Trained model
        feature_names: List of feature names

    Returns:
        DataFrame: Feature importance scores
    """
    # Get feature importances (for tree-based models)
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        importances = np.abs(model.coef_)
    else:
        return None

    # Create DataFrame
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    })

    importance_df = importance_df.sort_values('importance', ascending=False)

    return importance_df
```

**Expected Top Features:**
```
Feature                          Importance
-------------------------------- ----------
corr_resid_lin_bqx_60min         0.156
bqx_w60_linear_term              0.143
domain_r2_alignment_w60          0.128
triangulation_score              0.115
cov_quad_lin_bqx_60min          0.098
momentum_regime_bqx              0.087
rate_w60_r2                      0.072
eurusd_w60_linear (cross-pair)  0.065
```

---

## Part 8: Summary

### Maximization Strategy Overview

**4-Dimensional Feature Space:**
1. **Cross-Feature:** Combine regression × technical × currency × arbitrage × regime features
2. **Cross-Pair:** Leverage correlations across 28 forex pairs
3. **Cross-Window:** Integrate 6 time horizons (1-10.5 hours)
4. **Cross-Domain:** Triangulate rate_index and BQX domains

**Triangulation Approach:**
- **Level 1:** Individual features (730+ features)
- **Level 2:** Feature interactions (pairwise combinations)
- **Level 3:** Cross-pair confirmation (correlated pairs)
- **Level 4:** Cross-window confirmation (multiple horizons)
- **Level 5:** Cross-domain confirmation (rate + BQX)
- **Level 6:** Ensemble prediction (4 models weighted)

**ML Integration:**
- Complete feature matrix (730+ features per timestamp)
- Robust triangulation scoring (5-signal confirmation)
- Ensemble modeling (Random Forest + Gradient Boost + ElasticNet + Neural Net)
- Confidence-based prediction (only predict when triangulation score ≥ 3)

**Expected Performance:**
- **Accuracy:** 75-80% (with triangulation filtering)
- **Precision:** 80-85% (high-confidence predictions)
- **Coverage:** 60-70% (only predict when signals align)
- **Robustness:** Very high (multiple confirmation required)

---

**Status:** ML maximization strategy complete ✅
**Next:** Integrate with remediation plan and execute
