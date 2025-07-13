from flask import Flask, request, send_file, abort
from flask_cors import CORS 
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
import uuid

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

    data = request.get_json()

    raw_text = data.get("text", "")
    style = data.get("style", "sloppy1")

    #this is the JSON conversion code

    # === Step 2: Normalize and clean text ===
    # Replace all line endings with \n
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Replace tabs with spaces
    text = text.replace("\t", "    ")

    # Optional: escape backslashes and quotes (visual safety)
    text = text.replace("\\", "\\\\").replace("\"", "\\\"")

    # Optional: Remove emojis or non-printable characters
    text = ''.join(char for char in text if char.isprintable())
    

    font_path = FONT_MAP.get(style)
    if not font_path or not os.path.exists(font_path):
        return abort(400, "Invalid handwriting style")

    font_prop = font_manager.FontProperties(fname=font_path)
    filename = f"{uuid.uuid4()}.png"

    fig, ax = plt.subplots(figsize=(8, 6))

    #here i need to change line
    lines = text.split("\n")
    y = 0.95  # Start from top
    line_height = 0.07  # Adjust for spacing

    for line in lines:
        ax.text(0.05, y, line, fontsize=16, fontproperties=font_prop, va='top')
        y -= line_height

    ax.axis('off')
    plt.savefig(filename, bbox_inches='tight')
    plt.close()

    return send_file(filename, mimetype='image/png')

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

