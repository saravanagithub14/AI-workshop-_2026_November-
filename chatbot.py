"""A simple chatbot that uses the Groq API.

Chat in the terminal:      python chatbot.py
Chat in the web browser:   python chatbot.py --web
"""
import os
import sys
import gradio as gr
from dotenv import load_dotenv
from groq import Groq

# Step 1: Read the API key and model name from the .env file
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Step 2: Tell the AI who it is and how to behave
SYSTEM_PROMPT = (
    "You are a friendly career mentor for college students. "
    "Keep answers short and practical. If you don't know, say so."
)


# Step 3: Send the whole conversation to the AI and get its reply
def ask_ai(messages):
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content


# Chat in the terminal
def chat_in_terminal():
    # The conversation is a list of messages. It starts with the system prompt.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Chatbot ready. Type 'quit' to stop.\n")

    while True:
        question = input("You: ")
        if question == "quit":
            break

        messages.append({"role": "user", "content": question})
        answer = ask_ai(messages)
        messages.append({"role": "assistant", "content": answer})  # so the AI remembers it

        print("Bot:", answer, "\n")


# Chat in the web browser. Gradio calls this every time you send a message.
# "history" is the list of earlier messages in the chat.
def chat_in_browser(question, history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for old_message in history:
        messages.append({"role": old_message["role"], "content": old_message["content"]})
    messages.append({"role": "user", "content": question})
    return ask_ai(messages)


# Start the chatbot
if "--web" in sys.argv:
    gr.ChatInterface(chat_in_browser, title="My First AI Chatbot").launch()
else:
    chat_in_terminal()
