from flask import Flask, request, send_file, abort
from flask_cors import CORS
import os
import uuid
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)
CORS(app)

FONT_MAP = {
    "sloppy1": "Sloppy_Hand.ttf",
    "rush": "zai_NicolasSloppyPen.ttf"
}

A4_WIDTH_IN = 8.3
A4_HEIGHT_IN = 11.7
DPI = 150
FONT_SIZE = 11
LINE_HEIGHT = 0.035
MARGIN_LEFT = 0.07
MARGIN_TOP = 0.95

@app.route('/write', methods=['POST', 'OPTIONS'])
def write():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()
    text = data.get("text", "")
    style = data.get("style", "sloppy1")
    page_idx = int(request.args.get("page", 0))  # Default to first page

    font_path = FONT_MAP.get(style)
    if not font_path or not os.path.exists(font_path):
        return abort(400, "Invalid handwriting style")

    for style, font_file in FONT_MAP.items():
        if os.path.exists(font_file):
            pdfmetrics.registerFont(TTFont(style, font_file))

    # --- Page calculation ---
    page_width, page_height = A4_WIDTH_IN, A4_HEIGHT_IN
    max_chars_per_line = 90
    max_lines_per_page = int((MARGIN_TOP - 0.07) // LINE_HEIGHT)

    # Wrap text, respect manual \n
    logical_lines = text.split("\n")
    wrapped_lines = []
    for logical_line in logical_lines:
        wraps = textwrap.wrap(logical_line, width=max_chars_per_line)
        if wraps:
            wrapped_lines.extend(wraps)
        else:
            wrapped_lines.append("")

    # --- Paging ---
    pages = []
    for i in range(0, len(wrapped_lines), max_lines_per_page):
        pages.append(wrapped_lines[i:i + max_lines_per_page])

    # --- Render only requested page ---
    if page_idx < 0 or page_idx >= len(pages):
        return abort(404, f"Page {page_idx} not found")

    lines = pages[page_idx]
    filename = f"{uuid.uuid4()}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Convert margins and line height from inches to points (1 inch = 72 points)
    margin_left_pt = MARGIN_LEFT * 72
    margin_top_pt = height - (MARGIN_TOP * 72)
    line_height_pt = LINE_HEIGHT * 72
    font_size_pt = FONT_SIZE

    c.setFont(style, font_size_pt)
    y = margin_top_pt
    for line in lines:
        c.drawString(margin_left_pt, y, line)
        y -= line_height_pt

    c.save()

    response = send_file(filename, mimetype='application/pdf')
    try:
        os.remove(filename)
    except Exception:
        pass
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
