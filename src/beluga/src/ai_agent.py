# install once: pip install "openai>=1.0.0"
import os
import time
from openai import OpenAI
from dotenv import load_dotenv  
import glob

def read_docs_files():
    """Read all markdown files from docs/ directory"""
    docs_content = ""
    try:
        # Find all .md files in docs/ directory
        doc_files = glob.glob("docs/*.md") + glob.glob("docs/**/*.md", recursive=True)
        
        if not doc_files:
            return "No documentation files found in docs/ directory."
        
        for doc_file in doc_files:
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    docs_content += f"\n--- {doc_file} ---\n{content}\n"
            except Exception as e:
                print(f"⚠️ Could not read {doc_file}: {e}")
        
        return docs_content if docs_content else "No readable documentation found."
        
    except Exception as e:
        print(f"⚠️ Error reading docs: {e}")
        return "Error reading documentation files."
# ── 1. Configuration ──────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("NARWHAL_API_KEY")
ENDPOINT_URL = "https://hackathon-narwhal-t2.westus2.inference.ml.azure.com/v1"
MODEL_NAME = "/models/checkpoint-11871"

GENERATION_ARGS = {
    "temperature": 0.5,
    "top_p": 0.95,
    "max_tokens": 2048,
    "extra_body": {
        "chat_template_kwargs": {"enable_thinking": False}
    }
}

# ── 2. Narwhal Client Setup ───────────────────────────────────────────────────
client = OpenAI(api_key=API_KEY, base_url=ENDPOINT_URL)
messages = [
    {"role": "system", "content": "You are Beluga, a C3.ai PR Making Agent"}
]

def ask_llm(user_msg: str) -> str:
    """Append user_msg → call Narwhal → append assistant reply → return reply."""
    messages.append({"role": "user", "content": user_msg})
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        **GENERATION_ARGS
    )
    assistant_reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": assistant_reply})
    return assistant_reply

# ── 3. Draft PR Function ──────────────────────────────────────────────────────
def draft_pr_with_ai(files, jira, template,pr):
    dC = read_docs_files()

    """
    Given a list of changed files, Jira info, and template,
    return a tuple (title, body) drafted by Narwhal.
    """
    # Gather file diffs
    diffs_text = "\n\n".join(file.get('diff', '') for file in files)
    changed_files = [file.get('path', '') for file in files]

    # Load STANDARDS.md if it exists
    try:
        with open("STANDARDS.md", "r", encoding="utf-8") as f:
            standards = f.read()
    except FileNotFoundError:
        standards = "No STANDARDS.md found."

    # Build prompt
    prompt = f"""
You are a software assistant that drafts high-quality GitHub pull request titles and bodies.

Use the following information and please edit the PR to reflect those changes. The title of the PR should be the Jira Ticket # + FULL TITLE

--- Jira Info ---
{jira}

--- PR Template ---
{template}

--- Standards ---
{standards}

--- Changed Files ---
{chr(10).join(changed_files)}

--- Code Diffs ---
{diffs_text}



Please return:
Use one of these formats based on the name of the branch {dC}
- The TITLE IS THE WHOLE TITLE OF THE JIRA TICKET always
- Add the actual link to the jira ticket always
- Include a technically precise summary ALWAYS about the ticket and what the code does
- Make sure to actually include your own description of the sumary of changes using {jira} and this is the media files {pr}
"""

    # Call Narwhal
    response = ask_llm(prompt).strip()

    # Parse result
    raw_title = jira.split(":")[0].strip() + " " + jira.split(":")[1].strip()
    title = raw_title.split("|")[0].strip()
    lines = response.split("\n", 1)
    body = lines[1].strip() if len(lines) > 1 else ""
    body += pr 

    return title, body


