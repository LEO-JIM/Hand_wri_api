from flask import Flask, request, send_file, abort
from flask_cors import CORS
import os
import uuid
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch

app = Flask(__name__)
CORS(app)

# --- Configuration ---
FONT_FILES = {
    "sloppy1": ("SloppyHand",  "Sloppy_Hand.ttf"),
    "rush":    ("RushPen",      "zai_NicolasSloppyPen.ttf"),
}

# register fonts once at startup
HERE = os.path.dirname(__file__)
for key, (ps_name, filename) in FONT_FILES.items():
    path = os.path.join(HERE, filename)
    if not os.path.exists(path):
        raise RuntimeError(f"Font file not found: {path}")
    pdfmetrics.registerFont(TTFont(ps_name, path))

# Page geometry (A4)
PAGE_WIDTH_PT, PAGE_HEIGHT_PT = A4
MARGIN_LEFT_IN  = 0.7    # inches
MARGIN_TOP_IN   = 0.7    # inches down from top
FONT_SIZE_PT    = 12     # points
LINE_HEIGHT_IN  = 0.3    # inches between lines
CHARS_PER_LINE  = 110     # for textwrap

@app.route('/write', methods=['POST', 'OPTIONS'])
def write():
    if request.method == 'OPTIONS':
        return '', 204

    # 1) Parse input
    data  = request.get_json(force=True)
    raw   = data.get("text", "")
    style = data.get("style", "sloppy1")
    page  = int(request.args.get("page", 0))

    # 2) Validate font style
    if style not in FONT_FILES:
        return abort(400, "Invalid handwriting style")
    ps_font_name = FONT_FILES[style][0]

    # 3) Normalize and split text into wrapped lines
    #    respect manual \n, then wrap long lines
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    logical = text.split("\n")
    wrapped = []
    for L in logical:
        if L.strip() == "":
            # preserve blank lines
            wrapped.append("")
        else:
            wrapped.extend(textwrap.wrap(L, width=CHARS_PER_LINE))

    # 4) Pagination
    # how many lines fit per page?
    margin_top_pt   = PAGE_HEIGHT_PT - MARGIN_TOP_IN * inch
    line_height_pt  = LINE_HEIGHT_IN * inch
    lines_per_page  = int((margin_top_pt) // line_height_pt)
    pages = [
        wrapped[i : i + lines_per_page]
        for i in range(0, len(wrapped), lines_per_page)
    ]

    if page < 0 or page >= len(pages):
        return abort(404, f"Page {page} out of range")

    # 5) Render requested page to PDF
    filename = f"{uuid.uuid4()}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Convert layout units
    margin_left_pt = MARGIN_LEFT_IN * 72
    margin_top_pt = height - (MARGIN_TOP_IN * 72)
    line_height_pt = LINE_HEIGHT_IN * 72
    font_size_pt = FONT_SIZE_PT
    
    c.setFont(ps_font_name, font_size_pt)
    
    for page_lines in pages:
        y = margin_top_pt
        c.setFont(ps_font_name, font_size_pt)
        for line in page_lines:
            c.drawString(margin_left_pt, y, line)
            y -= line_height_pt
        c.showPage()  # Go to next page (or finalize if last)
    
    c.save()

    # 6) Send & clean up
    rv = send_file(filename, mimetype="application/pdf")
    try:
        os.remove(filename)
    except OSError:
        pass
    return rv

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
