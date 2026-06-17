import re
import pdfplumber
import PyPDF2
import docx
from io import BytesIO

def extract_text_from_pdf(file_file):
    text = ""
    try:
        # Try pdfplumber first
        with pdfplumber.open(file_file) as pdf:
            for page in pdf.pages:
                text_page = page.extract_text()
                if text_page:
                    text += text_page + "\n"
    except Exception:
        # Fallback to PyPDF2
        try:
            file_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(file_file)
            for page in pdf_reader.pages:
                text_page = page.extract_text()
                if text_page:
                    text += text_page + "\n"
        except Exception as e:
            text = f"Error reading PDF: {str(e)}"
    return text

def extract_text_from_docx(file_file):
    text = ""
    try:
        doc = docx.Document(file_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"
    except Exception as e:
        text = f"Error reading DOCX: {str(e)}"
    return text

def parse_resume_text(text, master_skills):
    parsed_data = {
        'name': None,
        'email': None,
        'phone': None,
        'education': [],
        'certifications': [],
        'skills': []
    }

    # Extract Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        parsed_data['email'] = email_match.group(0)

    # Extract Phone (common patterns including international and spaces)
    phone_match = re.search(r'\+?\d[\d\s()-]{8,14}\d', text)
    if phone_match:
        parsed_data['phone'] = phone_match.group(0).strip()

    # Extract Name Heuristic
    # Look at the first 5 non-empty lines, skip lines with email/phone/websites, choose the first clean line
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines[:5]:
        if parsed_data['email'] and parsed_data['email'] in line:
            continue
        if parsed_data['phone'] and parsed_data['phone'] in line:
            continue
        if any(keyword in line.lower() for keyword in ['curriculum', 'resume', 'cv', 'profile', 'http', 'www', 'portfolio']):
            continue
        # Name should be relatively short
        if 3 <= len(line.split()) <= 4 and re.match(r'^[a-zA-Z\s]+$', line):
            parsed_data['name'] = line
            break
    
    # Fallback to first line if no clean name found
    if not parsed_data['name'] and lines:
        parsed_data['name'] = lines[0][:100]

    # Extract Skills
    text_lower = text.lower()
    for skill in master_skills:
        # Use word boundaries to prevent substring matches (like 'Go' matching in 'Google')
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            parsed_data['skills'].append(skill)

    # Section extraction heuristics for Education & Certifications
    current_section = None
    education_keywords = ['education', 'academic', 'qualification', 'degree', 'schooling', 'university', 'college']
    cert_keywords = ['certification', 'certificates', 'credential', 'certified', 'licensure']

    sections = {
        'education': [],
        'certifications': []
    }

    # Line by line processing to capture sections
    for line in lines:
        line_lower = line.lower()
        
        # Check if line indicates a section change
        if any(kw in line_lower for kw in education_keywords) and len(line) < 30:
            current_section = 'education'
            continue
        elif any(kw in line_lower for kw in cert_keywords) and len(line) < 30:
            current_section = 'certifications'
            continue
        elif len(line) < 30 and any(keyword in line_lower for keyword in ['experience', 'project', 'skills', 'objective', 'summary', 'contact']):
            current_section = None
            continue
        
        # Add content to the active section
        if current_section:
            sections[current_section].append(line)

    parsed_data['education'] = "\n".join(sections['education'][:6]) if sections['education'] else "Not clearly identified"
    parsed_data['certifications'] = "\n".join(sections['certifications'][:6]) if sections['certifications'] else "Not clearly identified"

    return parsed_data
