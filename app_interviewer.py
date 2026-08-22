import streamlit as st
import requests

st.set_page_config(page_title="Interviewer Dashboard", page_icon="🎤", layout="wide")

# ---------- styling ----------
st.markdown(
    """
    <style>
      .stApp { background: linear-gradient(180deg,#f7f9fc 0%,#eef2f8 100%); }
      .hero {
        background: linear-gradient(135deg,#0f766e 0%,#0891b2 100%);
        padding: 1.8rem 2rem; border-radius: 18px; color:#fff;
        box-shadow: 0 10px 30px rgba(8,145,178,.22); margin-bottom: 1.2rem;
      }
      .hero h1 { color:#fff; margin:0; font-size:1.9rem; }
      .hero p  { color:#d7f5f0; margin:.3rem 0 0; }
      .card {
        background:#fff; border:1px solid #e8ecf4; border-radius:14px;
        padding:1.1rem 1.3rem; margin:.5rem 0; box-shadow:0 2px 10px rgba(20,30,60,.04);
      }
      .pill {
        display:inline-block; padding:.2rem .6rem; border-radius:999px;
        font-size:.78rem; font-weight:700; margin-right:.3rem;
      }
      .pill-tech { background:#eef2ff; color:#4338ca; }
      .pill-beh  { background:#ecfdf5; color:#047857; }
      .stButton>button {
        background:linear-gradient(135deg,#0f766e,#0891b2); color:#fff; border:0;
        border-radius:10px; padding:.5rem 1.1rem; font-weight:700;
      }
      .stButton>button:hover { filter:brightness(1.08); }
    </style>
    """,
    unsafe_allow_html=True,
)

API = st.sidebar.text_input("API base URL", "http://localhost:8000", key="api_base")
st.sidebar.caption("Point this at your running FastAPI server.")

st.markdown(
    '<div class="hero"><h1>🎤 Interviewer Dashboard</h1>'
    "<p>Review AI-screened candidates, interview kits, and HR policy.</p></div>",
    unsafe_allow_html=True,
)

tab_cand, tab_policy = st.tabs(["👤 Candidates", "📚 HR Policy"])

# ---------- CANDIDATES: questions + panel ----------
with tab_cand:
    try:
        jobs = requests.get(f"{API}/jobs", timeout=10).json()
    except Exception as e:
        st.error(f"Cannot reach API: {e}"); jobs = []

    if not jobs:
        st.warning("No jobs. Run seed_jobs.py."); st.stop()

    jlabels = {f'{j["title"]}  (#{j["job_id"]})': j for j in jobs}
    job = jlabels[st.selectbox("Job", list(jlabels.keys()), key="job_sel")]
    cands = requests.get(f"{API}/candidates", params={"job_id": job["job_id"]}).json()

    if not cands:
        st.info("No candidates have applied/been processed for this role yet.")
    else:
        top = max((c["score"] for c in cands), default=0)
        k1, k2, k3 = st.columns(3)
        k1.metric("Candidates", len(cands))
        k2.metric("Top match", f"{top*100:.0f}%")
        k3.metric("Role", job["title"])

        clabels = {f'Candidate #{c["candidate_id"]} — {c["score"]*100:.0f}%': c for c in cands}
        c = clabels[st.selectbox("Candidate (ranked by score)", list(clabels.keys()), key="cand_sel")]
        cid = c["candidate_id"]

        data = requests.get(f"{API}/interview/{cid}", params={"job_id": job["job_id"]})
        if not data.ok:
            st.error(f"{data.status_code} {data.text}")
        else:
            d = data.json(); summ = d.get("summary") or {}

            st.markdown('<div class="card">', unsafe_allow_html=True)
            colA, colB = st.columns(2)
            with colA:
                st.markdown("**💪 Strengths**")
                for s in summ.get("strengths", []): st.write("- " + s)
            with colB:
                st.markdown("**⚠️ Gaps**")
                for g in summ.get("gaps", []): st.write("- " + g)
            if summ.get("flags"):
                st.markdown("**🚩 Flags**")
                for f in summ["flags"]: st.write("- " + f)
            if summ.get("recommendation"):
                st.markdown(f"**Recommendation:** {summ['recommendation']}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("### 🎤 Interview Questions")
            for i, q in enumerate((d.get("interview_kit") or {}).get("questions", []), 1):
                with st.expander(f"Q{i}. {q['question']}"):
                    kind = (q.get("kind") or "").lower()
                    pill = "pill-tech" if "tech" in kind else "pill-beh"
                    st.markdown(
                        f'<span class="pill {pill}">{q.get("kind","")}</span>'
                        f'<span class="pill pill-tech">{q.get("difficulty","")}</span>',
                        unsafe_allow_html=True)
                    st.write(f"**Targets:** {q.get('targets')}")

            if d.get("panel"):
                st.divider()
                st.markdown("### 👥 Recommended Panel")
                st.write(d["panel"])

            # live, resume-grounded question generator
            st.divider()
            st.markdown("### 💬 Ask your own question (grounded in this résumé)")
            topic = st.text_input("What do you want to probe?",
                                  placeholder="e.g. their AWS experience, system-design depth",
                                  key=f"topic_{cid}")
            if st.button("Generate questions", key=f"ask_{cid}") and topic:
                with st.spinner("Reading the résumé…"):
                    a = requests.post(f"{API}/interview/{cid}/ask", params={"topic": topic})
                if a.ok:
                    for i, q in enumerate(a.json().get("questions", []), 1):
                        st.markdown(f"**{i}. {q['question']}**")
                        st.caption(f"{q.get('kind')} · {q.get('difficulty')} · targets: {q.get('targets')}")
                else:
                    st.error(f"{a.status_code} {a.text}")

            # pay-band recommendation (grounded in the compensation policy)
            st.divider()
            st.markdown("### 💰 Suggested Pay (per HR compensation policy)")
            if st.button("Suggest pay band", key=f"pay_{cid}"):
                with st.spinner("Checking compensation policy…"):
                    pr = requests.post(f"{API}/interview/{cid}/pay",
                                       params={"job_id": job["job_id"]})
                if pr.ok:
                    pj = pr.json()
                    st.metric("Suggested range", pj.get("suggested_range", "—"))
                    for p in pj.get("points", []):
                        st.write("- " + p)
                    st.caption("⚠️ Based on sample compensation policy — not a real offer.")
                else:
                    st.error(f"{pr.status_code} {pr.text}")

# ---------- HR POLICY (interviewer-only) ----------
with tab_policy:
    st.subheader("Ask about HR policy")
    q = st.text_input("Your question", "How many people should be on an interview panel?", key="policy_q")
    if st.button("Search", key="policy_btn"):
        r = requests.get(f"{API}/policies/search", params={"q": q})
        if not r.ok:
            st.error(f"{r.status_code} {r.text}")
        else:
            results = r.json().get("results", [])
            if not results:
                st.warning("No matching policy found. Run seed_policies.py.")
            for cc in results:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f"> {cc['text']}")
                st.caption(f"📄 {cc.get('citation','')}  ·  score {cc.get('score',0):.3f}")
                st.markdown("</div>", unsafe_allow_html=True)
