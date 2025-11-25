import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from io import BytesIO

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="RFI Dashboard", layout="wide")

# ----------------------------------------------------
# GLOBAL CSS (MODERN CARDS + BADGES)
# ----------------------------------------------------
st.markdown("""
<style>
body { background-color: #F5F7FA; }
.big-title {
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 6px;
}
.section-card {
    background: #FFFFFF;
    padding: 22px 26px;
    border-radius: 16px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
    margin-bottom: 26px;
}
.badge {
    padding: 6px 14px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 13px;
    color: white;
    margin-right: 8px;
}
.badge-green { background: #28A745; }
.badge-yellow { background: #FFC107; color: black; }
.badge-red { background: #DC3545; }
.status-chip {
    display: inline-block;
    padding: 5px 12px;
    background: #EFEFEF;
    border-radius: 12px;
    margin: 3px;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# TITLE
# ----------------------------------------------------
st.markdown("<div class='big-title'>RFI Progress Dashboard</div>", unsafe_allow_html=True)
st.write("Upload one or two Excel files to visualize progress and compare versions.")

# ----------------------------------------------------
# UPLOAD
# ----------------------------------------------------
colA, colB = st.columns(2)
with colA:
    file1 = st.file_uploader("Upload Excel (Version 1)", type=["xlsx"])
with colB:
    file2 = st.file_uploader("Upload Excel (Version 2 - Optional for Comparison)", type=["xlsx"])

# ----------------------------------------------------
# STATUS NORMALIZATION RULES
# ----------------------------------------------------
CLOSED = ["closed", "done", "completed", "resolved", "final", "✔"]
INPROG = ["in progress", "wip", "working", "ongoing"]

def classify_status(s):
    s = str(s).lower().strip()
    if any(k in s for k in CLOSED): return "Closed"
    if any(k in s for k in INPROG): return "In Progress"
    return "Pending"

# ----------------------------------------------------
# STAT COMPUTATION
# ----------------------------------------------------
def compute_stats(df):
    df.columns = df.columns.str.strip().str.lower()

    if "status" not in df.columns:
        return None

    df["bucket"] = df["status"].apply(classify_status)

    total = len(df)
    closed = (df["bucket"] == "Closed").sum()
    prog = (df["bucket"] == "In Progress").sum()
    pending = (df["bucket"] == "Pending").sum()
    progress = closed / total if total else 0

    return {
        "df": df,
        "total": total,
        "closed": closed,
        "prog": prog,
        "pending": pending,
        "progress": progress
    }

# ----------------------------------------------------
# PDF EXPORTER
# ----------------------------------------------------
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="RFI Dashboard Summary Report", ln=True)
    out = BytesIO()
    pdf.output(out)
    return out

# ----------------------------------------------------
# MAIN RENDER FUNCTION
# ----------------------------------------------------
def render_dashboard(sheets, label):
    st.markdown(f"## 📁 {label}")

    for sheet_name, df in sheets.items():

        stats = compute_stats(df)
        if stats is None: 
            continue

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader(f"📄 {sheet_name}")

        # BADGES
        st.markdown(f"""
        <span class='badge badge-green'>Closed: {stats['closed']}</span>
        <span class='badge badge-yellow'>In Progress: {stats['prog']}</span>
        <span class='badge badge-red'>Pending: {stats['pending']}</span>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        # Progress Bar
        with col1:
            st.write("**Overall Progress**")
            st.progress(stats["progress"])
            st.write(f"**{int(stats['progress']*100)}% complete**")

        # Gauge
        with col2:
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=stats["progress"] * 100,
                number={"suffix": "%"},
                gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#4A90E2"}},
            ))
            fig_g.update_layout(height=260)
            st.write("**Completion Gauge**")
            st.plotly_chart(fig_g, use_container_width=True)

        # Pie Chart
        with col3:
            pie_df = pd.DataFrame({
                "Status": ["Closed", "In Progress", "Pending"],
                "Count": [stats["closed"], stats["prog"], stats["pending"]]
            })
            fig_p = px.pie(
                pie_df, names="Status", values="Count",
                color="Status",
                color_discrete_map={"Closed": "green", "In Progress": "gold", "Pending": "red"},
                hole=0.45,
            )
            fig_p.update_layout(height=260)
            st.write("**Distribution**")
            st.plotly_chart(fig_p, use_container_width=True)

        # Chips
        st.write("**Statuses in this sheet**")
        chips = "".join([f"<span class='status-chip'>{x}</span>" for x in stats["df"]["status"].unique()])
        st.markdown(chips, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# RUN
# ----------------------------------------------------
if file1:
    sheets1 = pd.read_excel(file1, sheet_name=None)
    render_dashboard(sheets1, "Version 1")

if file2:
    sheets2 = pd.read_excel(file2, sheet_name=None)
    st.markdown("---")
    render_dashboard(sheets2, "Version 2 (Comparison)")

if file1:
    if st.button("Download PDF Summary"):
        st.download_button("Click to Download", generate_pdf(), "RFI_Report.pdf")
