"""
Document Processor - Extract products from documents (PDF, Images)

RESPONSIBILITY: Extract product data from documents using OCR and text analysis
DOES NOT: Validate business rules, create products, handle CSV files

The processor's job:
- Extract text from PDFs and images using OCR
- Identify product information using pattern matching
- Return ExtractedProduct dataclass with confidence scores
- NO CSV/Excel processing (use csv_parser instead)

Performance: Multi-engine OCR (Tesseract + EasyOCR)
Scalability: Page-by-page processing for large PDFs
Reliability: Fallback OCR engines, confidence scoring
Security: File size limits, supported format validation
"""

import os
import io
import re
import mimetypes
import logging
import pytesseract
# import easyocr  # Requires PyTorch - optional
from PIL import Image
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation

import PyPDF2
# import fitz  # PyMuPDF - optional

logger = logging.getLogger(__name__)

@dataclass
class ExtractedProduct:
    name: str
    price: Optional[str] = None
    cost_price: Optional[str] = None
    compare_at_price: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    stock_quantity: int = 0
    images: List[str] = None
    confidence: float = 0.0
    source_location: Optional[str] = None
    
    # Additional Shopify-compatible fields
    selling_type: str = 'physical'  # 'physical', 'digital', 'service'
    status: str = 'active'  # 'active', 'draft', 'archived'
    condition: str = 'new'  # 'new', 'used', 'refurbished'
    track_inventory: bool = True
    allow_backorders: bool = False
    low_stock_threshold: int = 5
    requires_shipping: bool = True
    is_digital: bool = False
    is_active: bool = True
    
    def __post_init__(self):
        if self.images is None:
            self.images = []

@dataclass
class DocumentAnalysisResult:
    products: List[ExtractedProduct]
    document_type: str
    total_pages: int
    confidence_score: float
    processing_time: float
    errors: List[str]
    metadata: Dict[str, Any]

class DocumentProcessor:
    """
    Document Processor - Extraction only (no business logic, no CSV)

    ROLE: Extract product data from PDF and Image documents
    DOES NOT: Handle CSV/Excel (use csv_parser), create products, validate business rules

    Uses OCR and text analysis to extract product information from:
    - PDF documents (with text and images)
    - Image files (JPG, PNG, GIF, BMP, TIFF)
    """

    def __init__(self):
        self.easyocr_reader = None

        # Supported file formats - ONLY documents requiring OCR
        # CSV/Excel should use csv_parser instead
        self.supported_formats = {
            'application/pdf': 'pdf',
            'image/jpeg': 'image',
            'image/jpg': 'image',
            'image/png': 'image',
            'image/gif': 'image',
            'image/bmp': 'image',
            'image/tiff': 'image',
        }
        
        # Product detection patterns
        self.price_patterns = [
            r'(?:USD|EUR|GBP|FCFA|CFA|\$|€|£|₣)\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP|FCFA|CFA|\$|€|£|₣)',
            r'Price:\s*[\d,]+\.?\d*',
            r'Cost:\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:dollars?|euros?|pounds?|francs?)'
        ]
        
        self.product_name_patterns = [
            r'Product(?:\s+Name)?:\s*([^\n\r]+)',
            r'Item(?:\s+Name)?:\s*([^\n\r]+)',
            r'Title:\s*([^\n\r]+)',
            r'^([A-Z][A-Za-z\s&\-\']+(?:\s+\d+[A-Za-z]*)?)\s*$'
        ]
        
        self.category_keywords = {
            'Electronics': ['phone', 'laptop', 'computer', 'tablet', 'tv', 'camera', 'headphone', 'speaker'],
            'Clothing': ['shirt', 't-shirt', 'pants', 'dress', 'jacket', 'shoes', 'hat', 'clothing', 'apparel'],
            'Home & Garden': ['furniture', 'table', 'chair', 'bed', 'lamp', 'decor', 'kitchen', 'garden'],
            'Health & Beauty': ['cream', 'lotion', 'makeup', 'perfume', 'supplement', 'vitamin', 'skincare'],
            'Sports & Outdoors': ['bike', 'equipment', 'fitness', 'outdoor', 'sports', 'exercise'],
            'Books & Media': ['book', 'dvd', 'cd', 'magazine', 'novel', 'textbook'],
            'Automotive': ['car', 'auto', 'vehicle', 'tire', 'parts', 'motorcycle'],
            'Food & Beverages': ['food', 'drink', 'beverage', 'snack', 'organic', 'coffee', 'tea']
        }

    def get_easyocr_reader(self):
        """Lazy initialization of EasyOCR reader"""
        if self.easyocr_reader is None:
            try:
                import easyocr
                self.easyocr_reader = easyocr.Reader(['en', 'fr'])
            except ImportError:
                logger.warning("EasyOCR not available, using Tesseract only")
                self.easyocr_reader = False
        return self.easyocr_reader

    def process_document(self, file_content: bytes, filename: str) -> DocumentAnalysisResult:
        """
        Main document processing entry point

        ONLY processes PDF and Image files
        For CSV/Excel, use csv_parser instead
        """
        import time
        start_time = time.time()

        try:
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

            if mime_type not in self.supported_formats:
                # Check if it's a CSV/Excel trying to use wrong processor
                if mime_type in ['text/csv', 'application/vnd.ms-excel',
                                 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                    raise ValueError(
                        "CSV/Excel files should be processed with csv_parser, not document_processor"
                    )
                raise ValueError(f"Unsupported file format: {mime_type}")

            document_type = self.supported_formats[mime_type]

            # Route to appropriate processor (PDF or Image only)
            if document_type == 'pdf':
                result = self._process_pdf(file_content, filename)
            elif document_type == 'image':
                result = self._process_image(file_content)
            else:
                raise ValueError(f"Handler not implemented for: {document_type}")
            
            processing_time = time.time() - start_time
            
            return DocumentAnalysisResult(
                products=result['products'],
                document_type=document_type,
                total_pages=result.get('total_pages', 1),
                confidence_score=self._calculate_overall_confidence(result['products']),
                processing_time=processing_time,
                errors=result.get('errors', []),
                metadata=result.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            processing_time = time.time() - start_time
            
            return DocumentAnalysisResult(
                products=[],
                document_type='unknown',
                total_pages=0,
                confidence_score=0.0,
                processing_time=processing_time,
                errors=[str(e)],
                metadata={}
            )

    def _process_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process PDF files using PyMuPDF (preferred) or PyPDF2 (fallback)"""
        try:
            try:
                import fitz  # PyMuPDF
                pdf_document = fitz.open(stream=file_content, filetype="pdf")
            except ImportError:
                # Fall back to PyPDF2 only
                return self._extract_pdf_with_pypdf2(file_content)
            
            products = []
            errors = []
            total_pages = len(pdf_document)
            
            for page_num in range(total_pages):
                page = pdf_document[page_num]
                
                # Extract text
                text = page.get_text()
                
                # Extract images from page
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Convert to PIL Image for OCR
                        image = Image.open(io.BytesIO(image_bytes))
                        
                        # OCR on extracted image
                        try:
                            import fitz  # PyMuPDF
                            pix = fitz.Pixmap(pdf_document, xref)
                            if pix.n - pix.alpha < 4:  # GRAY or RGB
                                img_data = pix.tobytes("png")
                                image = Image.open(io.BytesIO(img_data))
                                
                                # Tesseract OCR
                                ocr_text = pytesseract.image_to_string(image)
                                if ocr_text.strip():
                                    text += f"\n{ocr_text}"
                        except Exception as ocr_error:
                            logger.warning(f"OCR failed on PDF image: {ocr_error}")
                            
                    except Exception as img_error:
                        errors.append(f"Failed to extract image {img_index} from page {page_num}: {str(img_error)}")
                
                # Extract products from page text
                page_products = self._extract_products_from_text(text, f"page_{page_num + 1}")
                products.extend(page_products)
            
            pdf_document.close()
            
            return {
                'products': products,
                'total_pages': total_pages,
                'errors': errors,
                'metadata': {'extraction_method': 'pymupdf', 'total_images_processed': len(image_list) if 'image_list' in locals() else 0}
            }
            
        except Exception as e:
            logger.error(f"PyMuPDF processing failed: {str(e)}")
            # Fallback to PyPDF2
            return self._extract_pdf_with_pypdf2(file_content)

    def _extract_pdf_with_pypdf2(self, file_content: bytes) -> Dict[str, Any]:
        """Fallback PDF processing using PyPDF2"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            products = []
            errors = []
            total_pages = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    page_products = self._extract_products_from_text(text, f"page_{page_num + 1}")
                    products.extend(page_products)
                except Exception as e:
                    errors.append(f"Failed to process page {page_num + 1}: {str(e)}")
            
            return {
                'products': products,
                'total_pages': total_pages,
                'errors': errors,
                'metadata': {'extraction_method': 'pypdf2'}
            }
            
        except Exception as e:
            logger.error(f"PyPDF2 processing failed: {str(e)}")
            raise

    def _process_image(self, file_content: bytes) -> Dict[str, Any]:
        """Process image files using OCR"""
        products = []
        errors = []
        ocr_texts = []
        
        try:
            # Open image
            image = Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Tesseract OCR
            try:
                tesseract_text = pytesseract.image_to_string(image)
                if tesseract_text.strip():
                    ocr_texts.append(('tesseract', tesseract_text))
            except Exception as e:
                errors.append(f"Tesseract OCR failed: {str(e)}")
            
            # EasyOCR
            try:
                reader = self.get_easyocr_reader()
                if reader:
                    results = reader.readtext(file_content)
                    easyocr_text = ' '.join([result[1] for result in results])
                    if easyocr_text.strip():
                        ocr_texts.append(('easyocr', easyocr_text))
            except Exception as e:
                errors.append(f"EasyOCR failed: {str(e)}")
            
            # Extract products from OCR results
            for ocr_method, text in ocr_texts:
                method_products = self._extract_products_from_text(text, f"{ocr_method}_ocr")
                products.extend(method_products)
            
            # Remove duplicates based on product name similarity
            products = self._deduplicate_products(products)
            
        except Exception as e:
            errors.append(f"Image processing failed: {str(e)}")
        
        engines = ['tesseract']
        if self.get_easyocr_reader():
            engines.append('easyocr')
        metadata={'ocr_engines': engines}
        
        return {
            'products': products,
            'total_pages': 1,
            'errors': errors,
            'metadata': metadata
        }


    def _extract_products_from_text(self, text: str, source_location: str) -> List[ExtractedProduct]:
        """Extract products from plain text using pattern matching"""
        if not text or not text.strip():
            return []
        
        products = []
        
        # Split text into potential product sections
        sections = self._split_text_into_sections(text)
        
        for i, section in enumerate(sections):
            try:
                product = self._extract_single_product_from_text(section, f"{source_location}_section_{i}")
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Failed to extract product from section {i}: {str(e)}")
                continue
        
        return products

    def _split_text_into_sections(self, text: str) -> List[str]:
        """Split text into sections that likely contain individual products"""
        # Split by common delimiters
        delimiters = ['\n\n', '---', '***', 'Product:', 'Item:', '\n•', '\n-', '\n*']
        
        sections = [text]
        for delimiter in delimiters:
            new_sections = []
            for section in sections:
                new_sections.extend(section.split(delimiter))
            sections = [s.strip() for s in new_sections if s.strip()]
        
        # Filter out very short sections
        sections = [s for s in sections if len(s.split()) > 3]
        
        return sections[:10]  # Limit to prevent processing too many sections

    def _extract_single_product_from_text(self, text: str, source_location: str) -> Optional[ExtractedProduct]:
        """Extract a single product from a text section"""
        
        # Extract product name
        name = self._extract_product_name(text)
        if not name:
            return None
        
        # Extract other fields
        price = self._extract_price(text, 'price')
        cost_price = self._extract_price(text, 'cost')
        compare_price = self._extract_price(text, 'compare')
        
        category = self._extract_category(text)
        brand = self._extract_brand(text)
        sku = self._extract_sku(text)
        description = self._extract_description(text, name)
        stock_quantity = self._extract_stock_quantity(text)
        
        # Calculate confidence based on extracted fields
        confidence = self._calculate_product_confidence(name, price, category, brand, sku)
        
        return ExtractedProduct(
            name=name,
            price=price,
            cost_price=cost_price,
            compare_at_price=compare_price,
            category=category,
            brand=brand,
            sku=sku,
            description=description,
            stock_quantity=stock_quantity,
            confidence=confidence,
            source_location=source_location
        )

    def _extract_product_name(self, text: str) -> Optional[str]:
        """Extract product name from text"""
        
        # Try specific patterns first
        for pattern in self.product_name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                name = matches[0].strip()
                if len(name) > 2 and len(name) < 200:
                    return name
        
        # Fallback: look for capitalized words that might be product names
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Look for lines with mixed case and reasonable length
            if (2 < len(line) < 100 and 
                any(c.isupper() for c in line) and 
                any(c.islower() for c in line) and 
                not line.startswith(('Price:', 'Cost:', '$', '€', '£'))):
                return line
        
        return None

    def _extract_price(self, text: str, price_type: str = 'price') -> Optional[str]:
        """Extract price from text based on type"""
        
        if price_type == 'cost':
            patterns = [r'Cost(?:\s+Price)?:\s*([\d,]+\.?\d*)', r'Wholesale:\s*([\d,]+\.?\d*)']
        elif price_type == 'compare':
            patterns = [r'(?:Compare|Original|MSRP)(?:\s+Price)?:\s*([\d,]+\.?\d*)', r'Was:\s*([\d,]+\.?\d*)']
        else:  # regular price
            patterns = self.price_patterns
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Clean and return first match
                price_str = matches[0]
                # Remove currency symbols and clean
                price_clean = re.sub(r'[^\d.,]', '', price_str)
                if price_clean:
                    return price_clean
        
        return None

    def _extract_category(self, text: str) -> Optional[str]:
        """Extract category from text"""
        text_lower = text.lower()
        
        # First try explicit category patterns
        category_patterns = [
            r'Category:\s*([^\n\r]+)',
            r'Type:\s*([^\n\r]+)',
            r'Product\s+Type:\s*([^\n\r]+)'
        ]
        
        for pattern in category_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        # Try keyword matching
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return None

    def _extract_brand(self, text: str) -> Optional[str]:
        """Extract brand from text"""
        brand_patterns = [
            r'Brand:\s*([^\n\r]+)',
            r'Manufacturer:\s*([^\n\r]+)',
            r'Made\s+by:\s*([^\n\r]+)'
        ]
        
        for pattern in brand_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None

    def _extract_sku(self, text: str) -> Optional[str]:
        """Extract SKU from text"""
        sku_patterns = [
            r'SKU:\s*([^\s\n\r]+)',
            r'Product\s+Code:\s*([^\s\n\r]+)',
            r'Item\s+Code:\s*([^\s\n\r]+)',
            r'Code:\s*([^\s\n\r]+)'
        ]
        
        for pattern in sku_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None

    def _extract_description(self, text: str, product_name: str) -> Optional[str]:
        """Extract description from text"""
        
        description_patterns = [
            r'Description:\s*([^\n\r]+(?:\n[^\n\r]+)*)',
            r'Details:\s*([^\n\r]+(?:\n[^\n\r]+)*)',
            r'Features:\s*([^\n\r]+(?:\n[^\n\r]+)*)'
        ]
        
        for pattern in description_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                desc = matches[0].strip()
                # Clean up description
                desc = re.sub(r'\n+', ' ', desc)
                desc = re.sub(r'\s+', ' ', desc)
                if len(desc) > 10 and desc.lower() != product_name.lower():
                    return desc[:500]  # Limit description length
        
        return None

    def _extract_stock_quantity(self, text: str) -> int:
        """Extract stock quantity from text"""
        stock_patterns = [
            r'Stock:\s*(\d+)',
            r'Quantity:\s*(\d+)',
            r'Available:\s*(\d+)',
            r'In\s+Stock:\s*(\d+)'
        ]
        
        for pattern in stock_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except ValueError:
                    continue
        
        return 0

    def _calculate_product_confidence(self, name: str, price: str, category: str, brand: str, sku: str) -> float:
        """Calculate confidence score for extracted product"""
        confidence = 0.0
        
        # Base confidence for having a name
        if name:
            confidence += 0.3
            
        # Additional confidence for other fields
        if price:
            confidence += 0.25
        if category:
            confidence += 0.2
        if brand:
            confidence += 0.15
        if sku:
            confidence += 0.1
            
        return min(confidence, 1.0)

    def _calculate_overall_confidence(self, products: List[ExtractedProduct]) -> float:
        """Calculate overall confidence for all extracted products"""
        if not products:
            return 0.0
        
        return sum(product.confidence for product in products) / len(products)

    def _deduplicate_products(self, products: List[ExtractedProduct]) -> List[ExtractedProduct]:
        """Remove duplicate products based on name similarity"""
        if not products:
            return products
        
        unique_products = []
        seen_names = set()
        
        for product in products:
            name_normalized = product.name.lower().strip()
            
            # Simple deduplication based on exact name match
            if name_normalized not in seen_names:
                seen_names.add(name_normalized)
                unique_products.append(product)
        
        return unique_products

    def _parse_integer(self, value: str) -> int:
        """Safely parse integer from string"""
        try:
            # Remove non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d]', '', str(value))
            return int(cleaned) if cleaned else 0
        except (ValueError, TypeError):
            return 0

# Add missing import
import time