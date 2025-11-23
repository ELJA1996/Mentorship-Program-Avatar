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
        body { font-family: Arial; margin: 40px; }
        textarea { width: 300px; height: 100px; }
        input[type=text] { width: 300px; }
        .section { margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Mentorship Avatar Generator</h1>
    /generate
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
    img = Image.new('RGB', (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = ImageFont.load_default()
    font_text = ImageFont.load_default()

    draw.text((20, 20), title, font=font_title, fill=(0, 0, 0))
    draw.ellipse((250, 100, 350, 200), outline=(0, 0, 0), width=3)
    draw.rectangle((250, 200, 350, 400), outline=(0, 0, 0), width=3)

    y_text = 420
    for behavior in behaviors:
        draw.text((20, y_text), f"- {behavior}", font=font_text, fill=(0, 0, 0))
        y_text += 20

    img.save(filename)

@app.route('/', methods=['GET'])
def index():
    return render_template_string(html_template)

@app.route('/generate', methods=['POST'])
def generate():
    ultimate_title = request.form.get('ultimate_title')
    ultimate_behaviors = request.form.get('ultimate_behaviors').split('\n')
    worst_title = request.form.get('worst_title')
    worst_behaviors = request.form.get('worst_behaviors').split('\n')

    output_folder = "avatars_web_output"
    os.makedirs(output_folder, exist_ok=True)

    ultimate_file = os.path.join(output_folder, f"{ultimate_title.replace(' ', '_')}.png")
    worst_file = os.path.join(output_folder, f"{worst_title.replace(' ', '_')}.png")

    create_avatar(ultimate_title, ultimate_behaviors, ultimate_file)
    create_avatar(worst_title, worst_behaviors, worst_file)

    return f"<h2>Avatars generated!</h2><p>/download/{ultimate_title.replace(Download Ultimate Avatar</a></p><p>/download/{worst_title.replace(Download Worst Avatar</a></p>"

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    return send_file(os.path.join("avatars_web_output", filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

