# Part 2: Build a RAG Chatbot (Chat With Your Documents)

In Part 1 the chatbot could only answer from what the AI already knew. In this part you build a chatbot that answers questions using **your own documents**, and says *"I don't have that in my documents"* when the answer isn't there.

File: `rag_chatbot.py`

> Finish Part 1 first. You need the same `.venv` and `.env` file.

---

## What you will learn

- Why a normal chatbot can't answer questions about *your* files
- What **RAG** means, and its two steps: **Retrieval** and **Generation**
- What **embeddings** and a **vector database** are
- How to split documents into **chunks**
- How to write a prompt that stops the AI from making things up

---

## 1. The problem RAG solves

Ask the Part 1 chatbot: *"What projects has Asha built?"*

It has no idea who Asha is. Asha's details are in our file `docs/about_me.md`, and the AI has never seen that file. Worse, an AI will sometimes **make up** an answer that sounds right. This is called **hallucination**.

**The fix:** before asking the AI, we *find* the right parts of our documents and *paste them into the prompt*. Then the AI answers from that text, like an open-book exam.

That is **RAG: Retrieval-Augmented Generation**.

| Step | Plain English |
|---|---|
| **Retrieval** | Search your documents for the parts that match the question |
| **Augmented** | Add those parts to the prompt |
| **Generation** | The AI writes an answer using them |

---

## 2. Key ideas

| Word | What it means |
|---|---|
| **Document** | A `.txt` or `.md` file in the `docs/` folder |
| **Chunk** | A small piece of a document. We use one **paragraph** per chunk. |
| **Embedding** | A list of numbers that represents the *meaning* of a piece of text. Texts with similar meanings get similar numbers. |
| **Embedding model** | A small AI model that turns text into embeddings. Chroma uses one called `all-MiniLM-L6-v2`. It runs **on your computer**. |
| **Vector database** | A database that stores embeddings and can quickly find the ones closest to a question. We use **Chroma**. |
| **Index** | Saving all the chunks (and their embeddings) into the database, ready to search |
| **Context** | The chunks we found, pasted into the prompt |

### Why embeddings?

A normal search looks for the **same words**. Embeddings search by **meaning**.

The question *"Which tools does Asha know?"* doesn't contain the word "skills", but its meaning is close to the paragraph *"SQL, Python, Power BI and Excel..."*, so Chroma finds that paragraph.

> Groq doesn't make embeddings, so Chroma does that part on your computer. Groq is only used for the final answer.

---

## 3. How the RAG chatbot works

There are **two stages**.

### Stage 1: Indexing (run once, and again when your docs change)

```
  docs/about_me.md
          |
          v
  Split into paragraphs (chunks)
          |
          v
  Embedding model turns each paragraph into numbers
          |
          v
  Save them in the Chroma database (chroma_db folder)
```

### Stage 2: Answering (every question)

```
  You ask: "Which tools does Asha know?"
          |
          v
  RETRIEVAL: Chroma finds the 3 paragraphs closest in meaning
          |
          v
  AUGMENT: put those paragraphs + the question into one prompt
          |
          v
  GENERATION: Groq AI answers using ONLY those paragraphs
          |
          v
  "Asha knows SQL, Python, Power BI and Excel.  File used: docs\about_me.md"
```

---

## 4. The code, step by step

Open `rag_chatbot.py` and follow along.

### Step 1: Connect to Groq and Chroma

```python
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

database = chromadb.PersistentClient(path="chroma_db")
collection = database.get_or_create_collection("docs")
```

- The Groq part is the same as Part 1.
- `PersistentClient(path="chroma_db")` opens a database saved in the `chroma_db` folder. **Persistent** means it is saved to disk, so it is still there next time you run the program.
- A **collection** is like a table in the database. Ours is called `"docs"`.

### Step 2: Build the index

```python
def build_index():
    database.delete_collection("docs")
    collection = database.create_collection("docs")

    files = glob.glob("docs/*.txt") + glob.glob("docs/*.md")
    count = 0
    for file in files:
        with open(file, encoding="utf-8") as f:
            text = f.read()

        for paragraph in text.split("\n\n"):
            if paragraph.strip() == "":
                continue
            count += 1
            collection.add(
                ids=[f"paragraph-{count}"],
                documents=[f"[From {file}]\n{paragraph}"],
            )

    print(f"Saved {count} paragraphs from {len(files)} files.")
```

Line by line:

1. **Start fresh.** Delete the old collection and make a new empty one. Otherwise, text you removed from your docs would still be in the database.
2. **Find the files.** `glob.glob("docs/*.txt")` gives a list of every `.txt` file in `docs/`. We do the same for `.md` and join the two lists with `+`.
3. **Read each file** into the variable `text`.
4. **Split into paragraphs.** `"\n\n"` means two line breaks, which is a blank line. So `text.split("\n\n")` cuts the text at every blank line.
5. **Skip empty pieces.** `paragraph.strip()` removes spaces and line breaks. If nothing is left, `continue` skips to the next paragraph.
6. **Save the paragraph.** `collection.add(...)` stores it. Chroma makes the embedding for us automatically.
   - `ids` must be unique, so we number them: `paragraph-1`, `paragraph-2`, ...
   - We put the file name at the top of the text (`[From docs\about_me.md]`) so the AI can tell us which file it used.

### Why split into chunks at all?

- **Better search.** A small paragraph is about one topic, so it matches questions more precisely than a whole file.
- **Smaller prompts.** We send only the 3 most useful paragraphs to the AI, not every document.

### Step 3: Answer a question

```python
def answer(question, history):
    if collection.count() == 0:
        return "No documents saved yet. Run: python rag_chatbot.py --index"
```

If the database is empty, we tell the user to build the index first.

#### Retrieval

```python
    results = collection.query(query_texts=[question], n_results=3)
    found_paragraphs = results["documents"][0]
    context = "\n\n".join(found_paragraphs)
```

- `collection.query(...)` turns the question into an embedding and finds the **3 closest paragraphs**.
- We could ask several questions at once, so Chroma returns one list per question. We asked one, so we take item `[0]`.
- `"\n\n".join(...)` glues the paragraphs into one piece of text, with a blank line between each.

#### Augment + Generation

```python
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
```

- The `f"""..."""` string fills in `{context}` and `{question}`.
- Three rules in the prompt keep the AI honest:
  1. Use **ONLY** the information given (no guessing).
  2. If it isn't there, **say so** with a fixed sentence.
  3. **Name the file**, so we can check the answer.
- Then we send the prompt to Groq, exactly like Part 1.

#### What the AI actually receives

For the question *"Which tools does Asha know?"*, the prompt looks like this:

```
Answer the question using ONLY the information below.
If the answer is not in the information, say: "I don't have that in my documents."
After the answer, name the file you used.

Information:
[From docs\about_me.md]
## Skills
SQL, Python, Power BI and Excel. She used SQL at her internship to build a weekly sales dashboard.

[From docs\about_me.md]
...two more paragraphs...

Question: Which tools does Asha know?
```

> **Note:** this chatbot does **not** remember earlier questions. Gradio sends a `history`, but we don't use it. Every question is answered on its own, which keeps the RAG steps easy to follow.

### Step 4: Chat in the terminal

```python
def chat_in_terminal():
    print("RAG chatbot ready. Type 'quit' to stop.\n")
    while True:
        question = input("You: ")
        if question == "quit":
            break
        print("Bot:", answer(question, []), "\n")
```

Same loop as Part 1. We pass an empty list `[]` as the history because the terminal has none.

### Step 5: Start the chatbot

```python
if "--index" in sys.argv:
    build_index()
elif "--web" in sys.argv:
    gr.ChatInterface(answer, title="Ask My Documents").launch()
else:
    chat_in_terminal()
```

| You type | What happens |
|---|---|
| `python rag_chatbot.py --index` | Builds the database from `docs/` |
| `python rag_chatbot.py --web` | Opens the web page |
| `python rag_chatbot.py` | Chats in the terminal |

---

## 5. Run it

Make sure `(.venv)` is showing.

### Step 1: Add your documents

Put `.txt` or `.md` files in the `docs/` folder. There is already a sample file, `docs/about_me.md`. Leave a **blank line between paragraphs**, because that is how the code splits the text.

### Step 2: Build the index

```powershell
python rag_chatbot.py --index
```

```
Saved 6 paragraphs from 1 files.
```

The first time, Chroma downloads its embedding model (about 90 MB). After that it's saved on your computer.

### Step 3: Chat

In the terminal:

```powershell
python rag_chatbot.py
```

```
RAG chatbot ready. Type 'quit' to stop.

You: What did Asha build at her internship?
Bot: She built a weekly sales dashboard at her internship.
File used: docs\about_me.md

You: What is her favourite food?
Bot: I don't have that in my documents.

You: quit
```

The second answer shows the bot doesn't guess. That is exactly what we want.

Or in the browser:

```powershell
python rag_chatbot.py --web
```

Open the link it prints (for example `http://127.0.0.1:7860`). Press **Ctrl + C** to stop.

---

## 6. Try it yourself

1. **Use your own notes.** Write a file about yourself, your college, or a subject you're studying. Save it in `docs/`, run `--index` again, and ask questions about it.
2. **Forget to re-index.** Add a new line to `about_me.md` (for example *"Asha's favourite food is dosa."*) but **don't** run `--index`. Ask about it. Now run `--index` and ask again. What changed?
3. **Change how much is retrieved.** Change `n_results=3` to `n_results=1`. Do some answers get worse? Why?
4. **See what was found.** Add `print(context)` just after the `context = ...` line. Run the terminal version and look at what the AI is given for each question.
5. **Remove the rules.** Delete the line `If the answer is not in the information, say: ...` from the prompt and ask *"What is her favourite food?"* again. Does the AI start guessing?
6. **Compare with Part 1.** Ask the Part 1 chatbot *"What projects has Asha built?"* and compare its answer with the RAG chatbot's.

---

## 7. Common problems and fixes

| Problem | What it means | Fix |
|---|---|---|
| `No documents saved yet. Run: python rag_chatbot.py --index` | The database is empty | Run `python rag_chatbot.py --index` |
| `Saved 0 paragraphs from 0 files.` | No `.txt` or `.md` files found | Put files in the `docs/` folder and run the command from the project folder |
| The bot doesn't know something you just added | The database still has the old version | Run `--index` again after **every** change to `docs/` |
| Answers mix up topics | A paragraph is too long, or two topics share one paragraph | Add blank lines so each paragraph is about one thing, then re-index |
| `UnicodeDecodeError` | The file isn't saved as UTF-8 | In VS Code, click the encoding in the bottom bar, then **Save with Encoding**, then **UTF-8** |
| `ConnectTimeout` or `handshake operation timed out` during `--index` | Your network is blocking the embedding model download | See the fix below |
| Any Groq error (401, 404, 429) | Same as Part 1 | See the table at the end of Part 1 |

### Fix: the embedding model won't download

Chroma downloads its model from Amazon S3, which some college or office networks block. You can get the same model from Hugging Face instead. Save this as `download_model.py` in the project folder:

```python
import shutil
from pathlib import Path
from huggingface_hub import hf_hub_download

folder = Path.home() / ".cache" / "chroma" / "onnx_models" / "all-MiniLM-L6-v2" / "onnx"
folder.mkdir(parents=True, exist_ok=True)

files = ["onnx/model.onnx", "config.json", "special_tokens_map.json",
         "tokenizer_config.json", "tokenizer.json", "vocab.txt"]
for name in files:
    path = hf_hub_download("sentence-transformers/all-MiniLM-L6-v2", name)
    shutil.copyfile(path, folder / Path(name).name)
    print("Downloaded", name)
```

Run it once with `python download_model.py`, then run `python rag_chatbot.py --index` again.

---

## Summary

- A normal chatbot doesn't know your documents and may **make things up**.
- **RAG** = find the right text first (**Retrieval**), add it to the prompt (**Augmented**), then let the AI answer (**Generation**).
- **Embeddings** turn text into numbers that capture meaning, so we can search by meaning instead of exact words.
- **Chroma** is the vector database that stores the chunks and finds the closest ones.
- A clear prompt with rules ("use ONLY this", "say I don't know") keeps the answers honest.
- **Re-run `--index` every time your documents change.**

### Part 1 vs Part 2

| | Part 1: Chatbot | Part 2: RAG Chatbot |
|---|---|---|
| Knows your documents | No | Yes |
| Remembers the conversation | Yes | No (each question on its own) |
| Can make things up | Yes | Much less, because it must use the given text |
| Needs a database | No | Yes (Chroma) |
| Extra step before chatting | None | `python rag_chatbot.py --index` |
