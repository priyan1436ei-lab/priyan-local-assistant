"""Offline document extraction and multilingual keyword retrieval."""
import io
import math
from pathlib import Path
import re
import unicodedata
import zipfile
from xml.etree import ElementTree

TEXT_TYPES = {'.txt','.md','.csv','.json','.py','.js','.ts','.tsx','.html','.css','.log','.yaml','.yml','.sql','.java','.c','.cpp'}
MAX_BYTES = 5 * 1024 * 1024
MAX_CHARS = 400000

def extract(name, raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('Documents must be 5 MB or smaller')
    ext = Path(name).suffix.lower()
    if ext in TEXT_TYPES:
        text = raw.decode('utf-8-sig')
    elif ext == '.docx':
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            info = z.getinfo('word/document.xml')
            if info.file_size > 8 * 1024 * 1024:
                raise ValueError('DOCX text is too large')
            root = ElementTree.fromstring(z.read(info))
            ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            text = '\n'.join(''.join(p.itertext()) for p in root.findall('.//w:p',ns))
    elif ext == '.pdf':
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise ValueError('PDF support needs: python -m pip install -r requirements-documents.txt') from e
        reader = PdfReader(io.BytesIO(raw))
        if reader.is_encrypted:
            raise ValueError('Unlock this PDF before importing it')
        if len(reader.pages) > 250:
            raise ValueError('Import up to 250 pages at once')
        parts=[]
        size=0
        for n, page in enumerate(reader.pages):
            text_part = f'\n[Page {n+1}]\n' + (page.extract_text() or '')
            parts.append(text_part)
            size += len(text_part)
            if size > MAX_CHARS:
                break
        text='\n'.join(parts)
        if len(re.sub(r'\[Page \d+\]|\s','',text)) < 20:
            raise ValueError('No readable text found. Scanned PDFs need OCR outside this application.')
    else:
        raise ValueError('Supported: text/code, Markdown, CSV, JSON, DOCX and text-based PDF')
    if not text.strip():
        raise ValueError('Document is empty')
    if len(text) > MAX_CHARS:
        raise ValueError('Extracted text exceeds 400000 characters. Split the document first.')
    return text

def chunks(text, length=1200, overlap=180):
    return [text[i:i+length] for i in range(0,len(text),length-overlap)]

def terms(text):
    text=unicodedata.normalize('NFC',text).lower()
    return set(t for t in re.split(r'[\s.,!?;:()\[\]{}"<>/\\=+|]+', text) if len(t)>1)

def search(store, query, limit=5):
    tokens=terms(query)
    if not tokens:
        return []
    candidates=[]
    for doc in store.list('document'):
        for i, part in enumerate(doc['chunks']):
            low=unicodedata.normalize('NFC',part).lower()
            matched=[t for t in tokens if t in low]
            if matched:
                score=sum(1+math.log(1+low.count(t)) for t in matched)/math.sqrt(max(1,len(part)/1200))
                candidates.append((score,doc,i,part))
    candidates.sort(key=lambda x:x[0], reverse=True)
    return [dict(label=f'D{n+1}', document_id=d['id'], name=d['name'], chunk=i+1, text=p, score=round(s,3))
            for n,(s,d,i,p) in enumerate(candidates[:limit])]
