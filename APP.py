import streamlit as st
from openai import OpenAI
import docx
import re
from io import BytesIO
from docx.shared import RGBColor, Pt
import time

# Set OpenAI API key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Smart Resume Tailor", layout="wide")
st.markdown("""
    <style>
    body, .main, .block-container {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        overflow-x: hidden;
    }
    .stButton>button {
        background-color: #1DB954 !important;
        color: white !important;
        font-weight: bold;
    }
    .stTextInput>div>input, .stTextArea textarea {
        background-color: #121212 !important;
        color: white !important;
    }
    .stFileUploader {
        background-color: #121212 !important;
        color: white !important;
        padding: 1rem;
        border-radius: 8px;
    }
    label {
        color: #FFFFFF !important;
        font-weight: 600;
        font-size: 16px;
    }
    .stTextArea, .stTextInput {
        background-color: #121212 !important;
    }
    .stDownloadButton>button {
        background-color: #1DB954 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
    }
    .ats-score {
        font-size: 22px;
        color: #1DB954;
        padding-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Smart Resume Tailor – Boost Your ATS Score")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("#### 📄 Upload your resume (.docx only)")
    uploaded_resume = st.file_uploader("", type=["docx"])

with col2:
    st.markdown("#### 🧾 Paste the Job Description Here")
    jd_text = st.text_area("", height=300)

if st.button("🎯 Tailor My Resume"):
    if uploaded_resume and jd_text:
        with st.spinner('✨ Tailoring your resume...'):
            time.sleep(1)
            doc = docx.Document(uploaded_resume)
            full_text = "\n".join([para.text for para in doc.paragraphs])

            prompt = f"""
            You are an ATS optimization assistant. Based on the job description below, tailor the PROFESSIONAL SUMMARY, EXPERIENCE BULLET POINTS (minimum 10 per job), and PROJECTS SECTION (minimum 10 projects).

            INSTRUCTIONS:
            1. DO NOT change role titles or section headers.
            2. DO NOT use any emojis.
            3. Retain the original layout: gaps, separators ("―" lines), bullet spacing, and structure.
            4. HEADINGS like "PROFESSIONAL SUMMARY", "PROJECTS", "SKILLS", "EXPERIENCE" should be bold and blue.
            5. Role titles (e.g., Data Analyst), company names (e.g., Noesys Inc.), dates, and virtual program names should be bold (not blue).
            6. At the end, add keyword stuffing in white color, font size 1.
            7. Finish with: ATS SCORE: [number between 0 and 100]

            JOB DESCRIPTION:
            {jd_text}

            ORIGINAL RESUME:
            {full_text}
            """

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful ATS resume optimizer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            tailored_text = response.choices[0].message.content

            ats_score_match = re.search(r"(?i)ATS SCORE[:\s]+(\d{1,3})", tailored_text)
            ats_score = ats_score_match.group(1) if ats_score_match else "N/A"
            tailored_text_clean = re.sub(r"(?i)ATS SCORE[:\s]+(\d{1,3})", "", tailored_text).strip()

            output = BytesIO()
            new_doc = docx.Document()
            style = new_doc.styles['Normal']
            font = style.font
            font.name = 'Calibri'
            font.size = Pt(10.5)

            blue_headings = ["PROFESSIONAL SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS", "EDUCATION", "VIRTUAL EXPERIENCE PROGRAMS"]

            for line in tailored_text_clean.splitlines():
                if line.strip() == "":
                    continue

                para = new_doc.add_paragraph()
                run = para.add_run(line.strip())
                run.font.name = 'Calibri'
                run.font.size = Pt(10.5)

                if line.strip().startswith("-") or line.strip().startswith("•"):
                    para = new_doc.add_paragraph(style='List Bullet')
                    run = para.add_run(line.strip("-• "))
                    run.font.name = 'Calibri'
                    run.font.size = Pt(10.5)

                elif line.strip() in blue_headings:
                    run.bold = True
                    run.font.color.rgb = RGBColor(0, 112, 192)  # Blue

                elif ("Inc." in line or "LLC" in line or "Analyst" in line or "Intern" in line or "Assistant" in line or re.search(r"\b\d{4}\b", line)):
                    run.bold = True

                elif "―" in line:
                    run = para.add_run("―" * 100)
                    run.font.name = 'Calibri'
                    run.font.size = Pt(10.5)

            # Add invisible keyword stuffing at the end
            stuffing_para = new_doc.add_paragraph()
            stuffing_run = stuffing_para.add_run(" ".join(re.findall(r"\b\w+\b", jd_text.lower())))
            stuffing_run.font.color.rgb = RGBColor(255, 255, 255)
            stuffing_run.font.size = Pt(1)

            new_doc.save(output)
            st.success("✅ Resume tailored successfully!")
            st.markdown(f"<div class='ats-score'>📈 Estimated ATS Score: <strong>{ats_score}</strong></div>", unsafe_allow_html=True)
            st.download_button(
                label="📥 Download Tailored Resume",
                data=output.getvalue(),
                file_name="Tailored_Resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    else:
        st.error("❌ Please upload a resume and paste the job description.")