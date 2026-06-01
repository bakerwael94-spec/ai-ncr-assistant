# pdf_service.py


from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

def generate_pdf(df):

    pdf_file = "NCR_Report.pdf"

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    elements = []

    title = Paragraph("AI NCR Report", styles['Title'])

    elements.append(title)
    elements.append(Spacer(1, 12))

    for _, row in df.iterrows():

        text = f"""
        <b>ID:</b> {row['ID']}<br/>
        <b>Project:</b> {row['Project']}<br/>
        <b>Location:</b> {row['Location']}<br/>
        <b>Discipline:</b> {row['Discipline']}<br/>
        <b>Status:</b> {row['Status']}<br/>
        <b>Description:</b> {row['Description']}<br/><br/>
        """

        paragraph = Paragraph(text, styles['BodyText'])

        elements.append(paragraph)
        elements.append(Spacer(1, 12))

    doc.build(elements)

    return pdf_file