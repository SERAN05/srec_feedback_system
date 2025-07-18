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

    doc.build(elements)
    buffer.seek(0)
    return buffer
