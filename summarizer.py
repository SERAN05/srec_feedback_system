import subprocess

def summarize_feedback(category: str, comments: list[str]) -> str:
    if not comments:
        return "No feedback available."

    # Combine all comments into one block of text
    input_text = "\n".join(comments)

    # Create the summarization prompt
    prompt = f"""
    You are analyzing student feedback.
    Category: {category}
    Comments:
    {input_text}

    Task: Generate a concise summary (3–5 sentences). Highlight praises and issues.
    Avoid mentioning names. Keep it professional and actionable.
    """

    # Run Mistral via Ollama
    result = subprocess.run(
        ["ollama", "run", "mistral"],
        input=prompt.encode("utf-8"),
        capture_output=True,
    )

    return result.stdout.decode("utf-8").strip()
