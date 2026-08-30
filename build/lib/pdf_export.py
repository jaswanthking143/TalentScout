"""
pdf_export.py
Generates a PDF report for TalentScout top-ranked candidates using ReportLab.
"""
from typing import List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from models import Candidate

def export_candidates_to_pdf(
    output_path: str,
    role: str,
    ranked: List[Candidate],
    top_n: int,
    total_candidates: int
):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#0A192F'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#8892B0'),
        spaceAfter=15
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11
    )
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor('#64FFDA'),
        leading=11
    )

    story = []

    # Title & Header Summary
    story.append(Paragraph("TalentScout — Candidate Analysis Report", title_style))
    story.append(Paragraph(
        f"Role Analyzed: <b>{role.title()}</b> | Top {top_n} of {total_candidates} candidates",
        subtitle_style
    ))
    story.append(Spacer(1, 10))

    # Table Header
    headers = ["Rank", "Name", "Email / Contact", "Score", "Matched Skills", "Missing Skills"]
    table_data = [[Paragraph(h, header_style) for h in headers]]

    # Table Content
    top_candidates = ranked[:top_n]
    for i, c in enumerate(top_candidates, start=1):
        matched_text = ", ".join(c.matched_skills) if c.matched_skills else "None"
        missing_text = ", ".join(c.missing_skills) if c.missing_skills else "None"
        contact_text = f"{c.email}<br/>{c.phone}"

        row = [
            Paragraph(f"<b>#{i}</b>", cell_style),
            Paragraph(f"<b>{c.name}</b>", cell_style),
            Paragraph(contact_text, cell_style),
            Paragraph(f"<b>{c.match_score}%</b>", cell_style),
            Paragraph(matched_text, cell_style),
            Paragraph(missing_text, cell_style),
        ]
        table_data.append(row)

    col_widths = [35, 100, 130, 45, 115, 115]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A192F')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#64FFDA')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ])

    # Alternate row colors
    for r in range(1, len(table_data)):
        bg_color = colors.HexColor('#E9FBF6') if r == 1 else (colors.HexColor('#F8FAFC') if r % 2 == 0 else colors.white)
        table_style.add('BACKGROUND', (0, r), (-1, r), bg_color)

    table.setStyle(table_style)
    story.append(table)

    doc.build(story)