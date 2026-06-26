import hashlib
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from quiz.models import QuizAttempt
from resume_analyzer.models import ResumeAnalysis

# ReportLab libraries for PDF building
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

def draw_page_border(canvas, doc):
    """Draws decorative border and flourishes on the PDF page."""
    canvas.saveState()
    # Landscape Letter size is 792 x 612
    width, height = 792, 612
    
    # Draw outer thick navy border
    canvas.setStrokeColor(colors.HexColor('#0f172a'))
    canvas.setLineWidth(6)
    canvas.rect(20, 20, width - 40, height - 40)

    # Draw inner thin gold border
    canvas.setStrokeColor(colors.HexColor('#d97706'))
    canvas.setLineWidth(2)
    canvas.rect(28, 28, width - 56, height - 56)

    # Draw corner flourishes
    canvas.setFillColor(colors.HexColor('#d97706'))
    canvas.rect(24, 24, 12, 12, fill=True, stroke=False)
    canvas.rect(width - 36, 24, 12, 12, fill=True, stroke=False)
    canvas.rect(24, height - 36, 12, 12, fill=True, stroke=False)
    canvas.rect(width - 36, height - 36, 12, 12, fill=True, stroke=False)
    
    canvas.restoreState()

@login_required
def generate_certificate_view(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    
    if attempt.score < 70:
        raise Http404("Certificate is only available for scores of 70% and above.")

    # Get student name from resume analyzer or use standard full name / username
    resume = ResumeAnalysis.objects.filter(user=request.user).first()
    student_name = resume.name if resume and resume.name else (request.user.get_full_name() or request.user.username)

    # Generate verification Hash UUID
    hash_seed = f"{request.user.username}-{attempt.domain}-{attempt.score}-{attempt.id}"
    verification_code = hashlib.sha256(hash_seed.encode()).hexdigest()[:16].upper()
    issue_date = attempt.completed_at.strftime('%B %d, %Y')

    # Setup HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{attempt.id}.pdf"'

    # Create PDF document in landscape mode
    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CertSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=25
    )

    name_style = ParagraphStyle(
        'CertName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#6366f1'), # Indigo accent
        alignment=1,
        spaceAfter=20
    )

    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=22,
        textColor=colors.HexColor('#1e293b'),
        alignment=1,
        spaceAfter=30
    )

    code_style = ParagraphStyle(
        'CertCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9,
        textColor=colors.HexColor('#64748b'),
        alignment=1
    )

    story = []

    # Assemble elements
    story.append(Spacer(1, 40))
    story.append(Paragraph("CERTIFICATE OF COMPLETION", title_style))
    story.append(Paragraph("PROUDLY PRESENTED TO", subtitle_style))
    story.append(Paragraph(student_name.upper(), name_style))
    
    body_text = (
        f"for successfully completing the technical assessment in <b>{attempt.domain}</b><br/>"
        f"with a final evaluated score of <b>{attempt.score}%</b> on this day, <b>{issue_date}</b>."
    )
    story.append(Paragraph(body_text, body_style))

    # Add Signatures Block using table
    sig_style_title = ParagraphStyle(
        'SigTitle',
        fontName='Helvetica-Bold',
        fontSize=11,
        alignment=1,
        textColor=colors.HexColor('#0f172a')
    )
    sig_style_inst = ParagraphStyle(
        'SigInst',
        fontName='Helvetica',
        fontSize=9,
        alignment=1,
        textColor=colors.HexColor('#64748b')
    )

    sig_data = [
        [
            Paragraph("________________________", sig_style_title),
            Paragraph("________________________", sig_style_title)
        ],
        [
            Paragraph("Assessment Director", sig_style_title),
            Paragraph("Academic Lead", sig_style_title)
        ],
        [
            Paragraph("AI Interview Assistant", sig_style_inst),
            Paragraph("AI Evaluation Board", sig_style_inst)
        ]
    ]
    
    sig_table = Table(sig_data, colWidths=[250, 250])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    
    story.append(Spacer(1, 20))
    story.append(sig_table)
    
    story.append(Spacer(1, 35))
    story.append(Paragraph(f"Verification ID: {verification_code} | Secured by AI Verification Services", code_style))

    # Build the document
    doc.build(story, onFirstPage=draw_page_border)
    return response

@login_required
def list_certificates_view(request):
    """Lists eligible attempts from which certificates can be downloaded."""
    attempts = QuizAttempt.objects.filter(user=request.user, score__gte=70).order_by('-completed_at')
    return render(request, 'certificates/list.html', {'attempts': attempts})
