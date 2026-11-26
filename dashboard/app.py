import os
import requests
import streamlit as st
import pandas as pd

API = os.getenv("CONTRACTIQ_API_URL", "http://127.0.0.1:8000")
st.set_page_config(page_title="ContractIQ AI", page_icon="📑", layout="wide")
st.title("📑 ContractIQ")
st.caption("Contract intelligence · evidence-led review · human decision support")
st.warning("ContractIQ is not legal advice. Review every finding against the original agreement.")
with st.sidebar:
    st.subheader("Workspace")
    uploaded = st.file_uploader("Upload contract", type=["pdf", "docx"])
    run = st.button("Analyze contract", type="primary", disabled=uploaded is None, use_container_width=True)
    st.divider()
    st.caption(f"API: {API}")
if run and uploaded:
    with st.spinner("Extracting and reviewing contract…"):
        try:
            response = requests.post(f"{API}/documents/analyze", files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}, timeout=180)
            response.raise_for_status()
            st.session_state["analysis_result"] = response.json()
        except requests.RequestException as exc:
            st.error(f"Could not analyze document: {exc}")
result = st.session_state.get("analysis_result")
if result:
    data = result["analysis"]
    findings = data.get("findings", [])
    obligations = data.get("obligations", [])
    high = sum(item["severity"] == "high" for item in findings)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Review flags", len(findings))
    c2.metric("High priority", high)
    c3.metric("Obligations", len(obligations))
    c4.metric("Clauses detected", len(data.get("clauses_detected", [])))
    st.subheader(data["document_name"])
    st.caption(f"Analysis mode: {data['analysis_mode']} · ID: {result['id']}")
    st.info(data["summary"])
    left, right = st.columns(2)
    with left:
        st.markdown("#### Contract snapshot")
        st.write("**Parties:** " + (", ".join(data.get("parties") or []) or "Not identified"))
        st.write("**Effective date:** " + str(data.get("effective_date") or "Not identified"))
        st.write("**End date:** " + str(data.get("end_date") or "Not identified"))
        st.write("**Governing law:** " + str(data.get("governing_law") or "Not identified"))
        st.write("**Value:** " + str(data.get("contract_value") or "Not identified"))
        st.write("**Clauses:** " + (", ".join(data.get("clauses_detected") or []) or "None detected"))
    with right:
        st.markdown("#### Review priority")
        if findings:
            counts = pd.DataFrame([{"Priority": key.title(), "Count": sum(item["severity"] == key for item in findings)} for key in ["high", "medium", "low", "info"]])
            st.bar_chart(counts.set_index("Priority"))
        else:
            st.success("No baseline review flags were raised. This is not proof that the contract is risk-free.")
    st.divider()
    tab1, tab2, tab3 = st.tabs(["Potential risks", "Obligations", "Source text"])
    with tab1:
        for idx, item in enumerate(findings, 1):
            st.markdown(f"**{idx}. {item['title']}** · {item['severity'].upper()}")
            st.write(item["explanation"])
            st.write("**Suggested review:** " + item["recommendation"])
            for ev in item.get("evidence", []):
                st.caption(f"{ev['location']} · “{ev['quote']}”")
            st.divider()
    with tab2:
        if obligations:
            st.dataframe(pd.DataFrame([{"Party": item["party"], "Obligation": item["obligation"], "Deadline": item.get("deadline") or "Not specified"} for item in obligations]), use_container_width=True)
        else:
            st.info("No obligation statements were extracted by this analysis.")
    with tab3:
        for section in result.get("source_text", []):
            with st.expander(section["location"]):
                st.write(section["text"])
else:
    st.markdown("### Start with a contract")
    st.write("Upload a PDF or DOCX in the sidebar. The app extracts text, identifies review topics, and links findings back to source excerpts.")
    try:
        history = requests.get(f"{API}/documents", timeout=3).json()
        if history:
            st.markdown("#### Recent analyses")
            st.dataframe(pd.DataFrame(history), use_container_width=True)
    except requests.RequestException:
        st.error("API is not reachable. Start it with uvicorn contractiq.api:app --reload.")
