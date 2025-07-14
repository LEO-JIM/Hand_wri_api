from flask import Flask, request, send_file, abort
from flask_cors import CORS
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
import uuid
import textwrap

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

    font_prop = font_manager.FontProperties(fname=font_path)

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
    fig, ax = plt.subplots(figsize=(page_width, page_height), dpi=DPI)
    ax.axis('off')
    y = MARGIN_TOP
    for line in lines:
        ax.text(MARGIN_LEFT, y, line, fontsize=FONT_SIZE, fontproperties=font_prop, va='top')
        y -= LINE_HEIGHT

    filename = f"{uuid.uuid4()}.png"
    plt.savefig(filename, bbox_inches='tight', pad_inches=0.4)
    plt.close()

    # Return the file directly
    response = send_file(filename, mimetype='image/png')
    # Optionally cleanup file after sending
    try:
        os.remove(filename)
    except Exception:
        pass
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
