## 🧠 **Lexi — AI Legal Document Assistant**

Lexi is an intelligent web application that helps users **complete legal document templates** conversationally.
It identifies placeholders in uploaded legal drafts, analyzes their context, interacts with the user to fill in missing details, and finally generates a polished `.docx` document.

---

### 🎯 **Project Goal**

The goal of this test assignment is to:

* Accept upload of a legal `.docx` document.
* Identify and distinguish **template text** from **dynamic placeholders**.
* Analyze placeholders to explain what data they expect.
* Provide a **conversational chatbot experience** to fill in the placeholders.
* Prevent final generation until all fields are filled.
* Display and allow download of the completed document through a **popup dialog**.

---

### ⚙️ **Tech Stack**

| Component                  | Technology                         |
| -------------------------- | ---------------------------------- |
| **Frontend**               | Streamlit (Python)                 |
| **LLM Backend**            | Groq API (Llama 3.3 70B Versatile) |
| **Document Handling**      | python-docx                        |
| **Environment Management** | python-dotenv                      |
| **Language**               | Python 3.10+                       |

---

### 🚀 **Features**

#### 🧩 Smart Placeholder Detection

Lexi scans the uploaded `.docx` document to detect placeholders written in formats like `[Company Name]`, `$[Investment Amount]`, etc.
It distinguishes between **template text** (static legal clauses) and **dynamic placeholders** (variables that require user input).

#### 🧠 Contextual Analysis

Each placeholder is analyzed using Groq’s LLM to understand:

* What type of information is expected (e.g., company name, date, amount).
* A short natural-language description.
* Example values for user clarity.

#### 💬 Conversational Filling

Lexi acts as a friendly, professional **AI legal assistant**.
It initiates the conversation, explains its role, and guides the user through all required inputs via natural dialogue.
Users can respond freely (e.g., “The investor name is John Smith Ventures”).

#### 🧾 Validation and Completion

* Lexi tracks progress for each placeholder.
* It only enables the **“Generate Final Document”** button once every placeholder is filled.
* A progress bar shows completion percentage.

#### 🪄 Popup Final Preview

When ready, Lexi opens a **popup dialog** showing:

* A short preview of the completed document.
* A “Download Completed Document” button for `.docx`.
* Instructions to return to chat for corrections.

#### 🔐 Secure API Key Management

Uses a `.env` file for the **Groq API key** (with sidebar fallback if missing).
Supports both local and deployed environments.

---

### 📂 **Project Structure**

```
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                   # (Not committed) Contains GROQ_API_KEY
├── sample.docx            # Example input legal document
└── README.md              # Project documentation
```

---

### 🧩 **How to Run Locally**

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/lexi-legal-assistant.git
cd lexi-legal-assistant
```

#### 2. Set Up Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate       # (Linux/Mac)
.venv\Scripts\activate          # (Windows)
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment

Create a `.env` file in the root directory:

```
GROQ_API_KEY=your_real_groq_api_key_here
```

#### 5. Run the App

```bash
streamlit run app.py
```

---

### 🧠 **How It Works (Workflow Overview)**

1. **Upload Document** → User uploads `.docx` legal draft.
2. **Lexi Analyzes** → LLM identifies placeholders and provides semantic explanations.
3. **Conversation Begins** → Lexi introduces itself and starts asking about missing fields.
4. **User Responds** → Lexi interprets user input and updates placeholder values.
5. **Progress Check** → Lexi shows progress (e.g., “5/7 placeholders filled”).
6. **Finalization** → Once all placeholders are filled, user clicks “Generate Final Document.”
7. **Popup Preview** → A dialog displays preview text and download button.

---

### 🧰 **Example Placeholders**

| Placeholder            | Description                           | Example          |
| ---------------------- | ------------------------------------- | ---------------- |
| `[Company Name]`       | Legal name of the issuing entity      | Acme Corp        |
| `[Effective Date]`     | Date when the agreement becomes valid | November 1, 2025 |
| `$[Investment Amount]` | Capital amount invested               | $1,000,000       |

---

### 🧑‍⚖️ **Lexi’s Personality**

Lexi is designed to sound **professional, polite, and clear**, maintaining a friendly yet formal tone appropriate for legal workflows:

> “Hi there! I’m Lexi, your AI legal assistant. I’ve reviewed your document and found a few placeholders we need to fill. Let’s go through them together.”

---

### 🔒 **Security**

* API key never stored in the code or repo.
* `.env` file excluded via `.gitignore`.
* No user documents are transmitted anywhere except to Groq for contextual understanding.

---

### 🧩 **Future Improvements**

* Multi-party placeholder handling (`[Company Name]#1`, `[Company Name]#2`)
* Context-based tone adjustment (formal vs casual documents)
* Real-time HTML highlighting for placeholders
* Support for `.pdf` input parsing
