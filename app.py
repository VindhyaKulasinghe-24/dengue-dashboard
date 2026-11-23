import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# Page Configuration & Theme-Adaptive Formal Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sri Lanka Dengue Outbreak Prediction Dashboard",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(
    """
    <style>
    /* Global Typography & Formal Layout */
    html, body, [class*="css"] {
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        padding-left: clamp(1rem, 2.5vw, 2.75rem);
        padding-right: clamp(1rem, 2.5vw, 2.75rem);
        max-width: 100%;
    }

    /* Headings - inherit theme text color for guaranteed contrast */
    h1 {
        font-size: clamp(1.4rem, 2.3vw, 2.05rem) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
        line-height: 1.25 !important;
        margin-bottom: 0.25rem !important;
    }
    h2, h3 {
        font-size: clamp(1.05rem, 1.6vw, 1.35rem) !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }

    /* Responsive multi-column flex wrapping */
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.85rem !important;
    }

    /* Formal KPI Metric Cards - high contrast on both dark and light themes */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-top: 3px solid #3b82f6;
        padding: clamp(12px, 1.5vw, 16px) clamp(14px, 1.8vw, 20px);
        border-radius: 6px;
        height: 100%;
        box-sizing: border-box;
    }
    div[data-testid="stMetricValue"] > div {
        color: var(--text-color) !important;
        font-size: clamp(1.2rem, 1.75vw, 1.6rem) !important;
        font-weight: 600 !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: var(--text-color) !important;
        font-size: clamp(0.78rem, 1vw, 0.88rem) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        opacity: 0.85;
        white-space: normal !important;
    }

    /* Formal Header Callout Banner */
    .info-box {
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-left: 4px solid #3b82f6;
        padding: clamp(10px, 1.4vw, 14px) clamp(14px, 2vw, 18px);
        border-radius: 4px;
        margin-bottom: 1.25rem;
        font-size: clamp(0.85rem, 1.05vw, 0.95rem);
        line-height: 1.55;
    }

    /* Formal Summary Cards for Confusion Matrix Breakdown */
    .stat-card {
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-radius: 5px;
        padding: 12px 14px;
        margin-bottom: 0.65rem;
    }
    .stat-card-title {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        opacity: 0.85;
        margin-bottom: 4px;
    }
    .stat-card-value {
        font-size: 1.12rem;
        font-weight: 600;
    }
    .stat-card-sub {
        font-size: 0.82rem;
        opacity: 0.8;
    }

    /* Clean Navigation Tabs */
    div[data-baseweb="tab-list"] {
        overflow-x: auto !important;
        overflow-y: hidden !important;
        flex-wrap: nowrap !important;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
        gap: 0.5rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.28);
    }
    button[data-baseweb="tab"] {
        white-space: nowrap !important;
        padding-left: clamp(10px, 1.5vw, 18px) !important;
        padding-right: clamp(10px, 1.5vw, 18px) !important;
        font-size: clamp(0.84rem, 1.05vw, 0.95rem) !important;
        font-weight: 500 !important;
    }

    /* Tablet breakpoint (<= 1100px) */
    @media (max-width: 1100px) {
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            flex: 1 1 calc(50% - 0.85rem) !important;
            min-width: 240px !important;
        }
    }

    /* Mobile breakpoint (<= 640px) */
    @media (max-width: 640px) {
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        .block-container {
            padding-top: 0.75rem;
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_CONFIG = {
    "responsive": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

# -----------------------------------------------------------------------------
# High-Contrast Formal Color Palette (Visible on Dark & Light Backgrounds)
# -----------------------------------------------------------------------------
FAMILY_COLORS = {
    "Boosting": "#3b82f6",  # Formal Royal Blue
    "Bagging": "#14b8a6",   # Formal Teal
    "Stacking": "#cbd5e1",  # Light Slate Silver
}

CATEGORY_COLORS = {
    "Epidemiological (Case History)": "#3b82f6",
    "Weather & Climate": "#14b8a6",
    "Demographics & Seasonality": "#f59e0b",
    "Other": "#94a3b8",
}

FEATURE_LABELS = {
    "cases_vs_normal": "Cases vs. Normal Threshold",
    "cases": "Current Week Cases",
    "cases_avg4": "4-Week Rolling Average Cases",
    "cases_lag1": "Cases (1 Week Lag)",
    "cases_lag2": "Cases (2 Weeks Lag)",
    "cases_lag3": "Cases (3 Weeks Lag)",
    "population_density": "Population Density",
    "temp_max_c": "Maximum Temperature (°C)",
    "temp_min_c": "Minimum Temperature (°C)",
    "week": "Week of Year",
    "month": "Month of Year",
    "rain_lag4": "Rainfall (4 Weeks Lag)",
    "rain_lag3": "Rainfall (3 Weeks Lag)",
    "rain_lag2": "Rainfall (2 Weeks Lag)",
    "rain_lag1": "Rainfall (1 Week Lag)",
    "rain_sum4": "4-Week Cumulative Rainfall (mm)",
    "rainfall_mm": "Current Week Rainfall (mm)",
    "humidity_pct": "Relative Humidity (%)",
}

FEATURE_CATEGORIES = {
    "cases_vs_normal": "Epidemiological (Case History)",
    "cases": "Epidemiological (Case History)",
    "cases_avg4": "Epidemiological (Case History)",
    "cases_lag1": "Epidemiological (Case History)",
    "cases_lag2": "Epidemiological (Case History)",
    "cases_lag3": "Epidemiological (Case History)",
    "population_density": "Demographics & Seasonality",
    "week": "Demographics & Seasonality",
    "month": "Demographics & Seasonality",
    "temp_max_c": "Weather & Climate",
    "temp_min_c": "Weather & Climate",
    "rain_lag4": "Weather & Climate",
    "rain_lag3": "Weather & Climate",
    "rain_lag2": "Weather & Climate",
    "rain_lag1": "Weather & Climate",
    "rain_sum4": "Weather & Climate",
    "rainfall_mm": "Weather & Climate",
    "humidity_pct": "Weather & Climate",
}

METRIC_INFO = {
    "ROC_AUC": {
        "label": "ROC-AUC (Discrimination)",
        "short": "ROC-AUC",
        "desc": "Measures how effectively the model separates outbreak weeks from non-outbreak weeks across all decision thresholds (1.0 = ideal).",
        "higher_is_better": True,
    },
    "F1": {
        "label": "F1 Score (Precision-Recall Balance)",
        "short": "F1 Score",
        "desc": "Harmonic mean of Precision and Recall. Evaluates the balance between missed outbreaks and false positives.",
        "higher_is_better": True,
    },
    "Accuracy": {
        "label": "Accuracy (Overall Correctness)",
        "short": "Accuracy",
        "desc": "Proportion of all district-weeks (both outbreak and normal) classified correctly.",
        "higher_is_better": True,
    },
    "Precision": {
        "label": "Precision (Positive Predictive Value)",
        "short": "Precision",
        "desc": "Proportion of predicted outbreak alerts that correspond to actual outbreaks.",
        "higher_is_better": True,
    },
    "Recall": {
        "label": "Recall (Sensitivity)",
        "short": "Recall",
        "desc": "Proportion of actual outbreaks successfully identified by the model.",
        "higher_is_better": True,
    },
    "Train_sec": {
        "label": "Training Duration (Seconds)",
        "short": "Train Time (s)",
        "desc": "Elapsed time required to fit the model on the training partition (lower is faster).",
        "higher_is_better": False,
    },
}

# Custom non-overlapping label positions for the 9 ensemble models
SCATTER_TEXT_POS = {
    "CatBoost": "top right",
    "XGBoost": "top center",
    "LightGBM": "bottom center",
    "Random Forest": "bottom right",
    "Extra Trees": "top center",
    "AdaBoost": "top center",
    "Stacking": "top center",
    "Gradient Boosting": "top left",
    "Bagging (trees)": "bottom left",
}


def apply_formal_layout(fig, height=430, bottom_margin=65, is_horizontal_bar=False):
    """Applies clean spacing and subtle gridlines without overriding Streamlit's theme-adaptive text contrast."""
    fig.update_layout(
        autosize=True,
        height=height,
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", size=12),
        title=dict(font=dict(size=15)),
        margin=dict(l=12, r=35, t=48, b=bottom_margin),
        xaxis=dict(
            automargin=True,
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.18)",
            zeroline=False,
        ),
        yaxis=dict(
            automargin=True,
            showgrid=not is_horizontal_bar,
            gridcolor="rgba(148, 163, 184, 0.18)",
            zeroline=False,
        ),
    )
    return fig


# -----------------------------------------------------------------------------
# Data Loading
# -----------------------------------------------------------------------------
D = "dashboard_data"
RAW_CSV = "dengue_srilanka_full_2006_2025.csv"


@st.cache_data
def load_dashboard_data():
    res_df = pd.read_csv(f"{D}/results.csv")
    imp_s = pd.read_csv(f"{D}/importance.csv", index_col=0).iloc[:, 0]
    with open(f"{D}/confusion.json", "r", encoding="utf-8") as f:
        cm_data = json.load(f)
    hyb_df = pd.read_csv(f"{D}/hybrid_scores.csv")
    hp_df = pd.read_csv(f"{D}/hybrid_preds.csv")
    if "date" in hp_df.columns:
        hp_df["date"] = pd.to_datetime(hp_df["date"])
    return res_df, imp_s, cm_data, hyb_df, hp_df


@st.cache_data
def load_raw_dataset():
    if not os.path.exists(RAW_CSV):
        return None
    df = pd.read_csv(RAW_CSV)
    df["date"] = pd.to_datetime(df["end.date"])
    return df


res, imp, cm, hyb, hp = load_dashboard_data()

# -----------------------------------------------------------------------------
# Sidebar Controls & Methodology Reference
# -----------------------------------------------------------------------------
with st.sidebar:
    st.subheader("Analysis Parameters")

    all_families = sorted(res["Family"].unique())
    selected_families = st.multiselect(
        "Ensemble Architecture",
        options=all_families,
        default=all_families,
        help="Filter models by ensemble paradigm: Bagging, Boosting, or Stacking.",
    )
    if not selected_families:
        st.warning("Select at least one ensemble family. Resetting to all families.")
        selected_families = all_families

    metric_keys = list(METRIC_INFO.keys())
    selected_metric = st.selectbox(
        "Evaluation Metric",
        options=metric_keys,
        index=0,
        format_func=lambda k: METRIC_INFO[k]["label"],
    )

    st.caption(f"**{METRIC_INFO[selected_metric]['short']}**: {METRIC_INFO[selected_metric]['desc']}")

    st.divider()
    show_as_percent = st.toggle(
        "Format metrics as percentages (%)",
        value=True,
        help="Display normalized 0–1 metrics as percentages (0–100%).",
    )

    st.divider()
    with st.expander("Outbreak Definition & Methodology", expanded=False):
        st.markdown(
            """
            A district-week is classified as an **Outbreak** in the following week when both criteria are met:
            1. **Relative Threshold**: Next week's reported cases exceed the district's **52-week rolling 75th percentile**.
            2. **Absolute Floor**: Next week's reported cases are **at least 10**.
            """
        )

# -----------------------------------------------------------------------------
# Header & Executive KPI Cards
# -----------------------------------------------------------------------------
st.title("Sri Lanka Dengue Outbreak Prediction Dashboard")
st.markdown(
    f"""
    <div class="info-box">
        <strong>{cm.get("title", "Forecasting weekly district-level dengue outbreaks in Sri Lanka.")}</strong><br>
        Comparative evaluation of <strong>Bagging</strong>, <strong>Boosting</strong>, <strong>Stacking</strong>, and <strong>Hybrid (Random Forest + Neural Network)</strong> architectures trained on epidemiological and meteorological surveillance records (2006–2025).
    </div>
    """,
    unsafe_allow_html=True,
)

pick = res[res["Model"] == cm.get("best_model")]
best = pick.iloc[0] if len(pick) else res.sort_values("ROC_AUC", ascending=False).iloc[0]
fastest = res.sort_values("Train_sec", ascending=True).iloc[0]
avg_roc = res["ROC_AUC"].mean()
avg_f1 = res["F1"].mean()
avg_acc = res["Accuracy"].mean()


def fmt_score(val):
    return f"{val * 100:.1f}%" if show_as_percent else f"{val:.3f}"


def fmt_delta(val, ref):
    diff = val - ref
    return f"{diff * 100:+.1f}% vs. mean" if show_as_percent else f"{diff:+.3f} vs. mean"


k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(
    "Top Performing Model",
    best["Model"],
    f"{best['Family']} Architecture",
    delta_color="off",
    help="Model achieving the highest ROC-AUC on the out-of-sample test partition.",
)
k2.metric(
    "Best ROC-AUC",
    fmt_score(best["ROC_AUC"]),
    fmt_delta(best["ROC_AUC"], avg_roc),
    help=METRIC_INFO["ROC_AUC"]["desc"],
)
k3.metric(
    "Best Model F1 Score",
    fmt_score(best["F1"]),
    fmt_delta(best["F1"], avg_f1),
    help=METRIC_INFO["F1"]["desc"],
)
k4.metric(
    "Best Model Accuracy",
    fmt_score(best["Accuracy"]),
    fmt_delta(best["Accuracy"], avg_acc),
    help=METRIC_INFO["Accuracy"]["desc"],
)
k5.metric(
    "Fastest Training Time",
    fastest["Model"],
    f"{fastest['Train_sec']:.2f} s",
    delta_color="off",
    help="Model requiring the minimum computation time during training.",
)

st.write("")

# -----------------------------------------------------------------------------
# Main Navigation Tabs
# -----------------------------------------------------------------------------
tab_compare, tab_features, tab_hybrid, tab_explorer = st.tabs(
    [
        "Model Comparison",
        "Feature Importance & Error Analysis",
        "Hybrid Architecture & Forecast",
        "District Surveillance Explorer",
    ]
)

# =============================================================================
# TAB 1: MODEL COMPARISON
# =============================================================================
with tab_compare:
    filtered_res = res[res["Family"].isin(selected_families)].copy()
    ascending_sort = not METRIC_INFO[selected_metric]["higher_is_better"]
    view = filtered_res.sort_values(selected_metric, ascending=ascending_sort)

    col_chart1, col_chart2 = st.columns([1.35, 1.15])

    with col_chart1:
        plot_df = view.copy()
        is_time = selected_metric == "Train_sec"
        scale = 100.0 if (show_as_percent and not is_time) else 1.0
        plot_df["Display_Val"] = plot_df[selected_metric] * scale
        unit_suffix = "%" if (show_as_percent and not is_time) else (" s" if is_time else "")

        fig_bar = px.bar(
            plot_df,
            x="Display_Val",
            y="Model",
            color="Family",
            color_discrete_map=FAMILY_COLORS,
            orientation="h",
            text=plot_df["Display_Val"].map(lambda v: f"  {v:.1f}{unit_suffix}" if (show_as_percent or is_time) else f"  {v:.3f}"),
            title=f"Model Ranking by {METRIC_INFO[selected_metric]['short']}",
            labels={"Display_Val": METRIC_INFO[selected_metric]["short"], "Model": ""},
        )
        fig_bar.update_traces(
            textposition="outside",
            cliponaxis=False,
            marker_line_width=0,
        )
        apply_formal_layout(fig_bar, height=440, bottom_margin=65, is_horizontal_bar=True)
        fig_bar.update_layout(
            yaxis={"categoryorder": "total ascending" if not ascending_sort else "total descending", "automargin": True},
            legend_title_text="Architecture",
            legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        )
        max_val = plot_df["Display_Val"].max()
        fig_bar.update_xaxes(range=[0, max_val * 1.22])
        st.plotly_chart(fig_bar, width="stretch", config=PLOTLY_CONFIG)

    with col_chart2:
        scatter_df = filtered_res.copy()
        y_col = "ROC_AUC" if selected_metric == "Train_sec" else selected_metric
        y_scale = 100.0 if show_as_percent else 1.0
        scatter_df["Y_Plot"] = scatter_df[y_col] * y_scale

        fig_tradeoff = px.scatter(
            scatter_df,
            x="Train_sec",
            y="Y_Plot",
            color="Family",
            color_discrete_map=FAMILY_COLORS,
            size="Accuracy",
            text="Model",
            title=f"Computational Efficiency vs. {METRIC_INFO[y_col]['short']}",
            labels={
                "Train_sec": "Training Time (Seconds)",
                "Y_Plot": f"{METRIC_INFO[y_col]['short']} {'(%)' if show_as_percent else ''}",
            },
        )
        # Apply non-overlapping text positions per model and high-visibility marker borders
        for trace in fig_tradeoff.data:
            positions = [SCATTER_TEXT_POS.get(m, "top center") for m in trace.text]
            trace.textposition = positions
            trace.marker.line = dict(width=1.5, color="rgba(255, 255, 255, 0.7)")
            trace.cliponaxis = False

        apply_formal_layout(fig_tradeoff, height=440, bottom_margin=65, is_horizontal_bar=False)
        x_max = scatter_df["Train_sec"].max()
        y_min, y_max = scatter_df["Y_Plot"].min(), scatter_df["Y_Plot"].max()
        y_pad = max((y_max - y_min) * 0.18, 0.8 if show_as_percent else 0.008)
        fig_tradeoff.update_layout(
            xaxis=dict(range=[-1.2, x_max * 1.18], automargin=True),
            yaxis=dict(range=[y_min - y_pad, y_max + y_pad], automargin=True),
            legend_title_text="Architecture",
            legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_tradeoff, width="stretch", config=PLOTLY_CONFIG)

    st.subheader("Comparative Performance Table")
    st.caption("Evaluation metrics computed on the chronologically held-out test set (final 20% of observation period).")

    table_df = filtered_res.sort_values(selected_metric, ascending=ascending_sort).reset_index(drop=True)
    score_cols = ["Accuracy", "Precision", "Recall", "F1", "ROC_AUC"]
    if show_as_percent:
        for c in score_cols:
            table_df[c] = (table_df[c] * 100).round(2)
        max_bar = 100.0
        fmt_str = "%.2f%%"
    else:
        max_bar = 1.0
        fmt_str = "%.4f"

    st.dataframe(
        table_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Model": st.column_config.TextColumn("Model", width="medium"),
            "Family": st.column_config.TextColumn("Architecture", width="small"),
            "ROC_AUC": st.column_config.ProgressColumn("ROC-AUC", format=fmt_str, min_value=0, max_value=max_bar),
            "F1": st.column_config.ProgressColumn("F1 Score", format=fmt_str, min_value=0, max_value=max_bar),
            "Accuracy": st.column_config.ProgressColumn("Accuracy", format=fmt_str, min_value=0, max_value=max_bar),
            "Precision": st.column_config.ProgressColumn("Precision", format=fmt_str, min_value=0, max_value=max_bar),
            "Recall": st.column_config.ProgressColumn("Recall", format=fmt_str, min_value=0, max_value=max_bar),
            "Train_sec": st.column_config.NumberColumn("Train Time (s)", format="%.2f s"),
        },
    )

# =============================================================================
# TAB 2: FEATURE IMPORTANCE & CONFUSION MATRIX
# =============================================================================
with tab_features:
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Predictive Feature Importance")
        st.caption("Relative contribution of epidemiological, meteorological, and demographic variables (Random Forest estimator).")

        top_n = st.slider("Number of features displayed", min_value=5, max_value=len(imp), value=min(12, len(imp)))

        imp_df = imp.sort_values(ascending=False).head(top_n).sort_values(ascending=True).reset_index()
        imp_df.columns = ["raw_feature", "importance"]
        imp_df["Feature"] = imp_df["raw_feature"].map(lambda x: FEATURE_LABELS.get(x, x))
        imp_df["Category"] = imp_df["raw_feature"].map(lambda x: FEATURE_CATEGORIES.get(x, "Other"))
        imp_df["Importance_Pct"] = imp_df["importance"] * 100

        fi_fig = px.bar(
            imp_df,
            x="Importance_Pct",
            y="Feature",
            color="Category",
            orientation="h",
            text=imp_df["Importance_Pct"].map(lambda v: f"  {v:.1f}%"),
            title=f"Top {top_n} Predictors by Relative Importance",
            labels={"Importance_Pct": "Importance Share (%)", "Feature": ""},
            color_discrete_map=CATEGORY_COLORS,
        )
        fi_fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        apply_formal_layout(fi_fig, height=470, bottom_margin=75, is_horizontal_bar=True)
        fi_fig.update_layout(
            yaxis={"categoryorder": "total ascending", "automargin": True},
            legend_title_text="",
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        )
        fi_fig.update_xaxes(range=[0, imp_df["Importance_Pct"].max() * 1.24])
        st.plotly_chart(fi_fig, width="stretch", config=PLOTLY_CONFIG)

        st.markdown(
            """
            <div class="info-box">
                <strong>Analytical Note:</strong> Recent epidemiological momentum—specifically <strong>Cases vs. Normal Threshold (41.0%)</strong> and lagged case counts—accounts for the majority of predictive power, while 2–4 week lagged rainfall and temperature provide secondary environmental signals.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.subheader(f"Classification Error Analysis ({cm['best_model']})")
        st.caption("Out-of-sample confusion matrix across 4,825 district-week observations.")

        matrix = cm["matrix"]
        tn, fp = matrix[0][0], matrix[0][1]
        fn, tp = matrix[1][0], matrix[1][1]
        total = tn + fp + fn + tp

        annot_text = [
            [
                f"<b>{tn:,}</b> ({tn / total * 100:.1f}%)<br>True Negative",
                f"<b>{fp:,}</b> ({fp / total * 100:.1f}%)<br>False Positive",
            ],
            [
                f"<b>{fn:,}</b> ({fn / total * 100:.1f}%)<br>False Negative",
                f"<b>{tp:,}</b> ({tp / total * 100:.1f}%)<br>True Positive",
            ],
        ]

        cm_fig = go.Figure(
            data=go.Heatmap(
                z=matrix,
                x=[f"Predicted: {l}" for l in cm["labels"]],
                y=[f"Actual: {l}" for l in cm["labels"]],
                text=annot_text,
                texttemplate="%{text}",
                textfont=dict(color="#f8fafc", size=13),
                colorscale=[[0.0, "#1e293b"], [0.4, "#1e3a8a"], [1.0, "#2563eb"]],
                showscale=False,
                xgap=3,
                ygap=3,
            )
        )
        apply_formal_layout(cm_fig, height=340, bottom_margin=25, is_horizontal_bar=True)
        cm_fig.update_layout(
            title=f"Confusion Matrix — {cm['best_model']}",
            xaxis=dict(showgrid=False, automargin=True),
            yaxis=dict(autorange="reversed", showgrid=False, automargin=True),
        )
        st.plotly_chart(cm_fig, width="stretch", config=PLOTLY_CONFIG)

        m1, m2 = st.columns(2)
        with m1:
            st.markdown(
                f"""
                <div class="stat-card" style="border-left: 3px solid #3b82f6;">
                    <div class="stat-card-title">True Negatives (Specificity: {tn / (tn + fp) * 100:.1f}%)</div>
                    <div class="stat-card-value">{tn:,} district-weeks</div>
                    <div class="stat-card-sub">Non-outbreak weeks accurately identified</div>
                </div>
                <div class="stat-card" style="border-left: 3px solid #94a3b8;">
                    <div class="stat-card-title">False Positives (False Discovery: {fp / (tp + fp) * 100:.1f}%)</div>
                    <div class="stat-card-value">{fp:,} district-weeks</div>
                    <div class="stat-card-sub">Alerts issued without subsequent outbreak</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f"""
                <div class="stat-card" style="border-left: 3px solid #14b8a6;">
                    <div class="stat-card-title">True Positives (Sensitivity: {tp / (tp + fn) * 100:.1f}%)</div>
                    <div class="stat-card-value">{tp:,} district-weeks</div>
                    <div class="stat-card-sub">Outbreak weeks successfully detected</div>
                </div>
                <div class="stat-card" style="border-left: 3px solid #f59e0b;">
                    <div class="stat-card-title">False Negatives (Miss Rate: {fn / (tp + fn) * 100:.1f}%)</div>
                    <div class="stat-card-value">{fn:,} district-weeks</div>
                    <div class="stat-card-sub">Outbreak weeks not flagged in advance</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# =============================================================================
# TAB 3: HYBRID MODEL & FORECAST TRENDS
# =============================================================================
with tab_hybrid:
    st.subheader("Hybrid Ensemble Evaluation (Random Forest + Multi-Layer Perceptron)")
    st.caption(
        "Comparison of standalone Random Forest, standalone Artificial Neural Network (ANN), equal-weighted Hybrid (RF + ANN), and a non-ML persistence baseline."
    )

    h_left, h_right = st.columns([1.1, 1.4])

    with h_left:
        hyb_melt = hyb.melt(id_vars="Model", value_vars=["Accuracy", "F1", "ROC_AUC"], var_name="Metric", value_name="Score")
        hyb_melt["Score_Display"] = hyb_melt["Score"] * (100.0 if show_as_percent else 1.0)

        fig_hyb = px.bar(
            hyb_melt,
            x="Model",
            y="Score_Display",
            color="Metric",
            barmode="group",
            text=hyb_melt["Score_Display"].map(lambda v: f"{v:.1f}%" if show_as_percent else f"{v:.3f}"),
            title="Hybrid Architecture vs. Baselines",
            labels={"Score_Display": "Score (%)" if show_as_percent else "Score", "Model": ""},
            color_discrete_sequence=["#3b82f6", "#14b8a6", "#cbd5e1"],
        )
        fig_hyb.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        apply_formal_layout(fig_hyb, height=390, bottom_margin=75)
        fig_hyb.update_layout(
            xaxis=dict(showgrid=False, automargin=True),
            yaxis=dict(range=[0, 114 if show_as_percent else 1.14], automargin=True),
            legend_title_text="",
            legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_hyb, width="stretch", config=PLOTLY_CONFIG)

        st.dataframe(hyb, width="stretch", hide_index=True)

    with h_right:
        if "date" in hp.columns:
            st.markdown("#### National Outbreak Proportion vs. Hybrid Forecast")
            st.caption(
                "Weekly proportion of Sri Lankan districts experiencing an outbreak compared against the Hybrid model's mean predicted risk."
            )

            min_date = hp["date"].min().date()
            max_date = hp["date"].max().date()

            c_date, c_smooth = st.columns([2, 1])
            with c_date:
                date_range = st.date_input(
                    "Observation Window",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                )
            with c_smooth:
                smooth_window = st.selectbox(
                    "Temporal Smoothing",
                    options=[1, 2, 4],
                    index=0,
                    format_func=lambda w: "Unfiltered (1 Week)" if w == 1 else f"{w}-Week Moving Average",
                )

            hp_filtered = hp.copy()
            if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
                hp_filtered = hp_filtered[(hp_filtered["date"] >= start_d) & (hp_filtered["date"] <= end_d)].copy()

            scale_ts = 100.0 if show_as_percent else 1.0
            hp_filtered["Observed Outbreak Proportion"] = (
                hp_filtered["actual"].rolling(smooth_window, min_periods=1).mean() * scale_ts
            )
            hp_filtered["Hybrid Predicted Probability"] = (
                hp_filtered["hybrid"].rolling(smooth_window, min_periods=1).mean() * scale_ts
            )

            fig_ts = px.line(
                hp_filtered,
                x="date",
                y=["Observed Outbreak Proportion", "Hybrid Predicted Probability"],
                title="Out-of-Sample Temporal Trajectory (2022–2025)",
                labels={
                    "date": "Week Ending Date",
                    "value": "Proportion / Probability (%)" if show_as_percent else "Proportion / Probability",
                    "variable": "",
                },
                color_discrete_map={
                    "Observed Outbreak Proportion": "#3b82f6",
                    "Hybrid Predicted Probability": "#14b8a6",
                },
            )
            apply_formal_layout(fig_ts, height=410, bottom_margin=65)
            fig_ts.update_layout(
                legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
                hovermode="x unified",
            )
            st.plotly_chart(fig_ts, width="stretch", config=PLOTLY_CONFIG)

# =============================================================================
# TAB 4: SRI LANKA DISTRICT EXPLORER
# =============================================================================
with tab_explorer:
    raw_df = load_raw_dataset()
    if raw_df is None:
        st.info(f"Historical surveillance dataset (`{RAW_CSV}`) was not found in the working directory.")
    else:
        st.subheader("District-Level Epidemiological & Meteorological Records (2006–2025)")
        st.caption("Historical weekly dengue case counts and climate covariates across all 26 districts in Sri Lanka.")

        districts = sorted(raw_df["district"].unique())
        default_dist = "Colombo" if "Colombo" in districts else districts[0]

        f1, f2, f3 = st.columns([1.5, 1.5, 1])
        with f1:
            selected_district = st.selectbox("District", options=districts, index=districts.index(default_dist))
        with f2:
            min_yr, max_yr = int(raw_df["year"].min()), int(raw_df["year"].max())
            year_range = st.slider("Year Interval", min_value=min_yr, max_value=max_yr, value=(max(min_yr, 2018), max_yr))
        with f3:
            weather_overlay = st.selectbox(
                "Meteorological Covariate",
                options=["rainfall_mm", "temp_max_c", "humidity_pct"],
                format_func=lambda c: {
                    "rainfall_mm": "Weekly Rainfall (mm)",
                    "temp_max_c": "Maximum Temperature (°C)",
                    "humidity_pct": "Relative Humidity (%)",
                }[c],
            )

        dist_df = raw_df[
            (raw_df["district"] == selected_district)
            & (raw_df["year"] >= year_range[0])
            & (raw_df["year"] <= year_range[1])
        ].sort_values("date")

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Province", dist_df["province"].iloc[0] if len(dist_df) else "N/A")
        d2.metric("Cumulative Cases (Selected Period)", f"{int(dist_df['cases'].sum()):,}")
        d3.metric("Peak Weekly Incidence", f"{int(dist_df['cases'].max()):,}" if len(dist_df) else "0")
        d4.metric("Mean Weekly Rainfall", f"{dist_df['rainfall_mm'].mean():.1f} mm" if len(dist_df) else "N/A")

        c_cases, c_weather = st.columns(2)
        with c_cases:
            fig_cases = px.area(
                dist_df,
                x="date",
                y="cases",
                title=f"Weekly Reported Dengue Cases — {selected_district} ({year_range[0]}–{year_range[1]})",
                labels={"date": "Week Ending Date", "cases": "Reported Cases"},
                color_discrete_sequence=["#3b82f6"],
            )
            apply_formal_layout(fig_cases, height=360, bottom_margin=30)
            fig_cases.update_layout(hovermode="x unified")
            st.plotly_chart(fig_cases, width="stretch", config=PLOTLY_CONFIG)

        with c_weather:
            weather_label = {
                "rainfall_mm": "Weekly Rainfall (mm)",
                "temp_max_c": "Maximum Temperature (°C)",
                "humidity_pct": "Relative Humidity (%)",
            }[weather_overlay]
            fig_weather = px.line(
                dist_df,
                x="date",
                y=weather_overlay,
                title=f"{weather_label} — {selected_district} ({year_range[0]}–{year_range[1]})",
                labels={"date": "Week Ending Date", weather_overlay: weather_label},
                color_discrete_sequence=["#14b8a6"],
            )
            apply_formal_layout(fig_weather, height=360, bottom_margin=30)
            fig_weather.update_layout(hovermode="x unified")
            st.plotly_chart(fig_weather, width="stretch", config=PLOTLY_CONFIG)
