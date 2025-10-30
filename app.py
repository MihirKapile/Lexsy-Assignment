import streamlit as st
from groq import Groq
from io import BytesIO
import json
import re
from docx import Document

st.set_page_config(page_title="Conversational Legal Document Filler", layout="wide")

st.title("Conversational Legal Document Filler — Groq Llama 3.3 70B")
st.write(
    "Upload any legal document (.docx) with placeholders like [Company Name], [Effective Date], or $[Amount]. "
    "Then chat naturally with the AI to fill in all placeholders. When finished, type **'done'** or click "
    "**Generate Final Document** to download the completed version."
)

groq_api_key = st.sidebar.text_input("Groq API key", type="password")
if not groq_api_key:
    st.warning("Please provide your Groq API key in the sidebar to continue.")
    st.stop()

client = Groq(api_key=groq_api_key)

uploaded = st.file_uploader("Upload a .docx legal document", type=["docx"])
if not uploaded:
    st.info("Please upload a .docx file to start.")
    st.stop()

def load_docx(file_bytes):
    return Document(file_bytes)


def extract_placeholders(doc: Document):
    regex = re.compile(r"(\$?\[+[^\[\]]+\]+)")
    found = []
    for p in doc.paragraphs:
        for m in regex.findall(p.text):
            found.append(m)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for m in regex.findall(cell.text):
                    found.append(m)
    seen = []
    for f in found:
        if f not in seen:
            seen.append(f)
    return seen


def replace_placeholders(doc: Document, mapping: dict):
    def replace_in_text(text):
        for k, v in mapping.items():
            text = text.replace(k, v)
        return text

    for p in doc.paragraphs:
        if any(k in p.text for k in mapping):
            new_text = replace_in_text(p.text)
            for i in range(len(p.runs) - 1, -1, -1):
                p.runs[i]._element.getparent().remove(p.runs[i]._element)
            p.add_run(new_text)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if any(k in cell.text for k in mapping):
                    new_text = replace_in_text(cell.text)
                    cell._tc.clear_content()
                    cell.add_paragraph(new_text)
    return doc


doc = load_docx(uploaded)
placeholders = extract_placeholders(doc)

if not placeholders:
    st.warning("No placeholders found. Ensure placeholders are written in [brackets].")
    st.stop()

st.subheader(f"Detected {len(placeholders)} placeholders:")
st.write(placeholders)


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "placeholder_values" not in st.session_state:
    st.session_state.placeholder_values = {ph: "" for ph in placeholders}


def get_missing_placeholders(values_dict):
    return [k for k, v in values_dict.items() if not v.strip()]


def groq_conversational_update(user_message, chat_history, placeholders, current_values):
    """Sends user input + context to Groq and gets updated mapping and reply."""
    missing = get_missing_placeholders(current_values)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI legal assistant helping the user fill placeholders in a legal document. "
                "Each placeholder looks like [Company Name], [Effective Date], [Amount], etc. "
                "The user will provide values conversationally. Maintain and update a JSON mapping of "
                "placeholder → value as the user talks.\n\n"
                "Guidelines:\n"
                "- Respond naturally and confirm what was updated.\n"
                "- If some placeholders are still missing, remind the user.\n"
                "- When all placeholders are filled or the user says 'done', say that the document is ready.\n"
                "- Always include a JSON block with the updated mapping after each reply."
            ),
        }
    ]

    for m in chat_history:
        messages.append(m)

    messages.append(
        {
            "role": "user",
            "content": (
                f"Current placeholder values: {json.dumps(current_values)}\n\n"
                f"Missing placeholders: {missing}\n\n"
                f"User message: {user_message}"
            ),
        }
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
        max_tokens=700,
    )

    content = response.choices[0].message.content
    reply = content

    match = re.search(r"\{.*\}", content, re.S)
    if match:
        try:
            parsed = json.loads(match.group(0))
            for k, v in parsed.items():
                for ph in placeholders:
                    if k.strip().lower().replace(" ", "") in ph.lower().replace(" ", ""):
                        current_values[ph] = v
        except Exception:
            pass

    missing_after = get_missing_placeholders(current_values)
    if missing_after:
        reply += (
            f"\n\nYou still need to provide values for: {', '.join(missing_after)}."
        )
    else:
        reply += "\n\nAll placeholders are filled! You can now generate your final document."

    return reply, current_values



st.header("Chat with the AI to Fill Your Document")

user_message = st.chat_input("Type your message here...")

if user_message:
    st.session_state.chat_history.append({"role": "user", "content": user_message})

    reply, updated_values = groq_conversational_update(
        user_message,
        st.session_state.chat_history,
        placeholders,
        st.session_state.placeholder_values,
    )

    st.session_state.placeholder_values = updated_values
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        with st.chat_message("user"):
            st.write(chat["content"])
    else:
        with st.chat_message("assistant"):
            st.write(chat["content"])

filled_count = sum(1 for v in st.session_state.placeholder_values.values() if v)
st.progress(filled_count / len(placeholders))
st.write(f"Filled {filled_count} of {len(placeholders)} placeholders")

with st.expander("Current Placeholder Values"):
    st.json(st.session_state.placeholder_values)


if st.button("Generate Final Document") or user_message and user_message.lower().strip() == "done":
    filled_doc = replace_placeholders(load_docx(uploaded), st.session_state.placeholder_values)
    bio = BytesIO()
    filled_doc.save(bio)
    bio.seek(0)
    st.success("All placeholders replaced — document ready!")
    st.download_button("Download Completed Document", data=bio, file_name="filled_document.docx")
    preview = [p.text for p in filled_doc.paragraphs[:30] if p.text.strip()]
    st.subheader("Preview (first few paragraphs)")
    st.text("\n\n".join(preview))