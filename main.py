from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
import uuid
import textwrap
from PIL import Image
import base64

app = Flask(__name__)
CORS(app)

FONT_MAP = {
    "sloppy1": "Sloppy_Hand.ttf",
    "rush": "zai_NicolasSloppyPen.ttf"
}

# --- Config ---
A4_WIDTH_IN = 8.3
A4_HEIGHT_IN = 11.7
DPI = 150  # Print-like clarity
FONT_SIZE = 13  # Small but readable for homework
LINE_HEIGHT = 0.045  # Enough to fit many lines per page
MARGIN_LEFT = 0.07
MARGIN_TOP = 0.95

@app.route('/write', methods=['POST', 'OPTIONS'])
def write():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()
    text = data.get("text", "")
    style = data.get("style", "sloppy1")
    font_path = FONT_MAP.get(style)
    if not font_path or not os.path.exists(font_path):
        return abort(400, "Invalid handwriting style")

    font_prop = font_manager.FontProperties(fname=font_path)

    # --- Page calculation ---
    page_width, page_height = A4_WIDTH_IN, A4_HEIGHT_IN
    max_chars_per_line = 60  # Smaller font, more words
    # Estimate: from margin-top down, each line takes LINE_HEIGHT units, stop before off-page
    max_lines_per_page = int((MARGIN_TOP - 0.07) // LINE_HEIGHT)

    # Wrap text per line, respect manual \n breaks
    logical_lines = text.split("\n")
    wrapped_lines = []
    for logical_line in logical_lines:
        wraps = textwrap.wrap(logical_line, width=max_chars_per_line)
        if wraps:
            wrapped_lines.extend(wraps)
        else:
            wrapped_lines.append("")  # For empty lines

    # --- Paging ---
    pages = []
    for i in range(0, len(wrapped_lines), max_lines_per_page):
        pages.append(wrapped_lines[i:i + max_lines_per_page])

    # --- Render each page ---
    base64_images = []
    for page in pages:
        fig, ax = plt.subplots(figsize=(page_width, page_height), dpi=DPI)
        ax.axis('off')
        y = MARGIN_TOP
        for line in page:
            ax.text(MARGIN_LEFT, y, line, fontsize=FONT_SIZE, fontproperties=font_prop, va='top')
            y -= LINE_HEIGHT
        filename = f"{uuid.uuid4()}.png"
        plt.savefig(filename, bbox_inches='tight', pad_inches=0.4)
        plt.close()

        # Read and encode image as base64 data URI
        with open(filename, "rb") as img_f:
            img_bytes = img_f.read()
            b64 = base64.b64encode(img_bytes).decode()
            data_uri = f"data:image/png;base64,{b64}"
            base64_images.append(data_uri)
        os.remove(filename)  # cleanup

    # --- Return all pages as array ---
    return jsonify({"images": base64_images})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
