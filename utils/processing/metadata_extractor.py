import re
from datetime import datetime

class MetadataExtractor:
    def __init__(self):
        self.law_types = {
            'contract': 'Contract Law',
            'company': 'Corporate Law', 
            'companies': 'Corporate Law',
            'evidence': 'Evidence Law',
            'constitution': 'Constitutional Law',
            'cyber': 'Cyber Law',
            'information': 'Cyber Law',
            'technology': 'Cyber Law',
            'criminal': 'Criminal Law',
            'civil': 'Civil Law',
            'labor': 'Labor Law',
            'labour': 'Labor Law'
        }
    
    def extract_from_filename(self, filename):
        filename_lower = filename.lower()
        
        # Extract year
        year_match = re.search(r'(\d{4})', filename)
        year = int(year_match.group(1)) if year_match else None
        
        # Guess law type
        law_type = 'General Law'
        for keyword, legal_type in self.law_types.items():
            if keyword in filename_lower:
                law_type = legal_type
                break
        
        return {
            'jurisdiction': 'India',
            'law_type': law_type,
            'year': year,
            'source': filename,
            'extracted_date': datetime.now().isoformat()
        }
    
    def extract_from_content(self, text):
        return {
            'total_sections': len(re.findall(r'Section\s+\d+', text)),
            'total_words': len(text.split()),
            'content_extracted': True
        }