# Part 1: Build Your First AI Chatbot

In this part you build a chatbot that talks like a friendly career mentor. You can chat with it in the **terminal** or in a **web page**.

File: `chatbot.py`

---

## What you will learn

- What an **API** and an **API key** are
- How to send a message to an AI model and get a reply
- How a **system prompt** controls the AI's personality
- How the chatbot **remembers** the conversation
- How to turn your chatbot into a web page with **Gradio**

---

## 1. Key ideas (read this first)

| Word | What it means |
|---|---|
| **AI model** | The "brain" that writes the answers. We use `openai/gpt-oss-120b`. It runs on Groq's computers, not yours. |
| **Groq** | A company that runs AI models very fast. We talk to it over the internet. |
| **API** | A way for your program to talk to another program. Your Python code sends a request to Groq and gets an answer back. |
| **API key** | A secret password that tells Groq who you are. **Never share it or post it online.** |
| **`.env` file** | A small text file where we keep secrets like the API key, so they are not written inside the code. |
| **Prompt** | The text you send to the AI. |
| **System prompt** | Instructions that tell the AI *who it is* and *how to behave*. The user does not see it. |
| **Gradio** | A Python library that turns a function into a web page with a chat box. |

### How the chatbot works

```
  You type a question
          |
          v
  Python adds it to the conversation list
          |
          v
  The whole list is sent to Groq  ----->  AI model writes a reply
                                                  |
          +---------------------------------------+
          v
  Python prints the reply and adds it to the list
          |
          v
  Ask the next question (the AI now "remembers" everything above)
```

---

## 2. One-time setup

Do these steps once, inside the `Groq_Chatbots` folder.

### Step 1: Create a virtual environment

A virtual environment (`.venv`) is a private box for this project's Python packages, so they don't clash with other projects.

```powershell
python -m venv .venv
```

### Step 2: Turn it on

```powershell
.\.venv\Scripts\Activate.ps1
```

You will see `(.venv)` at the start of the line. **Do this every time you open a new terminal.**

> If you see *"running scripts is disabled on this system"*, run this once, then try again:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### Step 3: Install the packages

```powershell
pip install -r requirements.txt
```

This installs:

| Package | Used for |
|---|---|
| `groq` | Talking to the Groq API |
| `python-dotenv` | Reading the `.env` file |
| `gradio` | The web page |
| `chromadb` | The search database (used in Part 2) |

### Step 4: Get your API key

1. Go to **console.groq.com** and sign in.
2. Open **API Keys** and click **Create API Key**.
3. Copy the key (it starts with `gsk_`).

### Step 5: Create the `.env` file

Make a file called `.env` in the `Groq_Chatbots` folder with these two lines:

```
GROQ_API_KEY=paste_your_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

No spaces around `=` and no quotes.

---

## 3. The code, step by step

Open `chatbot.py` and follow along.

### Part A: Import the tools we need

```python
import os
import sys
import gradio as gr
from dotenv import load_dotenv
from groq import Groq
```

- `os` lets us read settings like the API key.
- `sys` lets us check if you typed `--web` when running the program.
- `gradio` builds the web page.
- `load_dotenv` reads the `.env` file.
- `Groq` is the tool that talks to the AI.

### Part B (Step 1): Connect to Groq

```python
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
```

- `load_dotenv()` reads `.env` so Python can see your key.
- `client` is our connection to Groq. We will use it to send messages.
- `MODEL` is the name of the AI model. If `.env` doesn't set one, it uses `"openai/gpt-oss-120b"`.

### Part C (Step 2): Give the AI a personality

```python
SYSTEM_PROMPT = (
    "You are a friendly career mentor for college students. "
    "Keep answers short and practical. If you don't know, say so."
)
```

This is the **system prompt**. Change it and the chatbot becomes a different character. Try it in the exercises below.

### Part D (Step 3): Ask the AI

```python
def ask_ai(messages):
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content
```

- We send the model name and the list of `messages`.
- Groq sends back a `response`. The reply text is inside `response.choices[0].message.content`.

### The `messages` list

The conversation is a Python **list**. Each item is a **dictionary** with a `role` and some `content`:

```python
[
    {"role": "system",    "content": "You are a friendly career mentor..."},
    {"role": "user",      "content": "How do I write a resume?"},
    {"role": "assistant", "content": "Start with a short summary..."},
    {"role": "user",      "content": "How long should it be?"},
]
```

| Role | Who wrote it |
|---|---|
| `system` | You, the programmer: the instructions |
| `user` | The person chatting |
| `assistant` | The AI |

**Important:** the AI does not remember anything by itself. Every time we ask, we send the **whole list**. That is how it "remembers" earlier messages.

### Part E: Chat in the terminal

```python
def chat_in_terminal():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Chatbot ready. Type 'quit' to stop.\n")

    while True:
        question = input("You: ")
        if question == "quit":
            break

        messages.append({"role": "user", "content": question})
        answer = ask_ai(messages)
        messages.append({"role": "assistant", "content": answer})

        print("Bot:", answer, "\n")
```

1. Start the list with the system prompt.
2. `while True` keeps the chat going forever...
3. ...until you type `quit`, then `break` stops the loop.
4. Add your question to the list.
5. Send the list to the AI and get the answer.
6. Add the answer to the list too (this is the memory).
7. Print the answer.

### Part F: Chat in the web browser

```python
def chat_in_browser(question, history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for old_message in history:
        messages.append({"role": old_message["role"], "content": old_message["content"]})
    messages.append({"role": "user", "content": question})
    return ask_ai(messages)
```

Gradio calls this function every time you press send. It gives us:

- `question`: what you just typed
- `history`: the earlier messages in the chat

We build the same kind of `messages` list as before, then ask the AI.

> **Why do we copy only `role` and `content`?** Gradio stores some extra information in each message (like `metadata`). Groq doesn't accept those extra parts, so we copy only the two it needs.

### Part G: Start the chatbot

```python
if "--web" in sys.argv:
    gr.ChatInterface(chat_in_browser, title="My First AI Chatbot").launch()
else:
    chat_in_terminal()
```

`sys.argv` is the list of words you typed to run the program. If it contains `--web`, we open the web page. Otherwise we chat in the terminal.

`gr.ChatInterface(...)` builds a whole chat web page from our one function. `.launch()` starts it.

---

## 4. Run it

Make sure `(.venv)` is showing, then:

### In the terminal

```powershell
python chatbot.py
```

Example:

```
Chatbot ready. Type 'quit' to stop.

You: My name is Ravi and I study mechanical engineering.
Bot: Nice to meet you, Ravi! What kind of career help are you looking for?

You: What is my name and what do I study?
Bot: Your name is Ravi, and you're studying mechanical engineering.

You: quit
```

The second answer proves the memory works.

### In the web browser

```powershell
python chatbot.py --web
```

It prints a link like:

```
* Running on local URL:  http://127.0.0.1:7860
```

Open that link in your browser. Press **Ctrl + C** in the terminal to stop the web page.

---

## 5. Try it yourself

1. **New personality.** Change `SYSTEM_PROMPT` to make the bot a cricket coach, a cooking teacher, or a pirate. Run it again.
2. **Reply language.** Add `"Always reply in Tamil."` (or any language) to the system prompt.
3. **Turn off memory.** In `chat_in_terminal`, delete the line `messages.append({"role": "assistant", ...})`. Tell it your name, then ask for it. What happens? Why?
4. **Make it more creative.** Change the API call to:
   ```python
   response = client.chat.completions.create(model=MODEL, messages=messages, temperature=1.2)
   ```
   `temperature` controls randomness: `0` = same answer every time, higher = more creative. Ask the same question a few times and compare.
5. **Change the title.** Change `"My First AI Chatbot"` to your own title and run the web version.

---

## 6. Common problems and fixes

| Error message | What it means | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'groq'` | The virtual environment is not on | Run `.\.venv\Scripts\Activate.ps1`, then try again |
| `running scripts is disabled on this system` | PowerShell is blocking the activate script | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once |
| `Error code: 401 ... Invalid API Key` | The key in `.env` is wrong | Copy the key again from console.groq.com. Check there are no spaces or quotes |
| `The api_key client option must be set` | Python can't find your `.env` file | Make sure `.env` is in the `Groq_Chatbots` folder and you run the command from that folder |
| `Error code: 404 ... model ... does not exist` | That model name is old or wrong | Change `GROQ_MODEL` in `.env` to a model listed at console.groq.com/docs/models |
| `Error code: 429 ... rate limit` | Too many requests too fast (free plan limit) | Wait a minute and try again |
| Web page says port 7860 is in use | Another copy is already running | Gradio picks the next free port (7861, 7862...). Use the link it prints, or stop the old one with Ctrl + C |

---

## Summary

- The AI model runs on Groq. Your code talks to it through the **API** using your **API key**.
- The conversation is a **list of messages** with roles: `system`, `user`, `assistant`.
- The AI has no memory of its own. **We send the whole list every time.**
- The **system prompt** sets the AI's personality.
- **Gradio** turns one Python function into a chat web page.

**Next:** Part 2, where the chatbot answers questions from **your own documents**.
