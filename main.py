from flask import Flask, request, send_file, abort
from flask_cors import CORS 
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
import uuid
import textwrap
import zipfile

app = Flask(__name__)
CORS(app)

FONT_MAP = {
    "sloppy1": "Sloppy_Hand.ttf",
    "rush": "zai_NicolasSloppyPen.ttf"
}

A4_SIZE = (8.27, 11.69)  # A4 size in inches
FONT_SIZE = 20           # Typical college homework
LINE_HEIGHT = 0.05       # In relative figure coordinates, adjust as needed
MAX_CHARS_PER_LINE = 45  # Adjust for handwritten style and font size

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
    logical_lines = text.split("\n")
    # Calculate how many lines fit per page
    lines_per_page = int((1.0 - 0.07) / LINE_HEIGHT)  # leave a top margin

    wrapped_lines = []
    for logical_line in logical_lines:
        wrapped_lines.extend(textwrap.wrap(logical_line, width=MAX_CHARS_PER_LINE) or [''])  # handle blank lines

    # Split into pages
    pages = [wrapped_lines[i:i+lines_per_page] for i in range(0, len(wrapped_lines), lines_per_page)]
    filenames = []
    for page_num, page_lines in enumerate(pages, 1):
        fig, ax = plt.subplots(figsize=A4_SIZE)
        ax.axis('off')
        y = 0.95
        for line in page_lines:
            ax.text(0.06, y, line, fontsize=FONT_SIZE, fontproperties=font_prop, va='top')
            y -= LINE_HEIGHT
        filename = f"{uuid.uuid4()}_page{page_num}.png"
        plt.savefig(filename, bbox_inches='tight', dpi=300)
        plt.close()
        filenames.append(filename)

    # If only one page, just return that
    if len(filenames) == 1:
        return send_file(filenames[0], mimetype='image/png')
    else:
        # Otherwise, zip them
        zip_filename = f"{uuid.uuid4()}_pages.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for f in filenames:
                zipf.write(f)
        # Clean up png files after zipping
        for f in filenames:
            os.remove(f)
        return send_file(zip_filename, mimetype='application/zip')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
