from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
import os

# 현재 스크립트의 디렉토리에 PDF 생성
pdf_path = "test.pdf"

# PDF 생성
c = canvas.Canvas(pdf_path)

# 텍스트 추가 (UTF-8 인코딩 사용)
text = "테스트 문서입니다.".encode('utf-8').decode('utf-8')
c.drawString(50, 700, text)

# PDF 저장
c.save() 