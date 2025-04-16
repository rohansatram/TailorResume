import subprocess
import os
import shutil
import re
from flask import Flask, render_template, request, send_from_directory, abort, after_this_request
from modify import *
import os
from dotenv import load_dotenv

#load_dotenv()

app = Flask(__name__)

#os.environ['GOOGLE_API_KEY'] = os.getenv('API_KEY')
#genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

# Directory where resume files are stored
RESUME_DIR = os.path.abspath('resume')

def compile_latex(tex_file):
    tex_dir = os.path.dirname(os.path.abspath(tex_file))
    tex_filename = os.path.basename(tex_file)
    pdf_file = os.path.splitext(tex_file)[0] + '.pdf'
    log_file = os.path.splitext(tex_file)[0] + '.log' # Log file path

    # Ensure the resume directory exists
    os.makedirs(tex_dir, exist_ok=True)

    compilation_success = False
    try:
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', tex_dir, tex_filename],
            cwd=tex_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=30
        )
        print("LaTeX compilation succeeded.")
        compilation_success = True
    except subprocess.CalledProcessError as e:
        print("LaTeX compilation failed.")
        # Log the error output which might be more detailed
        if os.path.exists(log_file):
            with open(log_file, 'r') as lf:
                print("--- LaTeX Log ---")
                print(lf.read())
                print("--- End Log ---")
        else:
             print(e.stdout.decode())
             print(e.stderr.decode())
    except subprocess.TimeoutExpired:
        print("LaTeX compilation timed out.")

    # Check if PDF exists even if compilation reported errors
    if os.path.exists(pdf_file):
        print(f"PDF file found at {pdf_file}")
        return pdf_file
    else:
        print("PDF file not found after compilation attempt.")
        return None

def clean_auxiliary_files(base_path, keep_pdf=False):
    """Cleans auxiliary files for a given base path.
       Optionally keeps the PDF file.
    """
    tex_dir = os.path.dirname(os.path.abspath(base_path))
    base_name = os.path.splitext(os.path.basename(base_path))[0]
    extensions = ['aux', 'log', 'out', 'toc', 'synctex.gz', 'tex', 'cls']
    if not keep_pdf:
        extensions.append('pdf')

    print(f"Cleaning files with base name: {base_name} in {tex_dir}")
    print(f"Extensions to clean: {extensions}")

    for ext in extensions:
        file_path = os.path.join(tex_dir, f"{base_name}.{ext}")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Removed {file_path}")
            except OSError as e:
                print(f"Error removing {file_path}: {e}")

@app.route('/')
def index():
    """Serve the index page."""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_resume():
    """Process the job description and generate the tailored resume PDF."""
    job_description = request.form.get('job_description')
    if not job_description:
        return "Job description is required", 400

    # Define file paths relative to RESUME_DIR
    original_tex_path = os.path.join(RESUME_DIR, 'resume.tex')
    modified_tex_path = os.path.join(RESUME_DIR, 'modified.tex')
    cls_source = os.path.join(RESUME_DIR, 'resume.cls')
    cls_destination = os.path.join(RESUME_DIR, 'modified.cls')
    generated_pdf_path = None

    try:
        # 1. Copy the .cls file
        if os.path.exists(cls_source):
            shutil.copyfile(cls_source, cls_destination)
            print(f"Copied {cls_source} to {cls_destination}")
        else:
            print(f"Error: Source file {cls_source} not found.")
            return f"Server error: {cls_source} not found.", 500

        # 2. Read the original .tex file
        if not os.path.exists(original_tex_path):
             print(f"Error: Source file {original_tex_path} not found.")
             return f"Server error: {original_tex_path} not found.", 500
        with open(original_tex_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # 3. Modify the content with job description
        modified_content = modify(content, job_description)

        # --- Add cleaning for markdown fences ---
        # Remove potential markdown code fences like ```latex ... ```
        modified_content = re.sub(r'^```[a-zA-Z]*\n?', '', modified_content) # Remove leading fence
        modified_content = re.sub(r'\n?```$', '', modified_content) # Remove trailing fence
        modified_content = modified_content.strip() # Remove leading/trailing whitespace
        # --- End cleaning --- 

        # 4. Save the modified content to a new .tex file
        os.makedirs(RESUME_DIR, exist_ok=True)
        with open(modified_tex_path, 'w', encoding='utf-8') as file:
            file.write(modified_content)
        print(f"Modified resume content saved to {modified_tex_path}")

        # 5. Compile the modified LaTeX file
        generated_pdf_path = compile_latex(modified_tex_path)

        if generated_pdf_path and os.path.exists(generated_pdf_path):
            # 6. Send the generated PDF as a download
            @after_this_request
            def cleanup(response):
                print("Running cleanup after request")
                # Clean everything *except* the PDF we just sent
                clean_auxiliary_files(modified_tex_path, keep_pdf=False)
                # Attempt to remove the PDF now if it exists
                if generated_pdf_path and os.path.exists(generated_pdf_path):
                     try:
                         # Wait a moment before deleting to ensure download started
                         import time
                         time.sleep(2)
                         os.remove(generated_pdf_path)
                         print(f"Cleaned up PDF: {generated_pdf_path}")
                     except OSError as e:
                         print(f"Error cleaning up PDF {generated_pdf_path}: {e}")
                return response

            return send_from_directory(directory=RESUME_DIR,
                                       path=os.path.basename(generated_pdf_path),
                                       as_attachment=True)
        else:
            # If PDF generation failed or PDF file not found after attempt
            print("PDF generation failed or PDF file not found.")
            # Clean up all generated files including potential failed PDF
            clean_auxiliary_files(modified_tex_path, keep_pdf=False)
            return "Error generating PDF. Please check the server logs.", 500

    except Exception as e:
        print(f"An error occurred during processing: {e}")
        # Clean up all generated files on any exception
        clean_auxiliary_files(modified_tex_path, keep_pdf=False)
        return f"An internal server error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)