<<<<<<< HEAD
import os
import io
from reportlab.platypus import Image, Table as PlatypusTable

def _institution_header(elements, styles, subtitle_line):
    snr_path = os.path.join(os.getcwd(), 'static', 'images', 'snr.png')
    logo_path = os.path.join(os.getcwd(), 'static', 'images', 'logo.png')
    snr_img = Image(logo_path, width=80, height=80) if os.path.exists(logo_path) else Paragraph('SNR', styles['Normal'])
    logo_img = Image(snr_path, width=80, height=80) if os.path.exists(snr_path) else Paragraph('LOGO', styles['Normal'])
    header_html = ("<para align='center'><b>SRI RAMAKRISHNA ENGINEERING COLLEGE</b><br/>"
                   "<font size=9>[Educational Service: SNR Sons Charitable Trust]<br/>"
                   "[Autonomous Institution, Reaccredited by NAAC with 'A+' Grade]<br/>"
                   "[Approved by AICTE and Permanently Affiliated to Anna University, Chennai]<br/>"
                   "[ISO 9001:2015 Certified and all eligible programmes Accredited by NBA]<br/>"
                   "VATTAMALAI PALAYAM, N.G.G.O. COLONY POST, COIMBATORE – 641 022.<br/><br/><b>" + subtitle_line + "</b></font></para>")
    tbl = PlatypusTable([[snr_img, Paragraph(header_html, styles['Normal']), logo_img]], colWidths=[90, 380, 90])
    tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 0.2*inch))

def generate_summary_pdf(category, summary):
    """Generate AI summary PDF with institutional header."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']

    _institution_header(elements, styles, "AI FEEDBACK SUMMARY")
    elements.append(Paragraph("AI Feedback Summary", title_style))
    elements.append(Spacer(1, 0.25*inch))
    elements.append(Paragraph(f"Category: {category}", subtitle_style))
    elements.append(Spacer(1, 0.25*inch))

    positive, negative, suggestions = extract_feedback_sections(summary)

    elements.append(Paragraph("Positive Feedback Summary", subtitle_style))
    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph(positive or "No positive feedback detected.", normal_style))
    elements.append(Spacer(1, 0.25*inch))

    elements.append(Paragraph("Negative Feedback Summary", subtitle_style))
    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph(negative or "No negative feedback detected.", normal_style))
    elements.append(Spacer(1, 0.25*inch))

    elements.append(Paragraph("Suggestions", subtitle_style))
    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph(suggestions or "No suggestions detected.", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    doc.build(elements)
    buffer.seek(0)
    return buffer

def extract_feedback_sections(summary):
    """
    Extract positive, negative, and suggestions from the AI summary text.
    This is a simple heuristic based on keywords and sentence splitting.
    """
    import re
    positive = []
    negative = []
    suggestions = []
    # Expanded keyword lists
    positive_kw = [
        'good','great','excellent','appreciate','appreciated','well','positive','improved','improvement','liked',
        'enjoy','enjoyed','satisfactory','best','helpful','supportive','clean','neat','fast','friendly','effective',
        'clear','clarity','organized','efficient','engaging','useful','valuable','strong'
    ]
    negative_kw = [
        'concern','issue','problem','lack','insufficient','overpriced','small','persist','bad','poor','negative',
        'complain','complaint','criticize','limited','long waiting','not satisfied','slow','dirty','confusing',
        'late','delay','delayed','missing','unavailable','difficult','hard','inadequate'
    ]
    suggestion_kw = [
        'improve','consider','suggest','recommend','address','implement','review','adjust','should','could','need',
        'needs','required','must','better','add','increase','decrease','reduce','enhance','provide','ensure'
    ]
    sentences = [s for s in re.split(r'(?<=[.!?])\s+', summary.strip()) if s]
    scored_positive_candidates = []
    for sent in sentences:
        s_lower = sent.lower()
        is_suggestion = any(k in s_lower for k in suggestion_kw)
        is_negative = any(k in s_lower for k in negative_kw)
        is_positive = any(k in s_lower for k in positive_kw) and not is_negative  # positive only if not clearly negative
        if is_suggestion:
            suggestions.append(sent)
        if is_negative:
            negative.append(sent)
        if is_positive:
            positive.append(sent)
        # Keep score for fallback if no explicit positives
        score = sum(s_lower.count(k) for k in positive_kw) - sum(s_lower.count(k) for k in negative_kw)
        if score > 0:
            scored_positive_candidates.append((score, sent))
    if not positive and scored_positive_candidates:
        # pick top scoring one or two sentences
        scored_positive_candidates.sort(reverse=True, key=lambda x: x[0])
        positive = [sp[1] for sp in scored_positive_candidates[:2]]
    return (" ".join(positive).strip(), " ".join(negative).strip(), " ".join(suggestions).strip())
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import inch
from myextensions import db
from models import Staff, Course, Event, Question, FeedbackResponse, QuestionResponse, Student
from datetime import datetime

# Matplotlib for advanced chart resembling provided example
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-GUI backend
    import matplotlib.pyplot as plt
    import numpy as np
    _MATPLOTLIB_AVAILABLE = True
except Exception:
    _MATPLOTLIB_AVAILABLE = False

def generate_excel_grouped_bar_chart(question_labels, totals, c4, c3, c2, c1, pct_34, width_in=6.8, height_in=2.8, dpi=300):
    """
    Generate an Excel-style grouped bar chart as a high-resolution PNG (BytesIO).
    """
    if not _MATPLOTLIB_AVAILABLE:
        return None

    labels = question_labels or []
    n = len(labels)
    x = np.arange(n)

    fig, ax = plt.subplots(figsize=(width_in, height_in))

    # Excel default theme-like colors (Office theme)
    colors_excel = {
        "total": "#4472C4",  # blue
        "r4": "#70AD47",     # green
        "r3": "#FFC000",     # yellow
        "r2": "#A5A5A5",     # gray
        "r1": "#ED7D31",     # orange
    }

    bar_width = 0.12
    offsets = np.array([-2, -1, 0, 1, 2]) * bar_width

    ax.bar(x + offsets[0], totals, bar_width, label='Total number of students', color=colors_excel["total"])
    ax.bar(x + offsets[1], c4, bar_width, label='Rating 4', color=colors_excel["r4"])
    ax.bar(x + offsets[2], c3, bar_width, label='Rating 3', color=colors_excel["r3"])
    ax.bar(x + offsets[3], c2, bar_width, label='Rating 2', color=colors_excel["r2"])
    ax.bar(x + offsets[4], c1, bar_width, label='Rating 1', color=colors_excel["r1"])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel('Number of Students', fontsize=8)

    max_vals = [max(vals) if vals else 0 for vals in zip(totals, c4, c3, c2, c1)]
    y_max = max(max_vals + [1])
    ax.set_ylim(0, y_max * 1.25)

    # Percentage labels above each group (centered)
    for i, p in enumerate(pct_34):
        ax.text(x[i], max_vals[i] + (y_max * 0.05), f"{p:.1f}%", ha='center', va='bottom', fontsize=8)

    ax.legend(fontsize=7, ncol=3, loc='upper center', bbox_to_anchor=(0.5, 1.18))
    ax.grid(axis='y', linestyle='--', linewidth=0.4, alpha=0.5)
    ax.tick_params(axis='y', labelsize=8)

    fig.tight_layout()
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    img_buffer.seek(0)
    return img_buffer

def generate_pdf_report(staff_id, event_id):
    """
    Generate a PDF report for a specific staff and event.
    Returns: BytesIO object containing the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']

    staff = Staff.query.get_or_404(staff_id)
    event = Event.query.get_or_404(event_id)
    course = Course.query.get_or_404(staff.course_id)

    _institution_header(elements, styles, "STUDENTS’ CONSOLIDATED FEEDBACK ON FACULTY & CORRECTIVE MEASURES")

    # Meta information (can be adapted when academic year / semester become real fields)
    current_year = datetime.utcnow().year
    academic_year = f"{current_year}-{current_year+1}"  # placeholder logic
    semester_label = "EVEN SEMESTER"  # assumption; adjust if you store this info
    class_name = "CLASS"  # placeholder

    # Heading block – place immediately under institutional header
    meta_table_data = [
        [Paragraph(f"<b>ACADEMIC YEAR:</b> {academic_year}", normal_style), '', Paragraph(f"<b>SEMESTER:</b> {semester_label}", normal_style), ''],
        [Paragraph(f"<b>Name of the Faculty</b><br/>{staff.name}", normal_style), Paragraph(f"<b>Course Code & Name</b><br/>{course.code}<br/>{course.name}", normal_style), Paragraph(f"<b>Class</b><br/>{class_name}", normal_style), Paragraph(f"<b>No. of students offered the feedback</b><br/>{len(FeedbackResponse.query.filter_by(staff_id=staff_id, event_id=event_id).all())}", normal_style)]
    ]
    meta_tbl = Table(meta_table_data, colWidths=[2.2*inch, 2.2*inch, 1.2*inch, 1.9*inch])
    meta_tbl.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.8, colors.black),
        ('SPAN', (0,0), (1,0)),  # academic year across first two columns
        ('SPAN', (2,0), (3,0)),  # semester across last two columns
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('BACKGROUND', (0,1), (-1,1), colors.beige),
    ]))
    elements.append(meta_tbl)
    elements.append(Spacer(1, 0.3*inch))

    # Ratings distribution table (Measures) directly below the title per user request
    feedback_responses = FeedbackResponse.query.filter_by(staff_id=staff_id, event_id=event_id).all()
    # Determine only questions that actually received at least one response for this staff & event
    used_question_ids = set()
    for fr in feedback_responses:
        for qr in fr.question_responses:
            used_question_ids.add(qr.question_id)
    if used_question_ids:
        questions = Question.query.filter(Question.id.in_(used_question_ids)).order_by(Question.id).all()
    else:
        questions = []

    # Build rating counts per question
    rating_counts = {q.id: {1:0,2:0,3:0,4:0} for q in questions}
    for fr in feedback_responses:
        for qr in fr.question_responses:
            if qr.question_id in rating_counts:
                rating_counts[qr.question_id][qr.rating] += 1

    # Header row: Parameter + Q1, Q2, ... abbreviations as requested
    header_row = ['Parameter'] + [f"Q{i+1}" for i, _ in enumerate(questions)]

    measures_data = [header_row]
    for rating in [4,3,2,1]:
        row = [str(rating)]
        for q in questions:
            row.append(str(rating_counts[q.id][rating]))
        measures_data.append(row)
    # % in 3 & 4
    percent_row = ['% in 3 & 4']
    for q in questions:
        total = sum(rating_counts[q.id].values())
        pct = ((rating_counts[q.id][3] + rating_counts[q.id][4]) / total * 100) if total else 0
        percent_row.append(f"{pct:.1f}")
    measures_data.append(percent_row)

    col_widths = [1.4*inch] + [ (6.0*inch - 1.4*inch)/ max(1, len(questions)) ] * len(questions)
    measures_tbl = Table(measures_data, colWidths=col_widths)
    measures_tbl.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.whitesmoke),
    ]))
    elements.append(measures_tbl)
    elements.append(Spacer(1, 0.4*inch))

    # --- Dynamic Grouped Bar Chart (Total, 4,3,2,1 counts + % above each group) ---
    if _MATPLOTLIB_AVAILABLE and questions:
        try:
            q_labels = [f"Q{i+1}" for i in range(len(questions))]
            totals = [sum(rating_counts[q.id].values()) for q in questions]
            c1 = [rating_counts[q.id][1] for q in questions]
            c2 = [rating_counts[q.id][2] for q in questions]
            c3 = [rating_counts[q.id][3] for q in questions]
            c4 = [rating_counts[q.id][4] for q in questions]
            pct = [(c3[i] + c4[i]) / totals[i] * 100 if totals[i] else 0 for i in range(len(questions))]

            img_buffer = generate_excel_grouped_bar_chart(
                q_labels,
                totals,
                c4,
                c3,
                c2,
                c1,
                pct,
                width_in=6.8,
                height_in=2.8,
                dpi=300,
            )

            if img_buffer is None:
                raise RuntimeError("Matplotlib not available")

            chart_img = Image(img_buffer, width=6.8*inch, height=2.8*inch)
            elements.append(chart_img)
            elements.append(Spacer(1, 0.3*inch))
        except Exception as e:
            elements.append(Paragraph(f"Chart generation error: {e}", normal_style))
            elements.append(Spacer(1, 0.2*inch))
    else:
        if not _MATPLOTLIB_AVAILABLE:
            elements.append(Paragraph("Matplotlib not installed; chart skipped. Add 'matplotlib' to requirements.txt to enable.", normal_style))
            elements.append(Spacer(1, 0.2*inch))

    # Continue with previous detailed table & chart starting on a new page
    elements.append(PageBreak())
    elements.append(Paragraph("Feedback Report", title_style))
    elements.append(Spacer(1, 0.25*inch))
    elements.append(Paragraph(f"Event: {event.title}", subtitle_style))
    elements.append(Paragraph(f"Course: {course.code} - {course.name}", subtitle_style))
    elements.append(Paragraph(f"Staff: {staff.name}", subtitle_style))
    elements.append(Spacer(1, 0.5*inch))
    if not questions:
        elements.append(Spacer(1, 0.25*inch))
        elements.append(Paragraph("No responses submitted for this staff in the selected event.", normal_style))
        doc.build(elements)
        buffer.seek(0)
        return buffer
    question_data = []
    for idx, question in enumerate(questions, start=1):
        ratings = []
        for feedback in feedback_responses:
            response = QuestionResponse.query.filter_by(feedback_id=feedback.id, question_id=question.id).first()
            if response:
                ratings.append(response.rating)
        if ratings:
            avg = sum(ratings) / len(ratings)
            question_data.append((question.text, round(avg, 2), f"Q{idx}"))
        else:
            question_data.append((question.text, 0, f"Q{idx}"))

    table_data = [['Question', 'Average Rating', 'Question No']]
    table_data.extend(question_data)
    table = Table(table_data, colWidths=[4.6*inch, 1.2*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))

    elements.append(Spacer(1, 0.5*inch))

    elements.append(PageBreak())

    responded_students = db.session.query(Student.id).join(FeedbackResponse, Student.id == FeedbackResponse.student_id)\
                         .filter(FeedbackResponse.staff_id == staff_id, FeedbackResponse.event_id == event_id)\
                         .distinct().count()
    total_students = Student.query.count()
    elements.append(Paragraph("Participation Statistics", subtitle_style))
    elements.append(Paragraph(f"Responses: {responded_students} students", normal_style))
    elements.append(Paragraph(f"Total Students: {total_students} students", normal_style))
    if total_students > 0:
        response_rate = (responded_students / total_students) * 100
        elements.append(Paragraph(f"Response Rate: {response_rate:.2f}%", normal_style))

    # Kind Note & Measures section requested by user
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Kind Note:</b>", normal_style))
    elements.append(Paragraph("(i) A target of 75% from the maximum score is being considered for evaluation and <b>attained target of 75%</b> is to be checked for every parameter.", normal_style))
    elements.append(Paragraph("<para align='center'><b>(OR)</b></para>", normal_style))
    elements.append(Paragraph("(ii) Corrective measures shall be given for <b>One least score</b> in specified criteria.", normal_style))
    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("<b>Measures planned for improvement</b>", normal_style))

    # Signature placeholders ONLY on final page (dashed, separated lines)
    class SignatureLines(Flowable):
        def __init__(self, total_width, left_label, right_label, line_length=170):
            super().__init__()
            self.width = total_width
            self.height = 40
            self.left_label = left_label
            self.right_label = right_label
            self.line_length = line_length
        def draw(self):
            c = self.canv
            y = 28
            c.setLineWidth(0.8)
            # dashed pattern: 4 on, 3 off
            c.setDash(4,3)
            # left line
            c.line(0, y, self.line_length, y)
            # right line
            c.line(self.width - self.line_length, y, self.width, y)
            c.setDash()  # reset
            c.setFont('Helvetica-Bold', 9)
            c.drawString(0, y-14, self.left_label)
            c.drawRightString(self.width, y-14, self.right_label)

    elements.append(Spacer(1, 0.9*inch))
    elements.append(SignatureLines(doc.width, 'Signature of the Faculty', 'HOD'))
=======
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing

from myextensions import db
from models import (
    Staff, Course, Event, Question,
    FeedbackResponse, QuestionResponse, Student
)

def generate_pdf_report(staff_id, event_id):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=72, rightMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    elements = []

    # ——— HEADER (unchanged) ———
    left_logo  = Image('static/images/image.png', width=0.8*inch, height=0.8*inch)
    right_logo = Image('static/images/logo.png',    width=0.8*inch, height=0.8*inch)
    title_para = Paragraph(
        "<b>SRI RAMAKRISHNA ENGINEERING COLLEGE</b>",
        ParagraphStyle('TitleCenter', alignment=TA_CENTER, fontSize=16)
    )
    doc_width = letter[0] - (doc.leftMargin + doc.rightMargin)
    header_tbl = Table(
        [[ left_logo, title_para, right_logo ]],
        colWidths=[0.9*inch, doc_width - 1.8*inch, 0.9*inch]
    )
    header_tbl.setStyle(TableStyle([
        ('VALIGN',   (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',    (1,0), (1,0),    'CENTER'),
        ('BOX',      (0,0), (-1,-1), 0, colors.white),
    ]))
    elements.append(header_tbl)
    elements.append(Spacer(1, 8))

    # Sub‑headings
    for txt in [
        "[Educational Service: SNR Sons Charitable Trust]",
        "[Autonomous Institution, Reaccredited by NAAC with 'A+' Grade]",
        "[Approved by AICTE and Permanently Affiliated to Anna University, Chennai]",
        "[ISO 9001:2015 Certified and all eligible programmes Accredited by NBA]",
        "VATTAMALAPALAYAM, N.G.G.O. COLONY POST, COIMBATORE – 641 022."
    ]:
        elements.append(Paragraph(txt,
            ParagraphStyle('center', alignment=TA_CENTER, fontSize=10)))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING",
        ParagraphStyle('center', alignment=TA_CENTER,
                       fontSize=12, fontName='Helvetica-Bold')
    ))
    elements.append(Paragraph(
        "STUDENTS’ CONSOLIDATED FEEDBACK ON FACULTY & CORRECTIVE MEASURES",
        ParagraphStyle('center', alignment=TA_CENTER,
                       fontSize=12, fontName='Helvetica-Bold')
    ))
    elements.append(Spacer(1, 20))

    # ——— LOAD DATA ———
    staff   = Staff.query.get_or_404(staff_id)
    event   = Event.query.get_or_404(event_id)
    course  = Course.query.get_or_404(staff.course_id)
    total_students    = Student.query.count()
    feedback_responses = FeedbackResponse.query.filter_by(
        staff_id=staff_id, event_id=event_id
    ).all()
    responded_students = len({f.student_id for f in feedback_responses})

    # determine semester label
    sem_label = "EVEN SEMESTER" if getattr(event, 'semester', 0) % 2 == 0 else "ODD SEMESTER"

    # ——— 1. ACADEMIC DETAILS TABLE ———
    acad_data = [
        # merge first two cols → Academic Year, and last two → Semester
        [
            Paragraph(f"<b>ACADEMIC YEAR:</b> {getattr(event, 'academic_year', '')}", styles['Normal']),
            '',
            Paragraph(f"<b>SEMESTER:</b> {getattr(event, 'semester', '')}", styles['Normal']),
            ''
        ],
        # merge cells to allow multi‑line Faculty names
        [
            Paragraph("<b>Name of the Faculty</b>", styles['Normal']),
            Paragraph(
                f"{staff.name}<br/>{getattr(event, 'co_instructor', '')}",
                styles['Normal']
            ),
            Paragraph("<b>Semester</b>", styles['Normal']),
            Paragraph(str(getattr(event, 'semester', '')), styles['Normal'])
        ],
        [
            Paragraph("<b>Course Code & Name</b>", styles['Normal']),
            Paragraph(f"{course.code}<br/>{course.name}", styles['Normal']),
            Paragraph("<b>Class</b>", styles['Normal']),
            Paragraph(str(getattr(event, 'class_year', '')), styles['Normal'])
        ],
        [
            Paragraph("<b>No. of students in the class</b>", styles['Normal']),
            Paragraph(str(responded_students), styles['Normal']),
            Paragraph("<b>No. of students offered the feedback</b>", styles['Normal']),
            Paragraph(str(responded_students), styles['Normal'])
        ]
    ]
    acad_tbl = Table(acad_data,
                     colWidths=[1.8*inch, 2.2*inch, 1.2*inch, 1.2*inch])
    acad_tbl.setStyle(TableStyle([
        ('SPAN',     (0,0), (1,0)),
        ('SPAN',     (2,0), (3,0)),
        ('GRID',     (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND',(0,0),(-1,0), colors.lightgrey),
        ('VALIGN',   (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',    (0,0), (-1,-1), 'CENTER'),
        ('LEFTPADDING',  (1,1), (1,-1), 6),
    ]))
    elements.append(acad_tbl)
    elements.append(Spacer(1, 12))

    # ——— 2. FEEDBACK TABLE ———
    questions = Question.query.order_by(Question.id).all()
    rating_labels = [4,3,2,1]

    # build count matrix
    counts = {r: [] for r in rating_labels}
    totals = []
    for q in questions:
        cnt = {r:0 for r in rating_labels}
        for fb in feedback_responses:
            resp = QuestionResponse.query.filter_by(
                feedback_id=fb.id, question_id=q.id
            ).first()
            if resp:
                cnt[resp.rating] += 1
        for r in rating_labels:
            counts[r].append(cnt[r])
        total_q = sum(cnt.values())
        totals.append(total_q)

    # header row with full question text
    header = [Paragraph("<b>Parameter</b>", styles['Normal'])]
    for q in questions:
        header.append(Paragraph(f"<b>{q.text}</b>", styles['Normal']))
    table_data = [header]
    for r in rating_labels:
        row = [Paragraph(str(r), styles['Normal'])] + [Paragraph(str(val), styles['Normal']) for val in counts[r]]
        table_data.append(row)
    table_data.append([Paragraph("Total", styles['Normal'])] + [Paragraph(str(val), styles['Normal']) for val in totals])
    pct_3_4 = [round(((counts[3][i] + counts[4][i]) / totals[i] * 100), 1) if totals[i] else 0 for i in range(len(questions))]
    table_data.append([Paragraph("% in 3&4", styles['Normal'])] + [Paragraph(str(val), styles['Normal']) for val in pct_3_4])

    feedback_tbl = Table(table_data,
                         repeatRows=1,
                         colWidths=[0.9*inch] +
                                   [(doc_width - 0.9*inch) / len(questions)] * len(questions))
    feedback_tbl.setStyle(TableStyle([
        ('GRID',        (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND',  (0,0), (-1,0), colors.HexColor('#d9d9d9')),
        ('BACKGROUND',  (0,-2),(-1,-2), colors.HexColor('#eaf3fa')),
        ('BACKGROUND',  (0,-1),(-1,-1), colors.HexColor('#eaf3fa')),
        ('ALIGN',       (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    elements.append(feedback_tbl)
    elements.append(Spacer(1, 12))

    # Add bar chart below the parameter table and above the Kind Note
    from reportlab.graphics.charts.legends import Legend
    from reportlab.graphics.widgets.markers import makeMarker
    drawing = Drawing(800, 300)
    bc = VerticalBarChart()
    bc.x = 100
    bc.y = 10
    bc.height = 100
    bc.width = 350
    bc.data = [totals, counts[4], counts[3], counts[2], pct_3_4]
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(max(totals + counts[4] + counts[3] + counts[2]), 100)
    bc.valueAxis.valueStep = 10
    bc.categoryAxis.labels = [f"Q{i+1}" for i in range(len(questions))]
    bc.barLabels.nudge = 7
    bc.barLabelFormat = '%d'
    bc.groupSpacing = 10
    bc.barSpacing = 2
    # Set colors for each series
    bc.bars[0].fillColor = colors.HexColor('#4F81BD')  # Total number of students (blue)
    bc.bars[1].fillColor = colors.HexColor('#9BBB59')  # 4 (green)
    bc.bars[2].fillColor = colors.HexColor('#F79646')  # 3 (orange)
    bc.bars[3].fillColor = colors.HexColor('#C0504D')  # 2 (red)
    bc.bars[4].fillColor = colors.HexColor('#00B050')  # %in 3&4 (light green)
    # Add legend
    # legend = Legend() # <-- Remove this line
    # legend_width = 350 # <-- Remove this line
    # legend.x = (800 - legend_width) // 2  # Center the legend in the drawing # <-- Remove this line
    # legend.y = 220  # Place legend above the chart # <-- Remove this line
    # legend.dx = 8 # <-- Remove this line
    # legend.dy = 8 # <-- Remove this line
    # legend.fontName = 'Helvetica' # <-- Remove this line
    # legend.fontSize = 8 # <-- Remove this line
    # legend.boxAnchor = 'nw' # <-- Remove this line
    # legend.columnMaximum = 1 # <-- Remove this line
    # legend.strokeWidth = 0 # <-- Remove this line
    # legend.deltax = 10  # Reduce space between legend items # <-- Remove this line
    # legend.deltay = 10 # <-- Remove this line
    # legend.autoXPadding = 5 # <-- Remove this line
    # legend.colorNamePairs = [ # <-- Remove this line
    #     (colors.HexColor('#4F81BD'), 'Total number of students'), # <-- Remove this line
    #     (colors.HexColor('#9BBB59'), '4'), # <-- Remove this line
    #     (colors.HexColor('#F79646'), '3'), # <-- Remove this line
    #     (colors.HexColor('#C0504D'), '2'), # <-- Remove this line
    #     (colors.HexColor('#00B050'), '%in 3&4'), # <-- Remove this line
    # ] # <-- Remove this line
    drawing.add(bc)
    # drawing.add(legend) # <-- Remove this line
    elements.append(drawing)
    elements.append(Spacer(1, 6))

    # Add custom legend as a table below the graph
    legend_data = [
        [
            '', Paragraph('<b>Total number of students</b>', styles['Normal']),
            '', Paragraph('<b>#REF!</b>', styles['Normal']),
            '', Paragraph('<b>4</b>', styles['Normal']),
            '', Paragraph('<b>3</b>', styles['Normal']),
            '', Paragraph('<b>2</b>', styles['Normal']),
            '', Paragraph('<b>%in 3&4</b>', styles['Normal'])
        ]
    ]
    legend_colors = [
        colors.HexColor('#4F81BD'),  # blue
        colors.HexColor('#F79646'),  # orange
        colors.HexColor('#A6A6A6'),  # gray
        colors.HexColor('#FFD966'),  # yellow
        colors.HexColor('#5B9BD5'),  # blue
        colors.HexColor('#70AD47'),  # green
    ]
    legend_cells = []
    for color in legend_colors:
        legend_cells.append('')
        legend_cells.append('')
    # Build the legend row with colored squares
    legend_row = []
    for i, color in enumerate(legend_colors):
        legend_row.append('')
        legend_row.append('')
    # Actually fill the legend row with colored squares and labels
    legend_row = []
    legend_labels = [
        'Total number of students', '#REF!', '4', '3', '2', '%in 3&4'
    ]
    for color, label in zip(legend_colors, legend_labels):
        legend_row.append(
            Table([[ '', ]], colWidths=8, rowHeights=8, style=TableStyle([
                ('BACKGROUND', (0,0), (0,0), color),
                ('BOX', (0,0), (0,0), 0.5, colors.black)
            ]))
        )
        legend_row.append(Paragraph(f'<b>{label}</b>', styles['Normal']))
    legend_table = Table([legend_row], colWidths=[10, 60, 10, 30, 10, 15, 10, 15, 10, 30, 10, 40], hAlign='LEFT')
    elements.append(legend_table)
    elements.append(Spacer(1, 12))

    # Add Kind Note and signature section as in the screenshot
    elements.append(Paragraph('<b>Kind Note:</b>', styles['Normal']))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph('''(i) A target of 75% from the maximum score is being considered for evaluation and <b>attained target of 75%</b> is to<br/>be checked for every parameter.''', ParagraphStyle('note', parent=styles['Normal'], leftIndent=20, spaceAfter=6)))
    elements.append(Paragraph('<b>(OR)</b>', ParagraphStyle('center', alignment=TA_CENTER, fontSize=11, spaceAfter=6)))
    elements.append(Paragraph('''(ii) Corrective measures shall be given for <b>One least score</b> in specified criteria.''', ParagraphStyle('note', parent=styles['Normal'], leftIndent=20, spaceAfter=6)))
    elements.append(Paragraph('<b>Measures planned for improvement</b>', styles['Normal']))
    elements.append(Spacer(1, 18))
    # Signature lines
    sign_table = Table([
        [Paragraph('<b>Signature of the Faculty</b>', styles['Normal']), '', Paragraph('<b>HOD</b>', styles['Normal'])]
    ], colWidths=[3*inch, 1.5*inch, 2*inch])
    sign_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('TOPPADDING', (0,0), (-1,-1), 12),
    ]))
    elements.append(sign_table)

    # ——— 3. (Your existing chart, participation stats & footer) ———
    # ... copy the exact code for Drawing, VerticalBarChart,
    #     Participation Statistics, Kind Note, Signature lines ...
>>>>>>> 4f20009145f69254e2269f4cf004e63fbc874e2c

    doc.build(elements)
    buffer.seek(0)
    return buffer
