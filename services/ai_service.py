from openai import OpenAI
import streamlit as st

# --------------------------------
# OPENAI CLIENT
# --------------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def analyze_image(base64_image):
    prompt = """
You are a senior construction QA/QC engineer.

Analyze this construction image and generate:

1. Suggested discipline
2. Defect type
3. Professional NCR description
4. Root cause
5. Corrective action

Return clearly structured output.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content