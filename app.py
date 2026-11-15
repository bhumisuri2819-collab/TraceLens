import json
import pandas as pd
import streamlit as st
from tracelens.store import init_db, load_traces, save_traces, clear_traces
from tracelens.evaluation import evaluate_traces, summarize_evaluations
from tracelens.samples import SAMPLE_TRACES
from tracelens.langfuse_client import fetch_langfuse_traces

st.set_page_config(page_title="TraceLens AI", page_icon="🔎", layout="wide")
init_db()

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1440px;}
[data-testid="stMetric"] {background: #111827; border: 1px solid #293548; padding: 16px; border-radius: 12px;}
div[data-testid="stMetricLabel"] p {color:#9ca3af;}
div[data-testid="stMetricValue"] {color:#f9fafb;}
section[data-testid="stSidebar"] {background:#0b1220;}
.small-muted {color:#94a3b8;font-size:0.88rem;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("# 🔎 TraceLens AI")
    st.caption("LLM observability · evaluation · experiments")
    page = st.radio("Workspace", ["Overview", "Trace Explorer", "Evaluations", "Data & Integrations"], label_visibility="collapsed")
    st.divider()
    st.caption("A portfolio project for inspecting and evaluating LLM application traces.")

traces = load_traces()

def ensure_demo():
    if not load_traces():
        save_traces(SAMPLE_TRACES)

if page == "Overview":
    st.title("LLM observability at a glance")
    st.markdown('<p class="small-muted">Understand quality, latency and reliability across your AI runs.</p>', unsafe_allow_html=True)
    if not traces:
        st.info("Your workspace is empty. Load the sample dataset or import traces from Data & Integrations.")
        if st.button("Load sample workspace", type="primary"):
            ensure_demo()
            st.rerun()
    else:
        results = evaluate_traces(traces)
        summary = summarize_evaluations(results)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total traces", f"{len(traces):,}")
        c2.metric("Pass rate", f"{summary['pass_rate']:.1f}%")
        c3.metric("Avg. latency", f"{summary['avg_latency']:.0f} ms")
        c4.metric("Error rate", f"{summary['error_rate']:.1f}%")
        left,right = st.columns([1.35,1])
        with left:
            st.subheader("Trace volume")
            df = pd.DataFrame(traces)
            if "created_at" in df:
                df["day"] = pd.to_datetime(df["created_at"], errors="coerce").dt.date
                volume = df.groupby("day").size().rename("traces")
                st.line_chart(volume)
            st.subheader("Recent traces")
            recent = pd.DataFrame(traces).sort_values("created_at", ascending=False).head(8)
            cols = [c for c in ["name","model","latency_ms","status","created_at"] if c in recent]
            st.dataframe(recent[cols], use_container_width=True, hide_index=True)
        with right:
            st.subheader("Evaluation checks")
            st.bar_chart(pd.Series(summary["checks"], name="pass rate"))
            st.subheader("Common models")
            model_counts = pd.Series([t.get("model","unknown") for t in traces]).value_counts()
            st.dataframe(model_counts.rename_axis("model").reset_index(name="runs"), use_container_width=True, hide_index=True)

elif page == "Trace Explorer":
    st.title("Trace Explorer")
    st.caption("Filter individual LLM executions and inspect their inputs, outputs and metadata.")
    if not traces:
        st.info("No traces yet. Import data or load the sample workspace.")
    else:
        df = pd.DataFrame(traces)
        models = sorted(df.get("model", pd.Series(["unknown"])).fillna("unknown").unique().tolist())
        selected_model = st.selectbox("Model", ["All models"] + models)
        statuses = sorted(df.get("status", pd.Series(["unknown"])).fillna("unknown").unique().tolist())
        selected_status = st.selectbox("Status", ["All statuses"] + statuses)
        filtered = df.copy()
        if selected_model != "All models": filtered = filtered[filtered["model"] == selected_model]
        if selected_status != "All statuses": filtered = filtered[filtered["status"] == selected_status]
        st.dataframe(filtered[[c for c in ["name","model","latency_ms","input","output","status","created_at"] if c in filtered]],
                     use_container_width=True, hide_index=True)
        ids = filtered["id"].astype(str).tolist()
        if ids:
            selected_id = st.selectbox("Inspect trace", ids)
            item = next(t for t in traces if str(t.get("id")) == selected_id)
            a,b = st.columns(2)
            with a:
                st.markdown("**Input**")
                st.code(str(item.get("input","")), language="text")
            with b:
                st.markdown("**Output**")
                st.code(str(item.get("output","")), language="text")
            with st.expander("Raw trace metadata"):
                st.json(item)

elif page == "Evaluations":
    st.title("Evaluation Studio")
    st.caption("Run transparent, deterministic quality checks over imported traces.")
    if not traces:
        st.info("Import traces or load the sample workspace to run evaluations.")
    else:
        results = evaluate_traces(traces)
        summary = summarize_evaluations(results)
        a,b,c = st.columns(3)
        a.metric("Overall pass rate", f"{summary['pass_rate']:.1f}%")
        b.metric("Average score", f"{summary['avg_score']:.2f}/5")
        c.metric("Checks executed", len(results) * len(summary["checks"]))
        st.subheader("Evaluation results")
        result_df = pd.DataFrame(results)
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        st.subheader("Check performance")
        st.bar_chart(pd.Series(summary["checks"], name="pass rate"))
        st.download_button("Download evaluation report", result_df.to_csv(index=False),
                           file_name="tracelens-evaluation-report.csv", mime="text/csv")

elif page == "Data & Integrations":
    st.title("Data & Integrations")
    st.caption("Bring your own traces. TraceLens accepts JSON arrays, JSONL and CSV files.")
    st.subheader("Load a starter dataset")
    if st.button("Load sample traces", type="primary"):
        ensure_demo()
        st.success("Sample traces are ready.")
        st.rerun()
    st.divider()
    st.subheader("Import trace data")
    uploaded = st.file_uploader("Choose JSON, JSONL or CSV", type=["json","jsonl","csv"])
    if uploaded is not None:
        try:
            if uploaded.name.endswith(".csv"):
                imported = pd.read_csv(uploaded).fillna("").to_dict(orient="records")
            elif uploaded.name.endswith(".jsonl"):
                imported = [json.loads(line) for line in uploaded.getvalue().decode().splitlines() if line.strip()]
            else:
                parsed = json.loads(uploaded.getvalue())
                imported = parsed if isinstance(parsed, list) else parsed.get("data", parsed.get("traces", [parsed]))
            st.write(f"Detected **{len(imported)}** records.")
            st.json(imported[:2])
            if st.button("Import these traces"):
                save_traces(imported)
                st.success(f"Imported {len(imported)} traces.")
                st.rerun()
        except Exception as exc:
            st.error(f"Could not parse this file: {exc}")
    st.divider()
    st.subheader("Connect to Langfuse")
    st.markdown("Use a Langfuse project’s public and secret API keys. Credentials stay in your local environment.")
    with st.form("langfuse_form"):
        host = st.text_input("Langfuse host", value="https://cloud.langfuse.com")
        public_key = st.text_input("Public key")
        secret_key = st.text_input("Secret key", type="password")
        submitted = st.form_submit_button("Fetch recent traces")
    if submitted:
        try:
            with st.spinner("Fetching traces…"):
                imported = fetch_langfuse_traces(host, public_key, secret_key)
            if imported:
                save_traces(imported)
                st.success(f"Fetched and imported {len(imported)} traces.")
                st.rerun()
            else:
                st.warning("The API returned no traces.")
        except Exception as exc:
            st.error(f"Langfuse connection failed: {exc}")
    st.divider()
    st.subheader("Workspace maintenance")
    st.caption(f"{len(traces)} traces currently stored locally in SQLite.")
    if st.button("Clear local workspace", type="secondary"):
        clear_traces()
        st.rerun()
