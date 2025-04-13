
from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from flask_cors import CORS
from io import BytesIO
import base64
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
CORS(app)

def inlocuieste_diacritice(text):
    diacritice = {
        'ș': 's', 'Ș': 'S', 'ț': 't', 'Ț': 'T',
        'â': 'a', 'Â': 'A', 'î': 'i', 'Î': 'I',
        'ă': 'a', 'Ă': 'A',
        'é': 'e', 'É': 'E', 'á': 'a', 'Á': 'A',
        'í': 'i', 'Í': 'I', 'ó': 'o', 'Ó': 'O',
        'ö': 'o', 'Ö': 'O', 'ü': 'u', 'Ü': 'U',
        'ő': 'o', 'Ő': 'O', 'ú': 'u', 'Ú': 'U',
    }
    for d, r in diacritice.items():
        text = text.replace(d, r)
    return text

@app.route('/genereaza-formular', methods=['POST'])
def genereaza_formular():
    d = request.form.copy()

    for key in d:
        d[key] = inlocuieste_diacritice(d[key])

    desen_data = d['desen_semnatura'].split(',')[1]
    desen_bytes = base64.b64decode(desen_data)
    desen_stream = BytesIO(desen_bytes)

    base_pdf_path = "230.pdf"
    output = BytesIO()
    packet = BytesIO()

    can = canvas.Canvas(packet, pagesize=A4)
    img = ImageReader(desen_stream)
    can.drawImage(img, 170, 90, width=110, preserveAspectRatio=True, mask='auto')

    can.setFont("Helvetica", 10)
    can.drawString(110, 643, d['nume'])
    can.drawString(110, 621.5, d['prenume'])

    if 'initiala_tata' in d:
        can.drawString(310, 643, d['initiala_tata'])

    can.setFont("Courier", 14)
    cnp_x = 340
    cnp_y = 634
    space_between = 18

    for i, char in enumerate(d['cnp'][:4]):
        can.drawString(cnp_x + i * space_between, cnp_y, char)
    for i, char in enumerate(d['cnp'][4:8]):
        can.drawString(cnp_x + (i + 4) * space_between, cnp_y, char)
    for i, char in enumerate(d['cnp'][8:13]):
        can.drawString(cnp_x + (i + 8) * space_between - 5, cnp_y, char)

    can.setFont("Helvetica", 10)
    can.drawString(110, 600, d['strada'])
    can.drawString(300, 600, d['numar'])
    can.drawString(400, 610, d['email'])
    can.drawString(400, 586, d['telefon'])

    can.drawString(74, 580, d['bloc'])
    can.drawString(130, 580, d['scara'])
    can.drawString(169, 580, d['etaj'])

    can.setFont("Helvetica", 8)
    can.drawString(200.5, 580, d['ap'])
    can.drawString(270, 580, d['judet'])

    can.setFont("Helvetica", 10)
    can.drawString(110, 558, d['localitate'])
    can.drawString(280, 558, d['cod_postal'])

    can.save()
    packet.seek(0)

    existing_pdf = PdfReader(base_pdf_path)
    new_pdf = PdfReader(packet)
    writer = PdfWriter()
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    writer.add_page(page)

    for i in range(1, len(existing_pdf.pages)):
        writer.add_page(existing_pdf.pages[i])

    writer.write(output)
    output.seek(0)
    pdf_bytes = output.read()

    try:
        msg = EmailMessage()
        msg['Subject'] = 'Formular 230 completat'
        msg['From'] = '230@eufoniastore.ro'
        msg['To'] = 'gra4ever@gmail.com'
        msg.set_content('Formularul 230 a fost completat. PDF-ul este atașat.')

        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename='Formular_230.pdf')

        with smtplib.SMTP_SSL('mail.eufoniastore.ro', 465) as smtp:
            smtp.login('230@eufoniastore.ro', 'A=c9uw#_-o,1')
            smtp.send_message(msg)

        output.seek(0)
        return send_file(output, download_name="Formular_230_complet.pdf", as_attachment=True)
    except Exception as e:
        return f'Eroare email: {str(e)}', 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
