import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import matplotlib.ticker as mtick

def human_format(x, pos):
    if x >= 1_000_000_000:
        return f"{x/1_000_000_000:.1f}B"
    elif x >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    elif x >= 1_000:
        return f"{x/1_000:.1f}K"
    else:
        return f"{int(x)}"

# Page config
st.set_page_config(
    page_title="COVID-19 Hospital & ICU Capacity – A00837328",
    layout="wide"
)

st.title("COVID-19 Hospital & ICU Capacity Globally")

st.markdown(
    """
    **Goal:** Monitor hospital strain and ICU pressure across countries and WHO regions.
    """
)

# Load data
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Date_reported"] = pd.to_datetime(df["Date_reported"], errors="coerce")
    metric_cols = [
        "Covid_new_hospitalizations_last_7days",
        "Covid_new_icu_admissions_last_7days",
        "Covid_new_hospitalizations_last_28days",
        "Covid_new_icu_admissions_last_28days",
    ]
    for c in metric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

DATA_PATH = "whoCovid19.csv"
df = load_data(DATA_PATH)

# Reusable cards (style)
CARD_BG = "linear-gradient(135deg, #0A63B0 0%, #0A2740 100%)"
CARD_TEXT_COLOR = "white"
CARD_SHADOW = "0 4px 12px rgba(0,0,0,0.25)"

def insight_card(title: str, value: str) -> str:
    return f"""
    <div style="
        background: {CARD_BG};
        border-radius: 16px;
        padding: 16px 18px;
        box-shadow: {CARD_SHADOW};
        text-align: center;
        color: {CARD_TEXT_COLOR};
        font-family: 'Segoe UI', sans-serif;
        height: 125px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    ">
        <div style="font-size: 1.3rem; opacity: 0.9; font-weight: 500;">
            {title}
        </div>
        <div style="font-size: 1.6rem; font-weight: 700; margin-top: 2px;">
            {value}
        </div>
    </div>
    """

st.divider()

# FILTER PANEL
st.markdown("### Filters")

f_left, f_right = st.columns(2)

with f_left:
    window = st.radio(
        "**Time window** // Select to show weekly or monthly data",
        ["Weekly (7 days)", "Monthly (28 days)"],
        index=0,
        horizontal=True,
    )

    if window.startswith("Weekly"):
        hosp_col = "Covid_new_hospitalizations_last_7days"
        icu_col = "Covid_new_icu_admissions_last_7days"
        window_desc = "last 7 days"
    else:
        hosp_col = "Covid_new_hospitalizations_last_28days"
        icu_col = "Covid_new_icu_admissions_last_28days"
        window_desc = "last 28 days"

with f_right:
    min_date = df["Date_reported"].min()
    max_date = df["Date_reported"].max()

    date_range = st.date_input(
        "**Date range** // Select the period to analyze",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

# Final filtered df – GLOBAL (all regions)
df_global = df[
    (df["Date_reported"] >= pd.to_datetime(start_date)) &
    (df["Date_reported"] <= pd.to_datetime(end_date))
]

if df_global.empty:
    st.warning("No data for the current filter selection.")
    st.stop()

st.divider()

st.markdown("### Key insights")

insights_container = st.container()


# Top insight cards
with insights_container:
    # Totals over the full filtered history
    total_hosp_hist = df_global["Covid_new_hospitalizations_last_7days"].sum()
    total_icu_hist  = df_global["Covid_new_icu_admissions_last_7days"].sum()

    # Peaks within the same filtered subset
    df_ts = (
        df_global
        .groupby("Date_reported", as_index=False)[[hosp_col, icu_col]]
        .sum()
    )

    peak_hosp = df_ts[hosp_col].max()
    peak_icu = df_ts[icu_col].max()


    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            insight_card(
                "Total hospitalizations",
                f"{int(total_hosp_hist):,}"
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            insight_card(
                "Total ICU admissions",
                f"{int(total_icu_hist):,}"
            ),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            insight_card(
                "Peak hospitalizations",
                f"{int(peak_hosp) if pd.notna(peak_hosp) else 0:,}"
            ),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            insight_card(
                "Peak ICU admissions",
                f"{int(peak_icu) if pd.notna(peak_icu) else 0:,}"
            ),
            unsafe_allow_html=True,
        )
st.markdown("### ")

# TABS
tab_overview, tab_corr, tab_country, tab_limits = st.tabs(
    #tab_regions
    [
        "1) Global evolution",
        "2) Hosp vs ICU",
        #"3) Countries total data",
        "4) Country trends",
        "5) Limitations & notes",
    ]
)

# 1) Global evolution
with tab_overview:
    st.markdown("### Global evolution of hospitalizations and ICU admissions")

    df_ts = (
        df_global
        .groupby("Date_reported", as_index=False)[[hosp_col, icu_col]]
        .sum()
        .sort_values("Date_reported")
    )

# Base line chart
    fig_ts = px.line(
        df_ts,
        x="Date_reported",
        y=[hosp_col, icu_col],
        labels={
            "value": "Number of patients",
            "variable": "Metric",
            "Date_reported": "Date",
        }
    )

    # Peak Markers

    # 1) Hospitalization peak
    hosp_peak_value = df_ts[hosp_col].max()
    hosp_peak_date = df_ts.loc[df_ts[hosp_col].idxmax(), "Date_reported"]

    fig_ts.add_scatter(
        x=[hosp_peak_date],
        y=[hosp_peak_value],
        mode="markers",
        marker=dict(size=12, color="gold", symbol="circle"),
        name="Highest peak",
        showlegend=True
    )

    # 2) ICU peak
    icu_peak_value = df_ts[icu_col].max()
    icu_peak_date = df_ts.loc[df_ts[icu_col].idxmax(), "Date_reported"]

    fig_ts.add_scatter(
        x=[icu_peak_date],
        y=[icu_peak_value],
        mode="markers",
        marker=dict(size=12, color="gold", symbol="circle"),
        name="Highest peak",
        showlegend=False
    )

    # Layout 
    fig_ts.update_layout(
        hovermode="x unified",
        legend_title="Metric",
    )

    st.plotly_chart(fig_ts, use_container_width=True)


# 2) Regions and peaks
#with tab_regions:

    # 3) Top 10 countries by total hospitalizations
 #   df_country_hosp = (
  #      df_global
   #    .sum()
   #     .rename(columns={"Covid_new_hospitalizations_last_7days": "Total_hospitalizations"})
   #     .sort_values("Total_hospitalizations", ascending=False)
   #     .head(10)
   # )

    #top3_countries_hosp = df_country_hosp["Country"].head(3).tolist()

    #st.write("#### Top 10 countries by total hospitalizations")
    #fig_cty_h, ax_ch = plt.subplots(figsize=(20, 2))
    #sns.barplot(
    #    data=df_country_hosp,
    #    x="Total_hospitalizations",
    #    y="Country",
    #    ax=ax_ch,
    #)
    #ax_ch.xaxis.set_major_formatter(mtick.FuncFormatter(human_format))

    #ax_ch.set_xlabel("Total hospitalizations (selected period)")
    #ax_ch.set_ylabel("Country")

    # highlight top 3 in blue, others in grey
    #for patch, country in zip(ax_ch.patches, df_country_hosp["Country"]):
    #    if country in top3_countries_hosp:
    #        patch.set_color("#1f77b4")
    #    else:
    #        patch.set_color("lightgray")

   # st.pyplot(fig_cty_h)

    #st.divider()

    # 4) Top 10 countries by total ICU admissions
    #df_country_icu = (
    #    df_global
    #    .groupby("Country", as_index=False)["Covid_new_icu_admissions_last_7days"]
    #    .sum()
    #    .rename(columns={"Covid_new_icu_admissions_last_7days": "Total_icu"})
    #    .sort_values("Total_icu", ascending=False)
    #    .head(10)
    #)

    #top3_countries_icu = df_country_icu["Country"].head(3).tolist()

    #st.write("#### Top 10 countries by total ICU admissions")
    #fig_cty_i, ax_ci = plt.subplots(figsize=(20, 2))
    #sns.barplot(
    #    data=df_country_icu,
    #    x="Total_icu",
    #    y="Country",
    #    ax=ax_ci,
    #)
    #ax_ci.xaxis.set_major_formatter(mtick.FuncFormatter(human_format))

   # ax_ci.set_xlabel("Total ICU admissions (selected period)")
   # ax_ci.set_ylabel("Country")

    # highlight top 3 in blue, others in grey
   # for patch, country in zip(ax_ci.patches, df_country_icu["Country"]):
   #     if country in top3_countries_icu:
   #         patch.set_color("#1f77b4")
   #     else:
   #         patch.set_color("lightgray")

   # st.pyplot(fig_cty_i)


# 3) Country trends
with tab_country:
    st.markdown("### Country-level trends")

    # Layout: left = options, right = chart
    c_opts, c_chart = st.columns([1, 3])

    # Options column
    with c_opts:
        view_mode = st.radio(
            "Country group",
            [
                "Top 5 countries globally",
                "Top 5 countries – AMR",
                "Top 5 countries – EUR",
                "Top 5 countries – AFR",
                "Top 5 countries – EMR",
                "Top 5 countries – SEAR",
                "Top 5 countries – WPR",
            ],
            index=0,
            key="country_group_mode",
        )

        metric_choice = st.radio(
            "Metric",
            ["Hospitalizations", "ICU admissions"],
            index=0,
            key="country_metric",
        )

        if metric_choice == "Hospitalizations":
            y_col = hosp_col
            y_label = f"New hospitalizations ({window_desc})"
        else:
            y_col = icu_col
            y_label = f"New ICU admissions ({window_desc})"

    # Determine scope (global or specific WHO region)
    region_map = {
        "Top 5 countries globally": None,
        "Top 5 countries – AMR": "AMR",
        "Top 5 countries – EUR": "EUR",
        "Top 5 countries – AFR": "AFR",
        "Top 5 countries – EMR": "EMR",
        "Top 5 countries – SEAR": "SEAR",
        "Top 5 countries – WPR": "WPR",
    }
    target_region = region_map[view_mode]

    if target_region is None:
        df_scope = df_global.copy()
    else:
        df_scope = df_global[df_global["WHO_region"] == target_region].copy()

    # If there is no data for that region, warn and stop
    if df_scope.empty:
        c_chart.warning("No data available for this region and date/time selection.")
    else:
        # Rank countries by TOTAL hospitalizations over the selected period
        df_rank = (
            df_scope
            .groupby("Country", as_index=False)["Covid_new_hospitalizations_last_7days"]
            .sum()
            .rename(columns={"Covid_new_hospitalizations_last_7days": "Total_hosp"})
            .sort_values("Total_hosp", ascending=False)
        )

        top_countries = df_rank["Country"].head(5).tolist()

        if not top_countries:
            c_chart.warning("No countries found for this selection.")
        else:
            df_country_ts = (
                df_scope[df_scope["Country"].isin(top_countries)]
                .sort_values("Date_reported")
            )

            with c_chart:
                fig_country = px.line(
                    df_country_ts,
                    x="Date_reported",
                    y=y_col,
                    color="Country",
                    labels={
                        "Date_reported": "Date",
                        y_col: y_label,
                    },
                )
                fig_country.update_layout(hovermode="x unified")
                st.plotly_chart(fig_country, use_container_width=True)


# 4) Hosp vs ICU
with tab_corr:
    st.markdown("### ICU share within total hospitalizations by WHO region")

    # Aggregate totals using WEEKLY (non-overlapping) values
    df_reg = (
        df_global
        .groupby("WHO_region", as_index=False)[
            ["Covid_new_hospitalizations_last_7days",
             "Covid_new_icu_admissions_last_7days"]
        ]
        .sum()
        .rename(columns={
            "Covid_new_hospitalizations_last_7days": "Total_hosp",
            "Covid_new_icu_admissions_last_7days": "Total_icu",
        })
    )

    # Avoid division by zero
    df_reg = df_reg[df_reg["Total_hosp"] > 0]

    # Calculate % ICU
    df_reg["ICU_pct"] = (df_reg["Total_icu"] / df_reg["Total_hosp"]) * 100

    # Sort regions by total hospitalizations
    df_reg = df_reg.sort_values("Total_hosp", ascending=False)

    fig, ax = plt.subplots(figsize=(20, 6))

    # Grey background bar = total hospitalizations
    ax.bar(
        df_reg["WHO_region"],
        df_reg["Total_hosp"],
        label="Hospitalizations (total)",
        color="lightgray",
    )

    # Blue bar = ICU admissions (bottom segment)
    ax.bar(
        df_reg["WHO_region"],
        df_reg["Total_icu"],
        label="ICU admissions",
        color="#1f77b4",
    )

    # Add ONLY percentage labels above the blue part
    xticks = ax.get_xticks()
    for x, (_, row) in zip(xticks, df_reg.iterrows()):
        ax.text(
            x,
            row["Total_icu"] + row["Total_hosp"] * 0.02,  # a bit above ICU height
            f'{row["ICU_pct"]:.1f}%',
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="#1f77b4",
        )

    ax.set_xlabel("WHO region")
    ax.set_ylabel("Total patients (weekly-based total over selected period)")
    ax.set_title("ICU load relative to hospitalizations")

    # Human-readable y-axis (K, M, B) – reuse your human_format if already defined
    import matplotlib.ticker as mtick

    def human_format(x, pos):
        if x >= 1_000_000_000:
            return f"{x/1_000_000_000:.1f}B"
        elif x >= 1_000_000:
            return f"{x/1_000_000:.1f}M"
        elif x >= 1_000:
            return f"{x/1_000:.1f}K"
        else:
            return f"{int(x)}"

    ax.yaxis.set_major_formatter(mtick.FuncFormatter(human_format))
    ax.legend()

    st.pyplot(fig)



# 5) Limitations
with tab_limits:
    st.markdown("### Data limitations, caveats and recommendations")

    st.markdown(
        """
        **Limitations**

        - The dataset focuses on hospitalizations and ICU admissions, not total infections or
          population, so it does not directly show incidence rates.
        - Reporting practices differ by country and can change over time, introducing noise and
          under/over-reporting bias.
        - Some dates and locations have missing values, especially in the 28-day indicators.

        Suggestions for future work

        - Combine this dataset with population to compute hospital/ICU rates per 100,000 inhabitants.  
        - Cross-link with vaccination or variant data to explain differences between waves.  
        - Add simple alerts or flags when countries exceed certain hospitalization or ICU thresholds.
        """
    )