import requests
import xml.etree.ElementTree as ET
import os
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import PyPDF2
import re
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class ArxivDocument:
    """Class for representing arXiv documents"""
    
    def __init__(self, title: str, authors: List[str], abstract: str, 
                 arxiv_id: str, published_date: str, pdf_url: str, 
                 categories: List[str], full_text: str = ""):
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.arxiv_id = arxiv_id
        self.published_date = published_date
        self.pdf_url = pdf_url
        self.categories = categories
        self.full_text = full_text
    
    def __str__(self):
        return f"arXiv:{self.arxiv_id} - {self.title}"
    
    def to_dict(self) -> Dict:
        """Converts document to dictionary for JSON serialization"""
        return {
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'arxiv_id': self.arxiv_id,
            'published_date': self.published_date,
            'pdf_url': self.pdf_url,
            'browser_url': f"https://arxiv.org/abs/{self.arxiv_id}",
            'categories': self.categories,
            'full_text': self.full_text
        }


class ArxivExtractor:
    """Class for extracting documents from arXiv"""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.pdf_base_url = "https://arxiv.org/pdf/"
        self.browser_base_url = "https://arxiv.org/abs/"
        
    def search_documents(self, 
                        topic: str, 
                        max_results: int = 10, 
                        days_back: int = 365,
                        categories: Optional[List[str]] = None) -> List[ArxivDocument]:
        """
        Searches for documents in arXiv by given topic
        
        Args:
            topic: Search topic
            max_results: Maximum number of results
            days_back: Number of days back for search
            categories: List of arXiv categories (e.g., ['cs.AI', 'quant-ph'])
        
        Returns:
            List of ArxivDocument objects
        """
        
        # Form query
        query_params = {
            'search_query': f'all:"{topic}"',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        # Add date filter
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            date_str = cutoff_date.strftime("%Y%m%d")
            query_params['search_query'] += f' AND submittedDate:[{date_str}0000 TO 999912312359]'
        
        # Add category filter
        if categories:
            category_filter = ' OR '.join([f'cat:{cat}' for cat in categories])
            query_params['search_query'] += f' AND ({category_filter})'
        
        try:
            # Execute request to arXiv API
            response = requests.get(self.base_url, params=query_params)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Extract documents
            documents = []
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                doc = self._parse_entry(entry)
                if doc:
                    documents.append(doc)
            
            return documents
            
        except requests.RequestException as e:
            print(f"Error requesting arXiv API: {e}")
            return []
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            return []
    
    def _parse_entry(self, entry) -> Optional[ArxivDocument]:
        """Parses XML entry element into ArxivDocument object"""
        try:
            # Extract basic information
            title = entry.find('.//{http://www.w3.org/2005/Atom}title').text.strip()
            summary = entry.find('.//{http://www.w3.org/2005/Atom}summary').text.strip()
            
            # Extract authors
            authors = []
            for author in entry.findall('.//{http://www.w3.org/2005/Atom}author'):
                name = author.find('.//{http://www.w3.org/2005/Atom}name').text.strip()
                authors.append(name)
            
            # Extract ID and date
            id_elem = entry.find('.//{http://www.w3.org/2005/Atom}id')
            arxiv_id = id_elem.text.split('/')[-1] if id_elem is not None else ""
            
            published = entry.find('.//{http://www.w3.org/2005/Atom}published')
            published_date = published.text[:10] if published is not None else ""
            
            # Extract categories
            categories = []
            for category in entry.findall('.//{http://arxiv.org/schemas/atom}primary_category'):
                cat = category.get('term')
                if cat:
                    categories.append(cat)
            
            # Form URL
            pdf_url = f"{self.pdf_base_url}{arxiv_id}.pdf"
            
            return ArxivDocument(
                title=title,
                authors=authors,
                abstract=summary,
                arxiv_id=arxiv_id,
                published_date=published_date,
                pdf_url=pdf_url,
                categories=categories
            )
            
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None
    
    def download_pdf(self, arxiv_id: str, output_dir: str = "downloads") -> Optional[str]:
        """
        Downloads PDF document by arXiv ID
        
        Args:
            arxiv_id: Document ID in arXiv
            output_dir: Folder for saving
            
        Returns:
            Path to downloaded file or None on error
        """
        try:
            # Create folder if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # URL for downloading PDF
            pdf_url = f"{self.pdf_base_url}{arxiv_id}.pdf"
            
            # Download file
            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()
            
            # Save file
            filename = f"{arxiv_id}.pdf"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"PDF downloaded: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error downloading PDF {arxiv_id}: {e}")
            return None
    
    def get_browser_url(self, arxiv_id: str) -> str:
        """Returns URL for viewing document in browser"""
        return f"{self.browser_base_url}{arxiv_id}"
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extracts full text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            # Use PyPDF2 for text extraction
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return self._clean_text(text)
                    
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """
        Cleans extracted text from extra characters and formatting
        
        Args:
            text: Original text
            
        Returns:
            Cleaned text
        """
        # Remove extra spaces and line breaks
        text = re.sub(r'\s+', ' ', text)
        
        # Remove arXiv special characters
        text = re.sub(r'arXiv:\d+\.\d+', '', text)
        
        # Remove page numbers
        text = re.sub(r'\b\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove repeating characters
        text = re.sub(r'([.!?])\1+', r'\1', text)
        
        # Remove extra spaces at beginning and end
        text = text.strip()
        
        return text
    
    def extract_text_from_pdf_by_id(self, arxiv_id: str, pdf_dir: str = "downloads") -> str:
        """
        Extracts text from PDF by arXiv ID
        
        Args:
            arxiv_id: Document ID in arXiv
            pdf_dir: Folder with PDF files
            
        Returns:
            Extracted text
        """
        pdf_path = os.path.join(pdf_dir, f"{arxiv_id}.pdf")
        
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return ""
        
        return self.extract_text_from_pdf(pdf_path)
    
    def search_and_download(self, 
                           topic: str, 
                           max_results: int = 5,
                           download_pdfs: bool = False,
                           extract_text: bool = False,
                           output_dir: str = "downloads") -> Dict:
        """
        Combined function: search, download PDF and extract text
        
        Args:
            topic: Search topic
            max_results: Maximum number of results
            download_pdfs: Whether to download PDF files
            extract_text: Whether to extract full text from PDF
            output_dir: Folder for saving PDF
            
        Returns:
            Dictionary with search results, downloaded files info and extracted text
        """
        print(f"Searching documents for topic: '{topic}'")
        
        # Search documents
        documents = self.search_documents(topic, max_results)
        
        if not documents:
            print("Documents not found")
            return {"documents": [], "downloaded_files": []}
        
        print(f"Found {len(documents)} documents")
        
        # Download PDF if required
        downloaded_files = []
        if download_pdfs:
            print("Downloading PDF files...")
            for doc in documents:
                filepath = self.download_pdf(doc.arxiv_id, output_dir)
                if filepath:
                    downloaded_files.append({
                        'arxiv_id': doc.arxiv_id,
                        'filepath': filepath,
                        'browser_url': self.get_browser_url(doc.arxiv_id)
                    })
                time.sleep(1)  # Small delay between requests
        
        # Extract text from PDF if required
        if extract_text and download_pdfs:
            print("Extracting full text from PDF...")
            for doc in documents:
                if any(f['arxiv_id'] == doc.arxiv_id for f in downloaded_files):
                    full_text = self.extract_text_from_pdf_by_id(doc.arxiv_id, output_dir)
                    doc.full_text = full_text
                    print(f"Extracted text from {doc.arxiv_id} ({len(full_text)} characters)")
        
        # Form result
        result = {
            "topic": topic,
            "search_date": datetime.now().isoformat(),
            "total_found": len(documents),
            "documents": [],
            "downloaded_files": downloaded_files
        }
        
        # Convert documents to dictionaries and add browser links
        for doc in documents:
            doc_dict = doc.to_dict()
            doc_dict['browser_url'] = self.get_browser_url(doc.arxiv_id)
            result["documents"].append(doc_dict)
        
        return result


# Usage example
if __name__ == "__main__":
    extractor = ArxivExtractor()
    
    # Example search for quantum physics documents
    topic = "quantum computing"
    results = extractor.search_and_download(
        topic=topic,
        max_results=3,
        download_pdfs=True,
        extract_text=True,
        output_dir="quantum_papers"
    )
    
    print(f"\nSearch results for topic '{topic}':")
    for i, doc in enumerate(results["documents"], 1):
        print(f"\n{i}. {doc['title']}")
        print(f"   Authors: {', '.join(doc['authors'])}")
        print(f"   arXiv ID: {doc['arxiv_id']}")
        print(f"   Date: {doc['published_date']}")
        print(f"   PDF: {doc['pdf_url']}")
        print(f"   Browser: {doc['browser_url']}")
        print(f"   Categories: {', '.join(doc['categories'])}")
        print(f"   Abstract: {doc['abstract'][:200]}...")
        if doc.get('full_text'):
            print(f"   Full text: {len(doc['full_text'])} characters")
            print(f"   Text beginning: {doc['full_text'][:300]}...")
    
    if results["downloaded_files"]:
        print(f"\nDownloaded PDF files: {len(results['downloaded_files'])}")
        for file_info in results["downloaded_files"]:
            print(f"  - {file_info['arxiv_id']}: {file_info['filepath']}") 