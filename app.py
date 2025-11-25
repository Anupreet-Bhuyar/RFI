import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="RFI Dashboard", layout="wide")

# ---------------------------------------------------------
# CSS FOR UI
# ---------------------------------------------------------
st.markdown("""
<style>
body { background-color: #F5F7FA; }

.card {
    background: white;
    padding: 22px 28px;
    border-radius: 16px;
    margin-bottom: 25px;
    box-shadow: 0px 4px 14px rgba(0,0,0,0.06);
}

.title {
    font-size: 36px;
    font-weight: 700;
}

.badge {
    padding: 6px 14px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 13px;
    margin-right: 8px;
    color: white;
}

.badge-green { background: #28A745; }
.badge-red { background: #DC3545; }
.badge-yellow { background: #FFC107; color: black; }

.chip {
    display: inline-block;
    padding: 4px 12px;
    background: #EFEFEF;
    border-radius: 10px;
    margin: 3px;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# STATUS CLEANING
# ---------------------------------------------------------
def clean_status(x):
    if pd.isna(x):
        return "Not reviewed"
    x = str(x)
    x = re.sub(r"[^\w\s]", "", x)  # remove emojis/symbols
    x = x.strip().lower()
    if "closed" in x:
        return "Closed"
    if "review" in x:
        return "Not reviewed"
    return "Not reviewed"

# ---------------------------------------------------------
# LOAD AND FIX SHEET
# ---------------------------------------------------------
def load_sheet(df_raw):
    # first row is header row
    new_header = df_raw.iloc[0]
    df = df_raw[1:].copy()
    df.columns = new_header
    df = df.reset_index(drop=True)

    # normalize column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # ensure status column exists
    if "status" in df.columns:
        df["status"] = df["status"].apply(clean_status)
    else:
        df["status"] = "Not reviewed"

    return df

# ---------------------------------------------------------
# STATS
# ---------------------------------------------------------
def compute_stats(df):
    total = len(df)
    closed = (df["status"] == "Closed").sum()
    pending = (df["status"] == "Not reviewed").sum()
    progress = closed / total if total else 0.0
    return total, closed, pending, progress

# ---------------------------------------------------------
# UI HEADER
# ---------------------------------------------------------
st.markdown("<div class='title'>RFI Progress Dashboard</div>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if uploaded_file:
    sheets = pd.read_excel(uploaded_file, sheet_name=None)

    for sheet_name, df_raw in sheets.items():
        df = load_sheet(df_raw)
        total, closed, pending, progress = compute_stats(df)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader(f"📄 {sheet_name}")

        # badges
        st.markdown(
            f"""
            <span class='badge badge-green'>Closed: {closed}</span>
            <span class='badge badge-red'>Pending: {pending}</span>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1.2, 1, 1])

        # -------- PROGRESS BAR --------
        with col1:
            st.write("**Progress**")
            st.progress(progress)
            st.write(f"### {int(progress * 100)}%")

        # -------- GAUGE (unique key) --------
        with col2:
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=progress * 100,
                    number={"suffix": "%"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "#4A90E2"},
                    },
                )
            )
            fig_gauge.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10))
            st.write("**Completion Gauge**")
            st.plotly_chart(
                fig_gauge,
                use_container_width=True,
                key=f"{sheet_name}_gauge"
            )

        # -------- PIE (unique key) --------
        with col3:
            pie_df = pd.DataFrame(
                {
                    "Status": ["Closed", "Not reviewed"],
                    "Count": [closed, pending],
                }
            )
            fig_pie = px.pie(
                pie_df,
                names="Status",
                values="Count",
                color="Status",
                color_discrete_map={"Closed": "green", "Not reviewed": "red"},
                hole=0.45,
            )
            fig_pie.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10))
            st.write("**Status Breakdown**")
            st.plotly_chart(
                fig_pie,
                use_container_width=True,
                key=f"{sheet_name}_pie"
            )

        # -------- STATUS CHIPS --------
        st.write("**Status values detected:**")
        unique_status = df["status"].unique()
        chips_html = "".join(
            f"<span class='chip'>{s}</span>" for s in unique_status
        )
        st.markdown(chips_html, unsafe_allow_html=True)

        st.write(f"**Total RFIs:** {total}")
        st.markdown("</div>", unsafe_allow_html=True)
