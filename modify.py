import os
from dotenv import load_dotenv
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

google_search_tool = Tool(google_search=GoogleSearch())

# 1. Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 2. Initialize GenAI client
client = genai.Client(api_key=api_key)

def modify(text, job_description):
    # 1. Extract relevant keywords from the job description using Search
    search_prompt = f"""
    You are a keyword extractor.
    List exactly 15 keywords
    Do not include any explanations, descriptions, or extra text—only the five keywords.

    Job Description:
    {job_description}
    """
    search_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=search_prompt,
        config=GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"]
        )
    )
    keywords = search_response.candidates[0].content.parts[0].text.strip()

    # Save keywords to a file
    with open("keywords.txt", "w") as f:
        f.write(keywords)

    # 2. Modify the LaTeX resume incorporating those keywords
    prompt = f"""You are an expert in LaTeX resume customization.
    Please adhere to the following formatting rules before making any changes:
    - Keep the preamble as is on the template (LaTeX preamble below) to prevent hyphenation issues and text bleeding:
    \\documentclass{{resume}}
    \\usepackage{{ragged2e}}
    \\hyphenpenalty=10000
    \\exhyphenpenalty=10000
    \\tolerance=1000
    \\begin{{document}}
    \\RaggedRight

    - Plain-text only: Do not use any Markdown syntax (no `**`, `*`, `#`, backticks, etc.).
    - No double-asterisk wrapping: Do not wrap any phrase (e.g. “Manufacturing Processes” or anything else) in `**…**`.

    Now, modify the LaTeX resume code below to align with the provided job description. Ensure that:
    - The resume highlights experiences, skills, and achievements relevant to the job description.
    - The formatting remains clean and professional.
    - The modified code is valid LaTeX and ready for compilation.
    - The overall length stays the same.
    - Incorporate these keywords where relevant: {keywords}

    Job Description:
    {job_description}

    LaTeX Resume Code:
    {text}
    """
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=GenerateContentConfig(response_modalities=["TEXT"])
    )

    # Return the modified LaTeX code
    return response.candidates[0].content.parts[0].text