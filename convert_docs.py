#!/usr/bin/env python
"""
Convert PDF and DOCX files to TXT for fallback compatibility
"""
import os
import sys

def convert_documents():
    """Convert all documents to text format"""
    try:
        from pypdf import PdfReader
        from docx import Document
        
        data_dir = 'data'
        converted = 0
        
        for filename in os.listdir(data_dir):
            filepath = os.path.join(data_dir, filename)
            
            if filename.endswith('.pdf'):
                try:
                    reader = PdfReader(filepath)
                    text = ''
                    for page in reader.pages:
                        text += page.extract_text() + '\n'
                    
                    txt_path = os.path.join(data_dir, filename.replace('.pdf', '.txt'))
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    print(f'✅ Converted {filename} to text')
                    converted += 1
                    
                except Exception as e:
                    print(f'❌ Failed to convert {filename}: {e}')
                    
            elif filename.endswith('.docx'):
                try:
                    doc = Document(filepath)
                    text = ''
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + '\n'
                    
                    txt_path = os.path.join(data_dir, filename.replace('.docx', '.txt'))
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    print(f'✅ Converted {filename} to text')
                    converted += 1
                    
                except Exception as e:
                    print(f'❌ Failed to convert {filename}: {e}')
        
        print(f'\n🎉 Converted {converted} documents to text format')
        return converted > 0
        
    except ImportError as e:
        print(f'❌ Missing required libraries: {e}')
        return False

if __name__ == "__main__":
    convert_documents()
