"""A RAG chatbot: it answers questions using YOUR documents.

How to use it:
  1. Put .txt or .md files in the docs/ folder.
  2. python rag_chatbot.py --index    (save the docs into a search database)
  3. python rag_chatbot.py            (chat in the terminal)
     python rag_chatbot.py --web      (chat in the web browser)

RAG = Retrieval-Augmented Generation:
  Retrieval  -> find the parts of your docs that match the question
  Generation -> give those parts to the AI so it answers from them
"""
import os
import sys
import glob
import chromadb
import gradio as gr
from dotenv import load_dotenv
from groq import Groq

# Step 1: Connect to Groq (the AI) and Chroma (the search database)
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

database = chromadb.PersistentClient(path="chroma_db")  # saved in the chroma_db folder
collection = database.get_or_create_collection("docs")


# Step 2: Save every paragraph of every doc into the database.
# Chroma turns each paragraph into numbers (an "embedding") so it can
# find paragraphs with a similar meaning later.
def build_index():
    # Start with an empty database, so deleted docs don't stay in it
    database.delete_collection("docs")
    collection = database.create_collection("docs")

    files = glob.glob("docs/*.txt") + glob.glob("docs/*.md")
    count = 0
    for file in files:
        with open(file, encoding="utf-8") as f:
            text = f.read()

        # A blank line separates paragraphs
        for paragraph in text.split("\n\n"):
            if paragraph.strip() == "":
                continue
            count += 1
            collection.add(
                ids=[f"paragraph-{count}"],
                documents=[f"[From {file}]\n{paragraph}"],  # keep the file name with the text
            )

    print(f"Saved {count} paragraphs from {len(files)} files.")


# Step 3: Answer a question using the docs
def answer(question, history):  # Gradio also sends the chat history; we don't use it
    if collection.count() == 0:
        return "No documents saved yet. Run: python rag_chatbot.py --index"

    # Retrieval: find the 3 paragraphs closest in meaning to the question
    results = collection.query(query_texts=[question], n_results=3)
    found_paragraphs = results["documents"][0]
    context = "\n\n".join(found_paragraphs)

    # Generation: give the AI those paragraphs and the question
    prompt = f"""Answer the question using ONLY the information below.
If the answer is not in the information, say: "I don't have that in my documents."
After the answer, name the file you used.

Information:
{context}

Question: {question}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


# Chat in the terminal
def chat_in_terminal():
    print("RAG chatbot ready. Type 'quit' to stop.\n")
    while True:
        question = input("You: ")
        if question == "quit":
            break
        print("Bot:", answer(question, []), "\n")


# Start the chatbot
if "--index" in sys.argv:
    build_index()
elif "--web" in sys.argv:
    gr.ChatInterface(answer, title="Ask My Documents").launch()
else:
    chat_in_terminal()
