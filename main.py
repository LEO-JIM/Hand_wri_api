from flask import Flask, request, send_file, abort
from flask_cors import CORS 
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
import uuid

app = Flask(__name__)
CORS(app) 

FONT_MAP = {
    "sloppy1": "fonts/Sloppy_Hand.ttf",
    "rush": "fonts/zai_NicolasSloppyPen.ttf"
}


@app.route('/write', methods=['POST', 'OPTIONS'])
def write():
    if request.method == 'OPTIONS':
        return '', 204
        
    data = request.get_json()
    print("[DEBUG] Received raw data:", request.data)
    print("[DEBUG] Parsed JSON data:", data)

    text = data.get("text", "")
    style = data.get("style", "sloppy1")
    print(f"[DEBUG] Text: {text}, Style: {style}")

    font_path = FONT_MAP.get(style)
    if not font_path or not os.path.exists(font_path):
        print("[ERROR] Invalid handwriting style!")
        return abort(400, "Invalid handwriting style")

    font_prop = font_manager.FontProperties(fname=font_path)
    filename = f"{uuid.uuid4()}.png"

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.text(0.05, 0.9, text, fontsize=16, fontproperties=font_prop, wrap=True)
    ax.axis('off')
    plt.savefig(filename, bbox_inches='tight')
    plt.close()

    return send_file(filename, mimetype='image/png')

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

