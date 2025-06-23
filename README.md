# NerdNET: RAG-Based Chatbot with Multimodal Query Resolution 

NerdNET is a full-stack Retrieval-Augmented Generation (RAG) chatbot designed to provide **context-aware answers** from PDF documents using **LlamaIndex**, **OpenAI's GPT-4**, and **Streamlit**. It supports **text Q&A, image generation, text-to-speech, and PowerPoint synthesis**, with user authentication and analytics.

---

## 🚀 Features

- 🔍 Document-grounded Q&A using OpenAI embeddings (`text-embedding-3-large`)
- 🖼️ Image generation based on user queries
- 🔊 Text-to-speech responses
- 📊 Session-aware analytics dashboard (usage metrics, chat history)
- 🔐 User authentication with SQLite
- 🧠 PDF parsing + persistent vector indexing

---

## 🛠️ Tech Stack

| Area             | Tools / Libraries                      |
|------------------|----------------------------------------|
| Frontend         | Streamlit                              |
| Backend (AI)     | OpenAI GPT-4, LlamaIndex                |
| Embeddings       | OpenAI `text-embedding-3-large`        |
| Data Storage     | SQLite (user sessions + analytics)     |
| PDF Parsing      | PyMuPDF (fitz), LlamaIndex             |
| Image Gen        | OpenAI DALL·E API                      |
| TTS              | pyttsx3 / gTTS                         |

---

## 📦 Installation

```bash
git clone https://github.com/yourusername/nerdnet-chatbot.git
cd nerdnet-chatbot
pip install -r requirements.txt

