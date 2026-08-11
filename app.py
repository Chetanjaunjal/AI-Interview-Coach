import os

from flask import Flask, flash, redirect, render_template, request, url_for
from pypdf import PdfReader
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "development-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")


def extract_text_from_pdf(file_path):
    """Extract readable text from every page in a PDF file."""
    try:
        reader = PdfReader(file_path)

        if reader.is_encrypted:
            return ""
    except Exception:
        return ""

    extracted_pages = []
    for page in reader.pages:
        try:
            page_text = page.extract_text()
        except Exception:
            page_text = ""

        if page_text and page_text.strip():
            extracted_pages.append(page_text.strip())

    return "\n\n".join(extracted_pages)


@app.errorhandler(413)
def file_too_large(error):
    """Show a useful message when Flask rejects an oversized request."""
    flash("The resume is too large. Please choose a PDF smaller than 5 MB.", "error")
    return redirect(url_for("home"))


@app.route("/upload-resume", methods=["POST"])
def upload_resume():
    uploaded_file = request.files.get("resume")

    if uploaded_file is None:
        flash("Please choose a PDF resume before uploading.", "error")
        return redirect(url_for("home"))

    if not uploaded_file.filename:
        flash("Please choose a PDF resume before uploading.", "error")
        return redirect(url_for("home"))

    if not uploaded_file.filename.lower().endswith(".pdf"):
        flash("Only PDF files are allowed.", "error")
        return redirect(url_for("home"))

    safe_filename = secure_filename(uploaded_file.filename)
    if not safe_filename or not safe_filename.lower().endswith(".pdf"):
        flash("That filename is not valid. Please rename the PDF and try again.", "error")
        return redirect(url_for("home"))

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)
    name, extension = os.path.splitext(safe_filename)
    counter = 1
    while os.path.exists(save_path):
        save_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{name}_{counter}{extension}"
        )
        counter += 1

    uploaded_file.save(save_path)
    extracted_text = extract_text_from_pdf(save_path)
    flash("Resume uploaded successfully.", "success")
    return render_template("index.html", extracted_text=extracted_text)


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
