import re
import os
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PyPDF2 import PdfReader
from docx import Document
import spacy
from spacy.matcher import Matcher
from io import BytesIO

nlp = spacy.load('en_core_web_sm')

app = FastAPI()

def extract_text_from_pdf(file):
    file.seek(0)
    reader = PdfReader(BytesIO(file.read()))
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    file.seek(0)
    doc = Document(BytesIO(file.read()))
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text

def extract_text_from_txt(file):
    file.seek(0)
    text = file.read().decode('utf-8')
    return text

def preprocess_text(text):
    text = text.lower()
    return text

def get_email_addresses(string):
    r = re.compile(r'[\w\.-]+@[\w\.-]+')
    return r.findall(string)

def get_phone_numbers(string):
    r = re.compile(r'(\d{3}[-.\s]??\d{3}[-.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-.\s]??\d{4}|\d{3}[-.\s]??\d{4})')
    phone_numbers = r.findall(string)
    return [re.sub(r'\D', '', num) for num in phone_numbers]

def extract_name(text):
    nlp_text = nlp(text)
    matcher = Matcher(nlp.vocab)
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
    matcher.add('NAME', [pattern])
    matches = matcher(nlp_text)
    for match_id, start, end in matches:
        span = nlp_text[start:end]
        return span.text
    return None

def extract_keywords(text):
    Keywords = ["education", "summary", "accomplishments", "executive profile", "professional profile",
                "personal profile", "work background", "academic profile", "other activities",
                "qualifications", "experience", "interests", "skills", "achievements", "publications",
                "publication", "certifications", "workshops", "projects", "internships", "trainings",
                "hobbies", "overview", "objective", "position of responsibility", "jobs"]

    keyword_positions = []
    for key in Keywords:
        keyword_positions += [(match.start(), match.end(), key) for match in re.finditer(f'\\b{key}\\b', text)]
    keyword_positions.sort()

    content = {}
    for i, (start_idx, end_idx, key) in enumerate(keyword_positions):
        next_start_idx = keyword_positions[i+1][0] if i+1 < len(keyword_positions) else len(text)
        content[key] = text[end_idx:next_start_idx].strip()

    return content

def extract_information_from_text(resume_text):
    resume_text = preprocess_text(resume_text)
    name = extract_name(resume_text)
    email = get_email_addresses(resume_text)
    phone_number = get_phone_numbers(resume_text)
    keywords_content = extract_keywords(resume_text)

    return {
        "name": name,
        "email": email[0] if email else None,
        "phone": phone_number[0] if phone_number else None,
        "keywords": keywords_content
    }

def extract_resume_info(file: UploadFile):
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext == '.pdf':
        resume_text = extract_text_from_pdf(file.file)
    elif file_ext == '.docx':
        resume_text = extract_text_from_docx(file.file)
    elif file_ext == '.txt':
        resume_text = extract_text_from_txt(file.file)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    return resume_text

@app.post("/upload_resume/")
async def upload_resume(file: UploadFile = File(...)):
    try:
        resume_text = extract_resume_info(file)
        extracted_info = extract_information_from_text(resume_text)
        return JSONResponse(content=extracted_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "_main_":
    uvicorn.run("resume_parser_api:app", host="0.0.0.0", port=8000, reload=True)