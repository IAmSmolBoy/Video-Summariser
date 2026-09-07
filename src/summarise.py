import os
import re
import sys
from google.genai import Client


from src.transcribe import download, transcribe


# Only run this block for Gemini Developer API
client = Client(api_key=os.getenv("GEMINI_API_KEY"))
INSTRUCTIONS = "Summarize this chronologically in bullet points with section headers that include an emoji within 5000 characters in raw markdown"
MODEL = "gemini-2.5-flash"
TOKEN_LIMIT = 100000


def prompt(content: str):
    print(f"Summarising {len(content)} characters...")
    
    response = client.models.generate_content(
        model=MODEL,
        contents={
            "text": f"{content}\n\n{INSTRUCTIONS}"
        }
    )
        
    print(f"tokens used: {response.candidates[0]}")
    
    return response.text


def summarise():
    
    full = ""

    with open("out.md", "w") as f:
        f.write("")
        
    for line in open("transcript.txt", "r").readlines():
        
        if re.match(r"^\d{1,2}:\d{2}.*$", line):
            continue

        full += line.strip().replace("  ", "\n") + " "
        
    if len(full) < TOKEN_LIMIT:
        with open("out.md", "a", encoding="utf-8") as f:
            f.write(prompt(full))
        return

    summaries = ""

    for i in range(TOKEN_LIMIT - 1000, len(full) - 1000, TOKEN_LIMIT):
        for j in range(i, i + 1000):
            if j > len(full) or full[j] == " ":
                content = full[:j]
                
                if summaries:
                    summaries += " "
                
                summaries += prompt(content)
                break
            
    with open("summaries.md", "a", encoding="utf-8") as f:
        f.write(summaries)
            
    with open("out.md", "a", encoding="utf-8") as f:
        f.write(prompt(summaries))

            
if __name__ == "__main__":
    
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        download(sys.argv[1])
    
    transcribe()
    
    summarise()
    
    client.close()