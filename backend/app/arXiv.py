import requests
import xml.etree.ElementTree as ET
import os
import time
from typing import List, Dict, Optional
import urllib.parse
from datetime import datetime, timedelta
import PyPDF2
import re


class ArxivDocument:
    """Класс для представления документа из arXiv"""
    
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
        """Преобразует документ в словарь для JSON сериализации"""
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
    """Класс для извлечения документов из arXiv"""
    
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
        Ищет документы в arXiv по заданной теме
        
        Args:
            topic: Тема для поиска
            max_results: Максимальное количество результатов
            days_back: Количество дней назад для поиска
            categories: Список категорий arXiv (например, ['cs.AI', 'quant-ph'])
        
        Returns:
            Список объектов ArxivDocument
        """
        
        # Формируем запрос
        query_params = {
            'search_query': f'all:"{topic}"',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        # Добавляем фильтр по дате
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            date_str = cutoff_date.strftime("%Y%m%d")
            query_params['search_query'] += f' AND submittedDate:[{date_str}0000 TO 999912312359]'
        
        # Добавляем фильтр по категориям
        if categories:
            category_filter = ' OR '.join([f'cat:{cat}' for cat in categories])
            query_params['search_query'] += f' AND ({category_filter})'
        
        try:
            # Выполняем запрос к API arXiv
            response = requests.get(self.base_url, params=query_params)
            response.raise_for_status()
            
            # Парсим XML ответ
            root = ET.fromstring(response.content)
            
            # Извлекаем документы
            documents = []
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                doc = self._parse_entry(entry)
                if doc:
                    documents.append(doc)
            
            return documents
            
        except requests.RequestException as e:
            print(f"Ошибка при запросе к arXiv API: {e}")
            return []
        except ET.ParseError as e:
            print(f"Ошибка при парсинге XML: {e}")
            return []
    
    def _parse_entry(self, entry) -> Optional[ArxivDocument]:
        """Парсит XML элемент entry в объект ArxivDocument"""
        try:
            # Извлекаем основную информацию
            title = entry.find('.//{http://www.w3.org/2005/Atom}title').text.strip()
            summary = entry.find('.//{http://www.w3.org/2005/Atom}summary').text.strip()
            
            # Извлекаем авторов
            authors = []
            for author in entry.findall('.//{http://www.w3.org/2005/Atom}author'):
                name = author.find('.//{http://www.w3.org/2005/Atom}name').text.strip()
                authors.append(name)
            
            # Извлекаем ID и дату
            id_elem = entry.find('.//{http://www.w3.org/2005/Atom}id')
            arxiv_id = id_elem.text.split('/')[-1] if id_elem is not None else ""
            
            published = entry.find('.//{http://www.w3.org/2005/Atom}published')
            published_date = published.text[:10] if published is not None else ""
            
            # Извлекаем категории
            categories = []
            for category in entry.findall('.//{http://arxiv.org/schemas/atom}primary_category'):
                cat = category.get('term')
                if cat:
                    categories.append(cat)
            
            # Формируем URL
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
            print(f"Ошибка при парсинге entry: {e}")
            return None
    
    def download_pdf(self, arxiv_id: str, output_dir: str = "downloads") -> Optional[str]:
        """
        Скачивает PDF документ по arXiv ID
        
        Args:
            arxiv_id: ID документа в arXiv
            output_dir: Папка для сохранения
            
        Returns:
            Путь к скачанному файлу или None при ошибке
        """
        try:
            # Создаем папку если не существует
            os.makedirs(output_dir, exist_ok=True)
            
            # URL для скачивания PDF
            pdf_url = f"{self.pdf_base_url}{arxiv_id}.pdf"
            
            # Скачиваем файл
            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()
            
            # Сохраняем файл
            filename = f"{arxiv_id}.pdf"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"PDF скачан: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Ошибка при скачивании PDF {arxiv_id}: {e}")
            return None
    
    def get_browser_url(self, arxiv_id: str) -> str:
        """Возвращает URL для просмотра документа в браузере"""
        return f"{self.browser_base_url}{arxiv_id}"
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Извлекает полный текст из PDF файла
        
        Args:
            pdf_path: Путь к PDF файлу
            
        Returns:
            Извлеченный текст
        """
        try:
            # Используем PyPDF2 для извлечения текста
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return self._clean_text(text)
                    
        except Exception as e:
            print(f"Ошибка при извлечении текста из PDF {pdf_path}: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """
        Очищает извлеченный текст от лишних символов и форматирования
        
        Args:
            text: Исходный текст
            
        Returns:
            Очищенный текст
        """
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем специальные символы arXiv
        text = re.sub(r'arXiv:\d+\.\d+', '', text)
        
        # Удаляем номера страниц
        text = re.sub(r'\b\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем повторяющиеся символы
        text = re.sub(r'([.!?])\1+', r'\1', text)
        
        # Удаляем лишние пробелы в начале и конце
        text = text.strip()
        
        return text
    
    def extract_text_from_pdf_by_id(self, arxiv_id: str, pdf_dir: str = "downloads") -> str:
        """
        Извлекает текст из PDF по arXiv ID
        
        Args:
            arxiv_id: ID документа в arXiv
            pdf_dir: Папка с PDF файлами
            
        Returns:
            Извлеченный текст
        """
        pdf_path = os.path.join(pdf_dir, f"{arxiv_id}.pdf")
        
        if not os.path.exists(pdf_path):
            print(f"PDF файл не найден: {pdf_path}")
            return ""
        
        return self.extract_text_from_pdf(pdf_path)
    
    def search_and_download(self, 
                           topic: str, 
                           max_results: int = 5,
                           download_pdfs: bool = False,
                           extract_text: bool = False,
                           output_dir: str = "downloads") -> Dict:
        """
        Комбинированная функция: поиск, скачивание PDF и извлечение текста
        
        Args:
            topic: Тема для поиска
            max_results: Максимальное количество результатов
            download_pdfs: Скачивать ли PDF файлы
            extract_text: Извлекать ли полный текст из PDF
            output_dir: Папка для сохранения PDF
            
        Returns:
            Словарь с результатами поиска, информацией о скачанных файлах и извлеченным текстом
        """
        print(f"Ищем документы по теме: '{topic}'")
        
        # Ищем документы
        documents = self.search_documents(topic, max_results)
        
        if not documents:
            print("Документы не найдены")
            return {"documents": [], "downloaded_files": []}
        
        print(f"Найдено {len(documents)} документов")
        
        # Скачиваем PDF если требуется
        downloaded_files = []
        if download_pdfs:
            print("Скачиваем PDF файлы...")
            for doc in documents:
                filepath = self.download_pdf(doc.arxiv_id, output_dir)
                if filepath:
                    downloaded_files.append({
                        'arxiv_id': doc.arxiv_id,
                        'filepath': filepath,
                        'browser_url': self.get_browser_url(doc.arxiv_id)
                    })
                time.sleep(1)  # Небольшая задержка между запросами
        
        # Извлекаем текст из PDF если требуется
        if extract_text and download_pdfs:
            print("Извлекаем полный текст из PDF...")
            for doc in documents:
                if any(f['arxiv_id'] == doc.arxiv_id for f in downloaded_files):
                    full_text = self.extract_text_from_pdf_by_id(doc.arxiv_id, output_dir)
                    doc.full_text = full_text
                    print(f"Извлечен текст из {doc.arxiv_id} ({len(full_text)} символов)")
        
        # Формируем результат
        result = {
            "topic": topic,
            "search_date": datetime.now().isoformat(),
            "total_found": len(documents),
            "documents": [],
            "downloaded_files": downloaded_files
        }
        
        # Преобразуем документы в словари и добавляем браузерные ссылки
        for doc in documents:
            doc_dict = doc.to_dict()
            doc_dict['browser_url'] = self.get_browser_url(doc.arxiv_id)
            result["documents"].append(doc_dict)
        
        return result


# Пример использования
if __name__ == "__main__":
    extractor = ArxivExtractor()
    
    # Пример поиска документов по квантовой физике
    topic = "quantum computing"
    results = extractor.search_and_download(
        topic=topic,
        max_results=3,
        download_pdfs=True,
        extract_text=True,
        output_dir="quantum_papers"
    )
    
    print(f"\nРезультаты поиска по теме '{topic}':")
    for i, doc in enumerate(results["documents"], 1):
        print(f"\n{i}. {doc['title']}")
        print(f"   Авторы: {', '.join(doc['authors'])}")
        print(f"   arXiv ID: {doc['arxiv_id']}")
        print(f"   Дата: {doc['published_date']}")
        print(f"   PDF: {doc['pdf_url']}")
        print(f"   Браузер: {doc['browser_url']}")
        print(f"   Категории: {', '.join(doc['categories'])}")
        print(f"   Аннотация: {doc['abstract'][:200]}...")
        if doc.get('full_text'):
            print(f"   Полный текст: {len(doc['full_text'])} символов")
            print(f"   Начало текста: {doc['full_text'][:300]}...")
    
    if results["downloaded_files"]:
        print(f"\nСкачано PDF файлов: {len(results['downloaded_files'])}")
        for file_info in results["downloaded_files"]:
            print(f"  - {file_info['arxiv_id']}: {file_info['filepath']}") 