import google.generativeai as genai

def modify(text, job_description):
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"""You are an expert in LaTeX resume customization. Modify the following LaTeX resume code to align with the provided job description. Ensure that:

    - The resume highlights experiences, skills, and achievements relevant to the job description.
    - Unrelated or less relevant content is minimized or removed.
    - The formatting remains clean and professional.
    - The modified code is valid LaTeX and ready for compilation.

    Job Description:
    {job_description}

    LaTeX Resume Code:
    {text}
"""
    response = model.generate_content(prompt)

     # Extract summary out of response
    modified = response.candidates[0].content.parts[0].text
    return modified