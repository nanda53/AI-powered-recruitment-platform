import streamlit as st
import requests

st.set_page_config(page_title="Apply for a Role", page_icon="📤", layout="centered")

# ---------- styling ----------
st.markdown(
    """
    <style>
      .stApp { background: linear-gradient(180deg,#f7f9fc 0%,#eef2f8 100%); }
      .hero {
        background: linear-gradient(135deg,#4f46e5 0%,#7c3aed 100%);
        padding: 2rem 2rem 1.5rem; border-radius: 18px; color: #fff;
        box-shadow: 0 10px 30px rgba(79,70,229,.25); margin-bottom: 1.4rem;
      }
      .hero h1 { color:#fff; margin:0; font-size:2rem; }
      .hero p  { color:#e9e7ff; margin:.35rem 0 0; font-size:1rem; }
      .card {
        background:#fff; border:1px solid #e8ecf4; border-radius:14px;
        padding:1.1rem 1.3rem; margin:.6rem 0; box-shadow:0 2px 10px rgba(20,30,60,.04);
      }
      .skill-chip {
        display:inline-block; background:#eef2ff; color:#4338ca; font-size:.8rem;
        padding:.2rem .6rem; border-radius:999px; margin:.15rem .25rem .15rem 0; font-weight:600;
      }
      .stButton>button {
        background:linear-gradient(135deg,#4f46e5,#7c3aed); color:#fff; border:0;
        border-radius:10px; padding:.55rem 1.2rem; font-weight:700; width:100%;
      }
      .stButton>button:hover { filter:brightness(1.07); }
    </style>
    """,
    unsafe_allow_html=True,
)

API = st.sidebar.text_input("API base URL", "http://localhost:8000")
st.sidebar.caption("Point this at your running FastAPI server.")

st.markdown(
    '<div class="hero"><h1>📤 Apply for a Role</h1>'
    "<p>Upload your résumé and get an instant AI screening result.</p></div>",
    unsafe_allow_html=True,
)

try:
    jobs = requests.get(f"{API}/jobs", timeout=10).json()
except Exception as e:
    st.error(f"Cannot reach API: {e}"); jobs = []

if not jobs:
    st.warning("No roles available. Run `python seed_jobs.py`.")
else:
    labels = {f'{j["title"]}  (#{j["job_id"]})': j for j in jobs}
    job = labels[st.selectbox("Choose a role", list(labels.keys()))]

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"#### {job['title']}")
    st.caption(job["description"])
    chips = "".join(f'<span class="skill-chip">{s}</span>'
                    for s in job.get("required_skills", []))
    st.markdown("**Required skills**<br>" + (chips or "—"), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    pdf = st.file_uploader("Upload your résumé (PDF / DOCX / TXT)", type=["pdf", "docx", "txt"])
    if st.button("🚀 Submit application", disabled=not pdf):
        with st.spinner("Uploading & analysing…"):
            r = requests.post(f"{API}/resumes", files={"file": (pdf.name, pdf.getvalue())})
        if not r.ok:
            st.error(f"Upload failed: {r.status_code} {r.text}")
        else:
            cid = r.json().get("candidate_id")
            with st.spinner("Running screening…"):
                p = requests.post(f"{API}/process",
                                  params={"candidate_id": cid, "job_id": job["job_id"]})
            if not p.ok:
                st.error(f"Screening failed: {p.status_code} {p.text}")
            else:
                res = p.json(); sc = res["score"]["score"]
                st.success(f"✅ Application submitted — you are candidate #{cid}.")

                m1, m2 = st.columns(2)
                m1.metric("Match score", f"{sc*100:.0f}%")
                m2.metric("Status", "Shortlisted" if res.get("shortlisted") else "Not shortlisted")
                st.progress(min(sc, 1.0))

                if res.get("shortlisted"):
                    st.balloons()
                    st.info(f"You have been **shortlisted** (match {sc*100:.0f}%). "
                            "Our team will reach out about interview scheduling.")
                else:
                    st.warning(f"Thank you for applying. Match score {sc*100:.0f}% — "
                               "you were not shortlisted for this role this time.")
                # applicant sees ONLY the verdict — no questions, no panel.
