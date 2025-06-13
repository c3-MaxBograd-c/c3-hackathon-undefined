import os
import time
import openai

def draft_pr_with_ai(files, jira, template):
    """
    Given a list of changed files, Jira info, and template,
    return a tuple (title, body) drafted by an OpenAI Assistant.
    """
    # 1. Gather file diffs
    diffs_text = "\n\n".join(file.get('diff', '') for file in files)
    changed_files = [file.get('path', '') for file in files]

    # 2. Load STANDARDS.md if it exists
    standards = ""
    try:
        with open("STANDARDS.md", "r", encoding="utf-8") as f:
            standards = f.read()
    except FileNotFoundError:
        standards = "No STANDARDS.md found."


    prompt_content = f"""
You are a software assistant that drafts high-quality GitHub pull request titles and bodies.

Use the following information and please edit the pr to reflect those changes and the title of the pr should be the jira ticker number:

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
- The TITLE IS JUST THE TICKET NUMBER THAT IS
- A clear and concise PR body beneath it(no ai comments,just the body) please do not add ur comments in the title or body.
"""

    # 4. Set up OpenAI
    assistant_id = os.getenv('OPENAI_ASSISTANT_ID')

    if not assistant_id:
        raise RuntimeError("OPENAI_ASSISTANT_ID environment variable not set.")

    # 5. Create a thread and run
    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt_content,
    )
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )

    # 6. Wait for completion
    while True:
        run_status = openai.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        )
        if run_status.status in ["completed", "failed", "cancelled"]:
            break
        time.sleep(2)

    if run_status.status != "completed":
        raise RuntimeError(f"Assistant run failed with status: {run_status.status}")

    # 7. Get response
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    content = messages.data[0].content[0].text.value.strip()
    lines = content.split("\n", 1)
    title = jira.split(":")[0].strip()  
    body = lines[1].strip() 

    return title, body
