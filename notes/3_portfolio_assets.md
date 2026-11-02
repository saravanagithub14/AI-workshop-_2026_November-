# Part 3: Make Your Personalized AI Portfolio Assets

In Part 2 the AI answered questions from your documents. In this part the AI **writes things for you** from your document: a LinkedIn profile, resume bullet points, a GitHub profile README and an interview self-introduction.

File: `portfolio_assets.py`

> Finish Part 1 first. You need the same `.venv` and `.env` file.

---

## What you will learn

- How to reuse **one prompt** with different **instructions** to make many outputs
- How to stop the AI from **inventing** facts about you
- How to save AI output into **files**
- How to build a Gradio page with a **text box and a dropdown**

---

## 1. Key ideas

| Word | What it means |
|---|---|
| **Profile** | Your `docs/about_me.md` file: the facts about you |
| **Asset** | One piece of writing for your portfolio, like a LinkedIn About section |
| **Instruction** | The part of the prompt that says *what* to write. Each asset has its own instruction. |
| **Rules** | The part of the prompt that says what the AI must **not** do. All assets share the same rules. |
| **Placeholder** | Text like `[add your GitHub link]` that shows where you need to fill in something yourself |

### How it works

```
  docs/about_me.md  (your facts)
          |
          v
  For each asset:   instruction + rules + your profile  =  one prompt
          |
          v
  Groq AI writes the asset
          |
          v
  Saved as a file in the portfolio/ folder
```

It is the same idea as RAG in Part 2, but simpler: your profile is short, so we send **all** of it instead of searching for the right paragraphs.

---

## 2. The code, step by step

Open `portfolio_assets.py` and follow along.

### Step 1: Connect to Groq

```python
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
```

Exactly the same as Part 1.

### Step 2: One instruction for each asset

```python
ASSETS = {
    "linkedin_about": "Write a LinkedIn headline (under 220 characters) and a LinkedIn About section ...",
    "resume_bullets": "Write 4 to 6 resume bullet points. Start each with a strong action verb. ...",
    "github_readme": "Write a GitHub profile README in Markdown: ...",
    "elevator_pitch": "Write a 30-second self-introduction for an interview, ...",
}
```

`ASSETS` is a **dictionary**. The **key** (like `"linkedin_about"`) is the asset's name and becomes its file name. The **value** is the instruction we give the AI.

To make a new kind of asset, just add one more line. No other code changes.

### The rules

```python
RULES = """Use ONLY the facts in the profile below. Do not invent jobs, companies, numbers or skills.
If something useful is missing, write a placeholder in square brackets, like [add your GitHub link]."""
```

Without these rules, an AI writing a resume will happily add skills, companies and numbers you never gave it. That would be a disaster in an interview. These two lines are the same trick as the *"use ONLY the information below"* rule in Part 2.

### Step 3: Ask the AI for one asset

```python
def make_asset(profile, instruction):
    prompt = f"""{instruction}
{RULES}

Profile:
{profile}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
```

We glue three things into one prompt: **what to write**, **the rules**, and **your profile**. Then we send it to Groq, the same way as before.

### Make every asset and save it

```python
def make_all_assets():
    profile = read_profile()
    os.makedirs("portfolio", exist_ok=True)

    for name, instruction in ASSETS.items():
        print("Writing", name, "...")
        text = make_asset(profile, instruction)
        with open(f"portfolio/{name}.md", "w", encoding="utf-8") as f:
            f.write(text)
```

- `read_profile()` reads `docs/about_me.md`.
- `os.makedirs("portfolio", exist_ok=True)` makes the `portfolio` folder. `exist_ok=True` means "don't complain if it's already there".
- `ASSETS.items()` gives us each name and instruction, one pair at a time.
- `open(..., "w")` opens a file for **writing**. If the file exists, it is replaced.

### In the browser

```python
gr.Interface(
    make_in_browser,
    inputs=[
        gr.Textbox(value=read_profile(), lines=15, label="About you"),
        gr.Dropdown(list(ASSETS), value="linkedin_about", label="Asset to make"),
    ],
    outputs=gr.Markdown(),
    title="My AI Portfolio Assets",
).launch()
```

In Parts 1 and 2 we used `gr.ChatInterface`, which is made for chatting. Here we use `gr.Interface`, which works for **any** function:

- `inputs` is a list of boxes. Gradio passes them to `make_in_browser` **in the same order**: the text box becomes `profile`, the dropdown becomes `asset_name`.
- The text box starts filled with your `about_me.md`, so you can edit it right on the page.
- `outputs=gr.Markdown()` shows the answer with bold text, bullet points and tables.

---

## 3. Run it

Make sure `(.venv)` is showing.

### Step 1: Write your profile

Replace the sample text in `docs/about_me.md` with **your** details: education, skills, projects, internships, achievements. Real numbers help ("cut report time by 40 percent").

### Step 2: Make all the assets

```powershell
python portfolio_assets.py
```

```
Writing linkedin_about ...
Writing resume_bullets ...
Writing github_readme ...
Writing elevator_pitch ...
Done. Open the portfolio folder to see your assets.
```

Open the `portfolio` folder. There is one `.md` file per asset.

### Or use the web page

```powershell
python portfolio_assets.py --web
```

Open the link it prints, pick an asset from the dropdown, and press **Submit**.

### Step 3: Check before you use it

The AI is a first draft, not the final version. **Read every line**, fix anything that isn't true, and fill in the `[placeholders]`.

---

## 4. Try it yourself

1. **Add a new asset.** Add a line to `ASSETS`, for example `"cover_letter": "Write a short cover letter for a data analyst job."`. Run it again.
2. **Remove the rules.** Delete `{RULES}` from the prompt and run it. Does the AI invent anything? Put it back.
3. **Pick a tone.** Add `"Write in a confident but humble tone."` to one instruction and compare.
4. **Use your GitHub README.** Copy `portfolio/github_readme.md` into a new GitHub repo named exactly like your username. GitHub shows it on your profile page.
5. **Combine with Part 2.** Put your resume as a `.txt` file in `docs/`, re-index, and ask the RAG chatbot questions about it.

---

## 5. Common problems and fixes

| Problem | What it means | Fix |
|---|---|---|
| `FileNotFoundError: ... docs/about_me.md` | The profile file is missing, or you are in the wrong folder | Make sure `docs/about_me.md` exists and run the command from the project folder |
| The assets are still about Asha | You didn't change the sample profile | Write your own details in `docs/about_me.md` and run it again |
| The AI added something that isn't true | AI can still make mistakes | Fix it by hand, and make the profile clearer about that point |
| `Error code: 429 ... rate limit` | 4 requests in a row can hit the free limit | Wait a minute and run it again |
| Any other Groq error (401, 404) | Same as Part 1 | See the table at the end of Part 1 |

---

## Summary

- One **instruction** per asset, plus shared **rules**, plus your **profile** = one prompt.
- The rules (*"use ONLY the facts"*, *"use placeholders"*) stop the AI from inventing things about you.
- A dictionary makes it easy to add new assets with one line.
- `gr.Interface` turns any function into a web page with your own inputs.
- **Always check AI writing before you put your name on it.**
