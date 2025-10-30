import streamlit as st
from groq import Groq
from io import BytesIO
import json
import re
from docx import Document

st.set_page_config(page_title="Context-Aware Legal Document Filler", layout="wide")

st.title("Context-Aware Legal Document Filler — Groq Llama 3.3 70B")
st.write(
    "Upload a legal document (.docx) with placeholders (e.g., [Company Name], [Effective Date]). "
    "The AI will understand the **context** of each placeholder from surrounding clauses and help you fill them conversationally."
)

# Sidebar
groq_api_key = st.sidebar.text_input("Groq API key", type="password")
if not groq_api_key:
    st.warning("Enter your Groq API key to start.")
    st.stop()

client = Groq(api_key=groq_api_key)


def load_docx(file_bytes):
    return Document(file_bytes)

def extract_placeholders_with_context(doc: Document, window=1):
    """Extract placeholders and their surrounding paragraph context."""
    regex = re.compile(r"(\$?\[+[^\[\]]+\]+)")
    placeholders = []
    contexts = {}

    for i, p in enumerate(doc.paragraphs):
        found = regex.findall(p.text)
        if found:
            context_snippet = []
            for offset in range(-window, window + 1):
                j = i + offset
                if 0 <= j < len(doc.paragraphs) and doc.paragraphs[j].text.strip():
                    context_snippet.append(doc.paragraphs[j].text.strip())
            for f in found:
                placeholders.append(f)
                contexts[f] = " ".join(context_snippet)
    seen, uniq_placeholders = set(), []
    for p in placeholders:
        if p not in seen:
            uniq_placeholders.append(p)
            seen.add(p)
    return uniq_placeholders, contexts

def replace_placeholders(doc: Document, mapping: dict):
    def replace_in_text(text):
        for k,v in mapping.items():
            text = text.replace(k, v)
        return text
    for p in doc.paragraphs:
        if any(k in p.text for k in mapping):
            new_text = replace_in_text(p.text)
            for i in range(len(p.runs)-1, -1, -1):
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

def get_missing_placeholders(values_dict):
    return [k for k,v in values_dict.items() if not v.strip()]

uploaded = st.file_uploader("Upload your .docx document", type=["docx"])
if not uploaded:
    st.info("Please upload a .docx file to continue.")
    st.stop()

doc = load_docx(uploaded)
placeholders, contexts = extract_placeholders_with_context(doc)

if not placeholders:
    st.warning("No placeholders found. Ensure placeholders are in [brackets].")
    st.stop()

st.subheader(f"Detected {len(placeholders)} placeholders:")
for ph in placeholders:
    with st.expander(f"{ph} — Context"):
        st.write(contexts.get(ph, "(No context found)"))

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "placeholder_values" not in st.session_state:
    st.session_state.placeholder_values = {ph: "" for ph in placeholders}

def groq_update(user_message, chat_history, placeholders, current_values, contexts):
    missing = get_missing_placeholders(current_values)
    context_text = "\n".join([f"{ph}: {contexts.get(ph, '')}" for ph in placeholders])

    system_prompt = (
        "You are an AI legal assistant helping the user fill placeholders in a legal document.\n"
        "You have access to the context around each placeholder (its clause text) so you can interpret meaning.\n"
        "Maintain a JSON mapping of placeholder→value as you chat.\n"
        "Provide a natural reply, confirm updates, and suggest if something looks like a date, amount, name, etc.\n"
        "Always include a JSON block of the updated mapping after each message.\n"
        "When all placeholders are filled or the user says 'done', indicate readiness for final document generation."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for m in chat_history:
        messages.append(m)

    messages.append(
        {
            "role": "user",
            "content": (
                f"Current mapping: {json.dumps(current_values)}\n\n"
                f"Missing: {missing}\n\n"
                f"Placeholder contexts:\n{context_text}\n\n"
                f"User message: {user_message}"
            ),
        }
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
        max_tokens=800,
    )

    content = response.choices[0].message.content
    reply = content

    match = re.search(r"\{.*\}", content, re.S)
    if match:
        try:
            parsed = json.loads(match.group(0))
            for k,v in parsed.items():
                for ph in placeholders:
                    if k.strip().lower().replace(" ","") in ph.lower().replace(" ",""):
                        current_values[ph] = v
        except Exception:
            pass

    missing_after = get_missing_placeholders(current_values)
    if missing_after:
        reply += f"\n\nRemaining placeholders: {', '.join(missing_after)}"
    else:
        reply += "\n\nAll placeholders filled. You can now generate your final document."

    return reply, current_values

st.header("Chat with the AI to Fill Your Document")
user_message = st.chat_input("Type a message (e.g., 'The Effective Date is Nov 1, 2025')")

if user_message:
    st.session_state.chat_history.append({"role": "user", "content": user_message})
    reply, updated_values = groq_update(
        user_message,
        st.session_state.chat_history,
        placeholders,
        st.session_state.placeholder_values,
        contexts,
    )
    st.session_state.placeholder_values = updated_values
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

filled_count = sum(1 for v in st.session_state.placeholder_values.values() if v)
st.progress(filled_count / len(placeholders))
st.write(f"Filled {filled_count}/{len(placeholders)} placeholders.")

with st.expander("Current Placeholder Values"):
    st.json(st.session_state.placeholder_values)


if st.button("Generate Final Document") or (
    user_message and user_message.lower().strip() == "done"
):
    filled_doc = replace_placeholders(load_docx(uploaded), st.session_state.placeholder_values)
    bio = BytesIO()
    filled_doc.save(bio)
    bio.seek(0)
    st.success("All placeholders replaced — document ready!")
    st.download_button("Download Completed Document", data=bio, file_name="filled_document.docx")
    preview = [p.text for p in filled_doc.paragraphs[:30] if p.text.strip()]
    st.subheader("Preview (first few paragraphs)")
    st.text("\n\n".join(preview))