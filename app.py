from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import os
import uuid
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Initialize FastAPI app
app = FastAPI(
    title="VAULT PDF Generator",
    description="API for generating financial transaction affidavits with green theme",
    version="1.0.0",
)

# Add CORS middleware to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define configuration
API_KEY = os.environ.get("API_KEY", "your-development-api-key")  # Set as environment variable
PDF_STORAGE_DIR = "generated_pdfs"

# Create storage directory if it doesn't exist
os.makedirs(PDF_STORAGE_DIR, exist_ok=True)

# Define VAULT brand colors
VAULT_GREEN = colors.HexColor('#1e8449')  # Dark green for headers
VAULT_LIGHT_GREEN = colors.HexColor('#c8e6c9')  # Light green for backgrounds
VAULT_BLACK = colors.black
VAULT_WHITE = colors.white
VAULT_GRAY = colors.HexColor('#f5f5f5')  # Light gray for alternating rows

# Data model for transaction affidavit request
class AffidavitRequest(BaseModel):
    sender: str
    receiver: str
    amount: float
    currency: str
    date: datetime
    transactionId: str
    notes: Optional[str] = None

# Dependency for API key verification
def verify_api_key(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "")
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return token

# Model for the response
class AffidavitResponse(BaseModel):
    pdfUrl: str
    filename: str

@app.get("/")
def read_root():
    return {"message": "VAULT PDF Generator API is running", "status": "OK"}

@app.post("/generate-affidavit", response_model=AffidavitResponse)
def generate_affidavit(request: AffidavitRequest, api_key: str = Depends(verify_api_key)):
    """
    Generate a PDF affidavit for a cryptocurrency transaction with VAULT branding
    """
    try:
        # Generate a unique filename
        filename = f"VAULT_Affidavit_{request.transactionId}_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(PDF_STORAGE_DIR, filename)
        
        # Create the PDF
        create_affidavit_pdf(filepath, request)
        
        # The URL that the frontend will use to download the PDF
        pdf_url = f"/download-affidavit/{filename}"
        
        return AffidavitResponse(pdfUrl=pdf_url, filename=filename)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.get("/download-affidavit/{filename}")
def download_affidavit(filename: str, api_key: str = Depends(verify_api_key)):
    """
    Download a generated PDF affidavit by filename
    """
    filepath = os.path.join(PDF_STORAGE_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        filepath, 
        media_type="application/pdf", 
        filename=filename
    )

# Custom page template with header and footer
def add_page_elements(canvas, doc):
    """Add header and footer to each page"""
    # Save state
    canvas.saveState()
    
    # Add a green header bar
    canvas.setFillColor(VAULT_GREEN)
    canvas.rect(
        0, 
        doc.height + doc.topMargin - 0.5*inch, 
        doc.width + doc.leftMargin + doc.rightMargin, 
        0.5*inch, 
        fill=True, 
        stroke=False
    )
    
    # Add VAULT logo text to the header
    canvas.setFillColor(VAULT_WHITE)
    canvas.setFont('Helvetica-Bold', 16)
    canvas.drawString(
        doc.leftMargin, 
        doc.height + doc.topMargin - 0.3*inch, 
        "VAULT"
    )
    
    # Draw diagonal VAULT watermark
    canvas.setFont('Helvetica-Bold', 80)
    canvas.setFillColor(VAULT_LIGHT_GREEN)
    canvas.saveState()
    canvas.translate(doc.width/2 + doc.leftMargin, doc.height/2)  
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "VAULT")
    canvas.restoreState()
    
    # Add footer
    canvas.setFillColor(VAULT_GREEN)
    canvas.rect(
        0, 
        doc.bottomMargin - 0.4*inch, 
        doc.width + doc.leftMargin + doc.rightMargin, 
        0.3*inch, 
        fill=True, 
        stroke=False
    )
    
    # Add footer text
    canvas.setFillColor(VAULT_WHITE)
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(
        doc.width/2 + doc.leftMargin,
        doc.bottomMargin - 0.25*inch,
        f"VAULT Financial | Transaction Record | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    # Draw thin green border around the page
    canvas.setStrokeColor(VAULT_GREEN)
    canvas.setLineWidth(0.5)
    canvas.rect(
        doc.leftMargin - 10, 
        doc.bottomMargin - 0.5*inch, 
        doc.width + 20, 
        doc.height + doc.topMargin + 0.5*inch, 
        fill=False, 
        stroke=True
    )
    
    canvas.restoreState()

def create_affidavit_pdf(filepath, data):
    """
    Create a professional-looking PDF affidavit with green theme for the VAULT platform
    """
    # Create a PDF document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=90,  # Increased top margin for header
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'VaultTitle',
        parent=styles['Heading1'],
        textColor=VAULT_GREEN,
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    # Subtitle style
    subtitle_style = ParagraphStyle(
        'VaultSubtitle',
        parent=styles['Heading2'],
        textColor=VAULT_BLACK,
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    # Normal style
    normal_style = ParagraphStyle(
        'VaultNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Create content elements
    elements = []
    
    # Add title
    elements.append(Spacer(1, 0.25 * inch))  # Space for header
    elements.append(Paragraph("TRANSACTION AFFIDAVIT", title_style))
    elements.append(Spacer(1, 0.25 * inch))
    
    # Add introduction text
    elements.append(Paragraph(
        "This document certifies that a transaction has been securely recorded on the "
        "VAULT Financial platform with the following details:",
        normal_style
    ))
    elements.append(Spacer(1, 0.25 * inch))
    
    # Format transaction date
    transaction_date = data.date.strftime("%B %d, %Y at %H:%M:%S UTC")
    
    # Transaction details table
    transaction_data = [
        ["Transaction ID", f"#{data.transactionId}"],
        ["Date", transaction_date],
        ["Sender", data.sender],
        ["Receiver", data.receiver],
        ["Amount", f"{data.amount} {data.currency}"],
    ]
    
    if data.notes:
        transaction_data.append(["Notes", data.notes])
    
    # Create the table with the transaction data
    transaction_table = Table(transaction_data, colWidths=[2 * inch, 3.5 * inch])
    transaction_table.setStyle(TableStyle([
        # Headers (left column)
        ('BACKGROUND', (0, 0), (0, -1), VAULT_GREEN),
        ('TEXTCOLOR', (0, 0), (0, -1), VAULT_WHITE),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        
        # Data cells (right column)
        ('BACKGROUND', (1, 0), (1, -1), VAULT_WHITE),
        ('TEXTCOLOR', (1, 0), (1, -1), VAULT_BLACK),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, VAULT_GREEN),
        ('BOX', (0, 0), (-1, -1), 1, VAULT_GREEN),
    ]))
    
    elements.append(transaction_table)
    elements.append(Spacer(1, 0.4 * inch))
    
    # Certification statement
    elements.append(Paragraph(
        "This affidavit certifies that the above transaction has been securely recorded in the VAULT "
        "system. This document serves as an official record of the transaction.",
        normal_style
    ))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Digital verification statement
    elements.append(Paragraph(
        f"Digitally verified and generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}.",
        normal_style
    ))
    
    # Add verification box
    verification_data = [
        ["Verification Status:", "VERIFIED"],
        ["Security Hash:", f"{uuid.uuid4().hex[:12].upper()}"],
        ["Platform:", "VAULT Financial"],
    ]
    
    verification_table = Table(verification_data, colWidths=[2 * inch, 3.5 * inch])
    verification_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (0, -1), VAULT_LIGHT_GREEN),
        ('TEXTCOLOR', (0, 0), (0, -1), VAULT_BLACK),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        
        # Data styling
        ('BACKGROUND', (1, 0), (1, -1), VAULT_WHITE),
        ('TEXTCOLOR', (1, 0), (1, 0), VAULT_GREEN),  # "VERIFIED" in green
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        
        # Border
        ('BOX', (0, 0), (-1, -1), 0.5, VAULT_GREEN),
        ('GRID', (0, 0), (-1, -1), 0.5, VAULT_LIGHT_GREEN),
    ]))
    
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(verification_table)
    
    # Build the PDF with our custom header/footer
    doc.build(elements, onFirstPage=add_page_elements, onLaterPages=add_page_elements)