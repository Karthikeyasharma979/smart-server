from flask import Blueprint, jsonify, request
import io
import os

from pypdf import PdfReader
from docx import Document

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

upload_bp = Blueprint("upload", __name__)

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _extract_pdf_text(file_bytes):
    pdf = PdfReader(io.BytesIO(file_bytes))
    return "\n".join((page.extract_text() or "") for page in pdf.pages).strip()


def _extract_docx_text(file_bytes):
    document = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs if p.text).strip()


def _extract_txt_text(file_bytes):
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return file_bytes.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    raise ValueError("Unable to decode text file with supported encodings")


def _extract_text(file_ext, file_bytes):
    if file_ext == "pdf":
        return _extract_pdf_text(file_bytes)
    if file_ext == "docx":
        return _extract_docx_text(file_bytes)
    if file_ext == "txt":
        return _extract_txt_text(file_bytes)
    raise ValueError(f"Unsupported file type: .{file_ext}")

@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Supported: PDF, DOCX, TXT."}), 400

    try:
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        file_bytes = file.read()
        text = _extract_text(file_ext, file_bytes)

        if not text:
            return jsonify({"error": "No readable text found in document."}), 400
        
        return jsonify({
            "message": "✅ File processed successfully!", 
            "file": file.filename, 
            "extracted_text": text
        }), 200

    except Exception as e:
        return jsonify({"error": f"❌ Failed to process file: {str(e)}"}), 500
