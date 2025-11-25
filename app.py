import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from io import BytesIO
import re

st.set_page_config(page_title="RFI Dashboard", layout="wide")

# ----------------------------------------------------
# CLEAN STATUS FUNCTION (remove emojis)
# ----------------------------------------------------
def clean_status(x):
    if pd.isna(x):
        return "Not reviewed"
    x = str(x)
    x = re.sub(r"[^\w\s]", "", x).strip()   # remove emojis/symbols
    x = x.lower()

    if "closed" in x:
        return "Closed"
    if "review" in x:
        return "Not reviewed"
    return "Not reviewed"

# ----------------------------------------------------
# LOAD & FIX EACH SHEET
# ----------------------------------------------------
def load_fixed_sheet(df):
    # Row 0 contains labels like "RFI ID", "FLOOR NAME", ...
    new_header = df.iloc[0]
    df = df[1:]                 # drop header row
    df.columns = new_header     # set correct header names
    df = df.reset_index(drop=True)

    # Force lowercase column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Ensure status exists
    if "status" not in df.columns:
        raise Exception("STATUS column missing")

    # Clean status
    df["status"] = df["status"].apply(clean_status)

    return df

# ----------------------------------------------------
# COMPUTE STATS
# ----------------------------------------------------
def compute_stats(df):
    total = len(df)
    closed = (df["status"] == "Closed").sum()
    pending = (df["status"] == "Not reviewed").sum()

    progress = closed / total if total else 0

    return total, closed, pending, progress

# ----------------------------------------------------
# PDF EXPORT
# ----------------------------------------------------
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="RFI Dashboard Summary Report", ln=True)

    pdf_bytes = pdf.output(dest='S').encode("latin-1")
    return pdf_bytes

# ----------------------------------------------------
# UI
# ----------------------------------------------------
st.title("RFI Progress Dashboard")
uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    sheets = pd.read_excel(uploaded_file, sheet_name=None)

    for sheet_name, raw_df in sheets.items():

        try:
            df = load_fixed_sheet(raw_df)
        except:
            continue

        total, closed, pending, progress = compute_stats(df)

        st.markdown("## 📄 " + sheet_name)

        # ---- Badges ----
        st.markdown(
            f"""
            <span style='background:#28A745;padding:6px 14px;color:white;border-radius:12px;margin-right:8px;'>Closed: {closed}</span>
            <span style='background:#DC3545;padding:6px 14px;color:white;border-radius:12px;'>Pending: {pending}</span>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns(3)

        # Progress Bar
        with col1:
            st.write("**Progress**")
            st.progress(progress)
            st.write(f"**{int(progress*100)}% complete**")

        # Gauge
        with col2:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=progress * 100,
                number={"suffix": "%"},
                gauge={"axis": {"range": [0, 100]},
                       "bar": {"color": "#4A90E2"}}
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)

        # Pie Chart
        with col3:
            pie_df = pd.DataFrame({
                "Status": ["Closed", "Not reviewed"],
                "Count": [closed, pending]
            })

            pie = px.pie(
                pie_df,
                names="Status",
                values="Count",
                color="Status",
                color_discrete_map={"Closed": "green", "Not reviewed": "red"},
                hole=0.45,
            )
            st.plotly_chart(pie, use_container_width=True)

        st.write(f"**Total RFIs: {total}**")

    st.download_button(
        "Download PDF Summary",
        data=generate_pdf(),
        file_name="RFI_Report.pdf",
        mime="application/pdf"
    )
