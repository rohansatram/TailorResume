import subprocess
import os
import shutil
from modify import *
import os
from dotenv import load_dotenv

load_dotenv()

os.environ['GOOGLE_API_KEY'] = os.getenv('API_KEY')
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

def compile_latex(tex_file):
    tex_dir = os.path.dirname(os.path.abspath(tex_file))
    tex_filename = os.path.basename(tex_file)

    try:
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_filename],
            cwd=tex_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print("LaTeX compilation succeeded.")
        print(result.stdout.decode())
    except subprocess.CalledProcessError as e:
        print("LaTeX compilation failed.")
        print(e.stdout.decode())
        print(e.stderr.decode())

def clean_auxiliary_files(tex_file):
    tex_dir = os.path.dirname(os.path.abspath(tex_file))
    base_name = os.path.splitext(os.path.basename(tex_file))[0]
    extensions = ['aux', 'log', 'out', 'toc', 'synctex.gz']

    for ext in extensions:
        file_path = os.path.join(tex_dir, f"{base_name}.{ext}")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed {file_path}")

# Copy the .cls file
cls_source = 'resume/resume.cls'
cls_destination = 'resume/modified.cls'
if os.path.exists(cls_source):
    shutil.copyfile(cls_source, cls_destination)
    print(f"Copied {cls_source} to {cls_destination}")
else:
    print(f"Error: Source file {cls_source} not found.")

# Read the original .tex file
with open('resume/resume.tex', 'r', encoding='utf-8') as file:
    content = file.read()

# Modify the content with job description
job_description = ""
modified = modify(content, job_description)

# Save the modified content to a new .tex file
modified_tex_path = 'resume/modified.tex'
with open(modified_tex_path, 'w', encoding='utf-8') as file:
    file.write(modified)
print(f"Modified resume content saved to {modified_tex_path}")

# Compile the modified LaTeX file
compile_latex(modified_tex_path)

# Clean auxiliary files
clean_auxiliary_files(modified_tex_path)