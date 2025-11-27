from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from transformers import pipeline
from docx import Document
import PyPDF2
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Summarizer model
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# Extract text from PDF
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# Extract text from DOCX
def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def create_section_title(summary):
    # Take first 4–6 words as a pseudo heading
    words = summary.split()
    if len(words) > 5:
        title = " ".join(words[:5])
    else:
        title = "Key Concepts"
    return title.title()


@app.post("/generate-reviewer")
async def generate_reviewer(file: UploadFile = File(...)):
    try:
        # Extract text
        if file.filename.endswith(".pdf"):
            raw_text = extract_text_from_pdf(file.file)
        elif file.filename.endswith(".docx"):
            raw_text = extract_text_from_docx(file.file)
        else:
            return JSONResponse(content={"error": "Only PDF or DOCX files are supported"}, status_code=400)

        cleaned = clean_text(raw_text)

        # Chunk text
        chunk_size = 400
        chunks = [cleaned[i:i+chunk_size] for i in range(0, len(cleaned), chunk_size)]

        # Summaries
        summaries = []
        for chunk in chunks:
            out = summarizer(chunk, max_length=80, min_length=40, do_sample=False)
            summaries.append(out[0]["summary_text"])

        # Build structured HTML reviewer
        html = ""
        for i, summary in enumerate(summaries):
            section_title = create_section_title(summary)

            html += f"<h2 style='margin-top:25px;'>{section_title}</h2>"
            html += "<ul>"

            # Break summary into bullet-friendly chunks
            sentences = re.split(r"\. |\? |\! ", summary)

            for s in sentences:
                s = s.strip()
                if len(s) < 5:
                    continue

                # Bold first key term (first 1–2 words)
                words = s.split()
                if len(words) > 2:
                    bold = " ".join(words[:2])
                    rest = " ".join(words[2:])
                    html += f"<li><b>{bold}</b> {rest}</li>"
                else:
                    html += f"<li>{s}</li>"

            html += "</ul>"

        return {"reviewer": html}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
