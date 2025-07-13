from flask import Flask, request, send_file, abort
from flask_cors import CORS 
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
import uuid
import textwrap
from PIL import Image

app = Flask(__name__)
CORS(app) 

FONT_MAP = {
    "sloppy1": "Sloppy_Hand.ttf",
    "rush": "zai_NicolasSloppyPen.ttf"
}

# A4 size in inches
A4_WIDTH_IN = 8.3
A4_HEIGHT_IN = 11.7
DPI = 150  # Use higher DPI for clarity

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
    # Real handwriting font size (college homework style)
    font_size = 16

    # Page config
    page_width, page_height = A4_WIDTH_IN, A4_HEIGHT_IN
    line_height = 0.055  # Spacing between lines (in figure rel units)
    max_chars_per_line = 48  # fits A4 horizontally for typical handwriting font
    max_lines_per_page = int((0.9 - 0.07) // line_height)  # 0.9 to 0.07 Y range

    # Split by \n (manual breaks), then wrap
    logical_lines = text.split("\n")
    wrapped_lines = []
    for logical_line in logical_lines:
        wrapped_lines.extend(textwrap.wrap(logical_line, width=max_chars_per_line) or [""])

    # Paginate
    pages = []
    for i in range(0, len(wrapped_lines), max_lines_per_page):
        pages.append(wrapped_lines[i:i + max_lines_per_page])

    image_files = []
    for page in pages:
        fig, ax = plt.subplots(figsize=(page_width, page_height), dpi=DPI)
        ax.axis('off')
        y = 0.93  # Start a little down from the top
        for line in page:
            ax.text(0.07, y, line, fontsize=font_size, fontproperties=font_prop, va='top')
            y -= line_height
        filename = f"{uuid.uuid4()}.png"
        plt.savefig(filename, bbox_inches='tight', pad_inches=0.4)
        plt.close()
        image_files.append(filename)

    # Combine pages vertically if more than one page
    if len(image_files) == 1:
        result_filename = image_files[0]
    else:
        images = [Image.open(f) for f in image_files]
        widths, heights = zip(*(img.size for img in images))
        total_height = sum(heights)
        max_width = max(widths)
        combined_image = Image.new('RGBA', (max_width, total_height), (255, 255, 255, 255))
        y_offset = 0
        for im in images:
            combined_image.paste(im, (0, y_offset))
            y_offset += im.size[1]
        result_filename = f"{uuid.uuid4()}_combined.png"
        combined_image.save(result_filename)
        # cleanup temporary images
        for f in image_files:
            os.remove(f)

    return send_file(result_filename, mimetype='image/png')

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
