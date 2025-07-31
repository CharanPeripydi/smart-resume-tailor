import streamlit as st
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from openai import OpenAI
import os
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from docx.oxml.ns import qn

# Load API key
load_dotenv()
client = OpenAI()

# Page config and style
st.set_page_config(page_title="Smart Resume Tailor", layout="wide")

st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
            padding: 20px;
            font-family: 'Segoe UI', sans-serif;
        }
        .stTextArea label, .stButton button {
            font-weight: bold;
        }
        .css-1aumxhk {
            background-color: #0072C6;
            color: white;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🧠 Smart Resume Tailor – AI Rewriter & Word Exporter")
st.markdown("Tailor your resume to any job description. Get ATS-optimized formatting, exact role preservation, and a clean downloadable Word file.")

# Text inputs
resume_text = st.text_area("📄 Paste Your Resume", height=300, placeholder="Paste your raw resume...")
jd_text = st.text_area("📝 Paste Job Description", height=300, placeholder="Paste the job description here...")

# ATS score function
def get_ats_score(resume, jd):
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform([resume, jd])
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return round(score * 100, 2)

# Button
if st.button("✍️ Tailor Resume"):
    if resume_text and jd_text:
        with st.spinner("Tailoring your resume… optimizing keywords, formatting for ATS, and preparing download... 💼"):
            # AI Prompt
            prompt = f"""
You are an expert resume writer. Do NOT change the job role titles in the Experience section — keep them exactly as written.
However, you may improve or rewrite the bullet points beneath each title based on the job description.

Write exactly 10 bullet points under each job. Make sure the resume is tightly formatted to fit within 2 pages.
Maintain original section order and use professional, clean formatting with no extra spacing.

Keep content ATS-friendly and relevant to the job description.

Resume:
{resume_text}

Job Description:
{jd_text}
"""

            # OpenAI API Call
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            optimized_resume = response.choices[0].message.content
            score = get_ats_score(optimized_resume, jd_text)

            # Display Result
            st.success("✅ Resume tailored successfully!")
            st.text_area("🧾 Tailored Resume Output", optimized_resume, height=400)
            st.metric(label="📊 ATS Match Score", value=f"{score}%")

            # Word Export
            doc = Document()
            style = doc.styles['Normal']
            font = style.font
            font.name = 'Calibri'
            font.size = Pt(10.5)

            # Format: Blue Headers + Line
            def add_header(text):
                para = doc.add_paragraph()
                run = para.add_run(text.upper())
                run.bold = True
                run.font.size = Pt(11.5)
                run.font.color.rgb = RGBColor(0, 102, 204)
                para.paragraph_format.space_after = Pt(0)
                para.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

                # Separator Line
                line_para = doc.add_paragraph()
                run_line = line_para.add_run("─" * 100)
                run_line.font.size = Pt(5)
                run_line.font.color.rgb = RGBColor(160, 160, 160)
                line_para.paragraph_format.space_after = Pt(4)

            for line in optimized_resume.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # Remove "Resume" header at top if present
                if line.lower().startswith("resume"):
                    continue

                # Blue section headers
                if line.isupper() or "__________" in line:
                    add_header(line.replace("_", "").strip())

                # Bullet points
                elif line.startswith("•") or line.startswith("-"):
                    para = doc.add_paragraph(line[1:].strip(), style='List Bullet')
                    para.paragraph_format.space_after = Pt(1)

                # Normal text
                else:
                    para = doc.add_paragraph(line)
                    para.paragraph_format.space_after = Pt(1)

            doc.save("Tailored_Resume.docx")

            # Download button
            with open("Tailored_Resume.docx", "rb") as file:
                st.download_button(
                    label="📥 Download Tailored Resume (.docx)",
                    data=file,
                    file_name="Tailored_Resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
    else:
        st.warning("⚠️ Please paste both your resume and job description.")
