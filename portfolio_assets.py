"""Turn a file about you into portfolio assets, using the Groq API.

How to use it:
  1. Write about yourself in docs/about_me.md (skills, projects, achievements).
  2. python portfolio_assets.py          (writes every asset into the portfolio/ folder)
     python portfolio_assets.py --web    (pick one asset in the web browser)
"""
import os
import sys
import gradio as gr
from dotenv import load_dotenv
from groq import Groq

# Step 1: Connect to Groq, same as Part 1
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Step 2: One instruction for each asset. Add your own to make more assets.
ASSETS = {
    "linkedin_about": "Write a LinkedIn headline (under 220 characters) and a LinkedIn About section "
                      "(3 short paragraphs, first person, friendly and confident).",
    "resume_bullets": "Write 4 to 6 resume bullet points. Start each with a strong action verb. "
                      "Use the numbers from the profile where there are any.",
    "github_readme": "Write a GitHub profile README in Markdown: a one-line intro, a list of skills, "
                     "and a table of projects with one line about each.",
    "elevator_pitch": "Write a 30-second self-introduction for an interview, in first person, under 90 words.",
}

# These rules stop the AI from making things up (the same idea as the RAG prompt in Part 2)
RULES = """Use ONLY the facts in the profile below. Do not invent jobs, companies, numbers or skills.
If something useful is missing, write a placeholder in square brackets, like [add your GitHub link]."""


# Step 3: Ask the AI to write one asset from the profile
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


def read_profile():
    with open("docs/about_me.md", encoding="utf-8") as f:
        return f.read()


# Make every asset and save each one as a file in the portfolio/ folder
def make_all_assets():
    profile = read_profile()
    os.makedirs("portfolio", exist_ok=True)

    for name, instruction in ASSETS.items():
        print("Writing", name, "...")
        text = make_asset(profile, instruction)
        with open(f"portfolio/{name}.md", "w", encoding="utf-8") as f:
            f.write(text)

    print("Done. Open the portfolio folder to see your assets.")


# In the browser: you can edit the profile and choose which asset to make
def make_in_browser(profile, asset_name):
    return make_asset(profile, ASSETS[asset_name])


# Start the program
if "--web" in sys.argv:
    gr.Interface(
        make_in_browser,
        inputs=[
            gr.Textbox(value=read_profile(), lines=15, label="About you"),
            gr.Dropdown(list(ASSETS), value="linkedin_about", label="Asset to make"),
        ],
        outputs=gr.Markdown(),
        title="My AI Portfolio Assets",
    ).launch()
else:
    make_all_assets()
