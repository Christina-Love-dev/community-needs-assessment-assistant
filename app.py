import streamlit as st
import pandas as pd
from anthropic import Anthropic
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

client = Anthropic(
    api_key=st.secrets["ANTHROPIC_API_KEY"]
)

st.title("🏘️ Community Needs Assessment Assistant")

st.caption(
    "Transform community survey responses into actionable insights with AI-assisted analysis powered by Claude."
)

survey_purpose = st.text_area(
    "What is the purpose of this survey?",
    placeholder="Example: Understand barriers faced by senior center clients accessing community resources."
)

uploaded_file = st.file_uploader(
    "Upload survey responses (CSV)",
    type=["csv"]
)

if uploaded_file is not None:

    data = pd.read_csv(uploaded_file)

    if data.empty:
        st.error("The uploaded survey contains no responses.")
        st.stop()

    st.subheader("Survey Overview")

    st.write(f"Total Responses: {len(data)}")
    st.write(f"Total Questions: {len(data.columns)}")

    st.subheader("Questions Detected")

    for column in data.columns:
         st.markdown(f"- **{column}**")

    with st.expander("📄 Preview Uploaded Survey", expanded=False):
         st.dataframe(data)

    st.subheader("Select Questions to Include in Analysis")

    selected_columns = st.multiselect(
        "Which survey questions should Claude analyze?",
        data.columns,
        default=data.columns
    )

    if not selected_columns:
        st.warning("Please select at least one question to analyze.")

    with st.expander("🔍 Selected Survey Data", expanded=True):
         st.dataframe(data[selected_columns])

    analysis_data = data[selected_columns]

    responses_text = analysis_data.to_string()

    if survey_purpose:
        st.subheader("Assessment Purpose")
        st.write(survey_purpose)

    if st.button("Generate Community Assessment"):

        if not survey_purpose:
            st.warning(
                "Please enter the purpose of the survey before generating an assessment."
            )

        else:

            st.subheader("Community Needs Assessment Report")

            with st.spinner("🤖 Claude is identifying themes and drafting your community assessment..."):

                prompt = f"""
                Survey Purpose:
                {survey_purpose}

                Number of survey responses:
                {len(data)}

                Selected survey questions:
                {", ".join(selected_columns)}

                Survey data:
                {responses_text}

You are an experienced community research analyst preparing a report for nonprofit leaders.

Your task is to analyze the selected survey responses and produce a professional Community Needs Assessment.

Instructions:
- Base all findings only on the survey data provided.
- Do not invent facts, statistics, or participant opinions.
- If the survey data is limited, acknowledge that limitation.
- Identify recurring themes, unmet needs, and opportunities for improvement.
- Write in a clear, objective, and professional tone suitable for nonprofit staff and community stakeholders.

Format your response in Markdown using these headings only:

### Executive Summary

Provide a concise overview of the most important findings.

### Key Themes

Summarize the major patterns observed in the survey responses using bullet points where appropriate.

### Community Needs Identified

Describe the needs, barriers, or service gaps revealed by the survey.

### Recommended Actions

Provide practical, evidence-based recommendations that logically follow from the survey findings.

Do not include a title.
Do not use level-1 (#) or level-2 (##) headings.
Begin immediately with "### Executive Summary".
"""
                message = client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=1500,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                assessment = message.content[0].text

                st.markdown(assessment)
                
                pdf_buffer = BytesIO()

                doc = SimpleDocTemplate(pdf_buffer)

                styles = getSampleStyleSheet()

                story = []

                story.append(
                    Paragraph(
                        "Community Needs Assessment Report",
                        styles["Title"]
                    )
                )

                story.append(Spacer(1, 24))

                for line in assessment.split("\n"):

                    line = line.strip()

                    if not line:
                        continue

                    if line.startswith("###"):
                        story.append(
                            Paragraph(
                                line.replace("###", "").strip(),
                                styles["Heading2"]
                            )
                        )

                    else:
                        clean_line = (
                            line
                            .replace("**", "")
                            .replace("- ", "• ")
                        )

                        story.append(
                            Paragraph(
                                clean_line,
                                styles["BodyText"]
                            )
                        )

                    story.append(Spacer(1, 12))


                doc.build(story)

                pdf_data = pdf_buffer.getvalue()

                st.download_button(
                    label="📄 Download Community Needs Assessment PDF",
                    data=pdf_data,
                    file_name="community_needs_assessment.pdf",
                    mime="application/pdf"
                )