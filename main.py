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


@app.route('/write', methods=['POST', 'OPTIONS'])
def write():
    if request.method == 'OPTIONS':
        return '', 204


    print("RAW REQUEST DATA:", request.data)
    print("JSON DATA:", request.get_json())
    
    data = request.get_json()

    text = data.get("text", "")
    style = data.get("style", "sloppy1")
    
    font_path = FONT_MAP.get(style)
    if not font_path or not os.path.exists(font_path):
        return abort(400, "Invalid handwriting style")

    font_prop = font_manager.FontProperties(fname=font_path)
    filename = f"{uuid.uuid4()}.png"

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis('off')
    

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis('off')
    
    # Split by \n (manual breaks)
    logical_lines = text.split("\n")
    y = 0.95
    line_height = 0.07
    max_chars_per_line = 50  # Wrap after ~50 characters (adjust as needed)
    
    for logical_line in logical_lines:
        # Auto-wrap long lines
        wrapped_lines = textwrap.wrap(logical_line, width=max_chars_per_line)
        for wrapped_line in wrapped_lines:
            ax.text(0.05, y, wrapped_line, fontsize=16, fontproperties=font_prop, va='top')
            y -= line_height


    plt.savefig(filename, bbox_inches='tight')
    plt.close()

    return send_file(filename, mimetype='image/png')

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

