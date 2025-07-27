from pydantic import BaseModel
from typing import List, Optional

class GenerationRequest(BaseModel):
    platform: str
    topic: str

class GenerationResponse(BaseModel):
    content: str

class ArxivSearchRequest(BaseModel):
    topic: str
    max_results: int = 5
    download_pdfs: bool = False
    extract_text: bool = False
    days_back: int = 365
    categories: Optional[List[str]] = None

class ArxivDocumentResponse(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    published_date: str
    pdf_url: str
    browser_url: str
    categories: List[str]
    full_text: Optional[str] = None

class ArxivSearchResponse(BaseModel):
    topic: str
    search_date: str
    total_found: int
    documents: List[ArxivDocumentResponse]
    downloaded_files: List[dict]
