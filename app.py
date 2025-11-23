from flask import Flask, render_template_string, request, send_file
from PIL import Image, ImageDraw, ImageFont
import os

app = Flask(__name__)

# HTML template
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Mentorship Avatar Generator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        textarea { width: 300px; height: 100px; }
        input[type=text] { width: 300px; }
        .section { margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Mentorship Avatar Generator</h1>
    <form method="POST" action="/generate">
        <div class="section">
            <h3>Ultimate Avatar</h3>
            <label>Title:</label><br>
            <input type="text" name="ultimate_title"><br>
            <label>Behaviors (one per line):</label><br>
            <textarea name="ultimate_behaviors"></textarea>
        </div>
        <div class="section">
            <h3>Worst Avatar</h3>
            <label>Title:</label><br>
            <input type="text" name="worst_title"><br>
            <label>Behaviors (one per line):</label><br>
            <textarea name="worst_behaviors"></textarea>
        </div>
        <input type="submit" value="Generate Avatars">
    </form>
</body>
</html>
"""

def create_avatar(title, behaviors, filename):
    # Skapa en vit bild
    img = Image.new('RGB', (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Standardfont (du kan byta till TrueType-font om du vill)
    font_title = ImageFont.load_default()
    font_text = ImageFont.load_default()

    # Titeltext
    draw.text((20, 20), title, font=font_title, fill=(0, 0, 0))

    # Enkel "avatar"-figur: huvud + kropp
    draw.ellipse((250, 100, 350, 200), outline=(0, 0, 0), width=3)  # huvud
    draw.rectangle((250, 200, 350, 400), outline=(0, 0, 0), width=3)  # kropp

    # Beteenden som lista
    y_text = 420
    for behavior in behaviors:
        behavior = behavior.strip()
        if behavior:
            draw.text((20, y_text), f"- {behavior}", font=font_text, fill=(0, 0, 0))
            y_text += 20

    img.save(filename)

def safe_filename(title):
    if not title:
        title = "avatar"
    # Ta bort konstiga tecken
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ "
    cleaned = "".join(c for c in title if c in allowed).strip()
    if not cleaned:
        cleaned = "avatar"
    return cleaned.replace(" ", "_") + ".png"

@app.route('/', methods=['GET'])
def index():
    return render_template_string(html_template)

@app.route('/generate', methods=['POST'])
def generate():
    ultimate_title = request.form.get('ultimate_title', 'Ultimate Avatar')
    ultimate_behaviors_raw = request.form.get('ultimate_behaviors', '')
    ultimate_behaviors = ultimate_behaviors_raw.split('\n')

    worst_title = request.form.get('worst_title', 'Worst Avatar')
    worst_behaviors_raw = request.form.get('worst_behaviors', '')
    worst_behaviors = worst_behaviors_raw.split('\n')

    output_folder = "avatars_web_output"
    os.makedirs(output_folder, exist_ok=True)

    ultimate_filename = safe_filename(ultimate_title)
    worst_filename = safe_filename(worst_title)

    ultimate_file = os.path.join(output_folder, ultimate_filename)
    worst_file = os.path.join(output_folder, worst_filename)

    create_avatar(ultimate_title, ultimate_behaviors, ultimate_file)
    create_avatar(worst_title, worst_behaviors, worst_file)

    # Visa enkla länkar för nedladdning
    return (
        "<h2>Avatars generated!</h2>"
        f'<p><a href="/download/{ultimate_filename}">Download Ultimate Avatar</a></p>'
        f'<p><a href="/download/{worst_filename}">Download Worst Avatar</a></p>'
        '<p><a href="/">Back</a></p>'
    )

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    return send_file(os.path.join("avatars_web_output", filename), as_attachment=True)

if __name__ == '__main__':
    # Kör appen, t.ex. med: python app.py
    app.run(host='0.0.0.0', port=5000, debug=True)
