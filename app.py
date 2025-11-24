from flask import Flask, render_template_string, request, send_file
from PIL import Image, ImageDraw, ImageFont
import os

app = Flask(__name__)

# =========================
# HTML TEMPLATE (Boliden-style)
# =========================

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Boliden Mentorship Avatar Generator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background: #f4f7fa;
            color: #1f2933;
        }
        h1 {
            margin-bottom: 4px;
            color: #3C577C;
        }
        small {
            color: #6b7b8c;
        }
        textarea { width: 360px; height: 140px; }
        input[type=text] { width: 360px; }
        select { width: 180px; }
        .section {
            margin-bottom: 25px;
            padding: 15px 18px;
            background: #ffffff;
            border-radius: 10px;
            border: 1px solid #d0d7e2;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
        .section h3 {
            margin-top: 0;
            color: #3C577C;
        }
        .row {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .col {
            flex: 1 1 320px;
        }
        .submit-row {
            margin-top: 15px;
        }
        input[type=submit] {
            padding: 10px 18px;
            border-radius: 6px;
            border: none;
            background: #3C577C;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }
        input[type=submit]:hover {
            background: #304462;
        }
        .avatar-preview {
            max-width: 380px;
            border-radius: 8px;
            border: 1px solid #d0d7e2;
            margin-bottom: 10px;
            background: white;
        }
        a {
            color: #3C577C;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        hr {
            border: none;
            border-top: 1px solid #d0d7e2;
            margin: 10px 0 20px;
        }
    </style>
</head>
<body>
    <h1>Boliden Mentorship Avatar Generator</h1>
    <small>Metals for generations – behaviours for better mentoring.</small>
    <hr>

    <p>
        Enter a title, select <strong>role</strong> and <strong>profile type</strong>, and describe the behaviours.<br>
        The avatar's expression, posture and colours will reflect the behaviours you write.
    </p>

    <form method="POST" action="/generate">
        <div class="row">
            <div class="col">
                <div class="section">
                    <h3>Avatar A</h3>
                    <label>Title / Name:</label><br>
                    <input type="text" name="title_a" placeholder="e.g. The Ultimate Mentor"><br><br>

                    <label>Role:</label><br>
                    <select name="role_a">
                        <option value="mentor">Mentor</option>
                        <option value="trainee">Trainee</option>
                    </select><br><br>

                    <label>Profile type:</label><br>
                    <select name="profile_a">
                        <option value="ultimate">Ultimate</option>
                        <option value="worst">Worst</option>
                        <option value="mixed">Mixed / Not sure</option>
                    </select><br><br>

                    <label>Behaviours (one per line):</label><br>
                    <textarea name="behaviours_a"
                        placeholder="- Listens deeply
- Asks open questions
- Encourages reflection"></textarea>
                </div>
            </div>

            <div class="col">
                <div class="section">
                    <h3>Avatar B (optional)</h3>
                    <label>Title / Name:</label><br>
                    <input type="text" name="title_b" placeholder="e.g. The Worst Trainee"><br><br>

                    <label>Role:</label><br>
                    <select name="role_b">
                        <option value="mentor">Mentor</option>
                        <option value="trainee">Trainee</option>
                    </select><br><br>

                    <label>Profile type:</label><br>
                    <select name="profile_b">
                        <option value="ultimate">Ultimate</option>
                        <option value="worst">Worst</option>
                        <option value="mixed">Mixed / Not sure</option>
                    </select><br><br>

                    <label>Behaviours (one per line):</label><br>
                    <textarea name="behaviours_b"
                        placeholder="- Interrupts others
- Talks mostly about themselves
- Is often late or distracted"></textarea>
                </div>
            </div>
        </div>

        <div class="submit-row">
            <input type="submit" value="Generate Avatars">
        </div>
    </form>
</body>
</html>
"""

# =========================
# FONT & FILENAME HELPERS
# =========================

def get_font(size: int) -> ImageFont.ImageFont:
    """Try to load a TrueType font, otherwise fall back to the default."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size
            )
        except OSError:
            return ImageFont.load_default()


def safe_filename(title: str) -> str:
    if not title:
        title = "avatar"
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ "
    cleaned = "".join(c for c in title if c in allowed).strip()
    if not cleaned:
        cleaned = "avatar"
    return cleaned.replace(" ", "_") + ".png"


# =========================
# BEHAVIOUR ANALYSIS
# =========================

def analyze_behaviours(behaviours, role: str, profile: str):
    """Analyse behaviour text and derive visual traits."""
    text = ("\n".join(behaviours)).lower()

    positive_words = [
        "listen", "listens", "listening", "lyssnar",
        "empathy", "empathetic", "empatisk",
        "open", "öppen", "curious", "nyfiken",
        "support", "supportive", "stöd",
        "encourag", "uppmuntr",
        "present", "närvarande",
        "respect", "respekt",
        "honest", "transparent", "ärlig",
        "prepared", "förberedd", "forberedd", "reflect", "reflekter"
    ]

    negative_words = [
        "interrupt", "avbryter",
        "ego", "self-centered", "pratar om sig själv",
        "judge", "judging", "kritiserar", "klandrar",
        "blame", "shame",
        "cold", "kall",
        "arrogant", "hård", "kontrollerande",
        "sarcastic", "sarkastisk",
        "not listening", "doesn't listen", "doesnt listen", "lyssnar inte"
    ]

    high_energy_words = [
        "energetic", "engaged", "engagerad",
        "motivating", "inspiring", "inspirerar",
        "driven", "driv", "active"
    ]

    low_energy_words = [
        "tired", "trött", "passive", "passiv",
        "drained", "exhausted", "utmattad",
        "low energy", "nedstämd", "flat"
    ]

    low_reliability_words = [
        "late", "sen", "always late",
        "cancel", "ställer in", "no show",
        "doesn't show", "doesnt show",
        "comes unprepared", "unprepared", "ingen återkoppling"
    ]

    warmth_words = [
        "warm", "caring", "kind", "snäll",
        "safe", "trygg", "welcoming"
    ]
    cold_words = [
        "distant", "remote", "kall", "stiff", "stel",
        "detached"
    ]

    score_pos = sum(w in text for w in positive_words)
    score_neg = sum(w in text for w in negative_words)
    score_hi_e = sum(w in text for w in high_energy_words)
    score_lo_e = sum(w in text for w in low_energy_words)
    score_low_rel = sum(w in text for w in low_reliability_words)
    score_warm = sum(w in text for w in warmth_words)
    score_cold = sum(w in text for w in cold_words)

    # Mood baseline
    if profile == "ultimate":
        mood = "good"
    elif profile == "worst":
        mood = "bad"
    else:
        mood = "neutral"

    if score_pos > score_neg + 1:
        mood = "good"
    elif score_neg > score_pos + 1:
        mood = "bad"

    # Energy
    if score_hi_e > score_lo_e + 1:
        energy = "high"
    elif score_lo_e > score_hi_e + 1:
        energy = "low"
    else:
        energy = "medium"

    # Reliability
    reliability = "high"
    if score_low_rel > 0:
        reliability = "low"

    # Warmth
    if score_warm > score_cold:
        warmth = "warm"
    elif score_cold > score_warm:
        warmth = "cold"
    else:
        warmth = "neutral"

    # Openness
    if mood == "good" or warmth == "warm":
        openness = "open"
    elif mood == "bad" or warmth == "cold":
        openness = "closed"
    else:
        openness = "medium"

    return {
        "role": role,
        "profile": profile,
        "mood": mood,
        "energy": energy,
        "reliability": reliability,
        "warmth": warmth,
        "openness": openness,
    }


# =========================
# AVATAR DRAWING
# =========================

def draw_avatar_person(draw: ImageDraw.ImageDraw, box, traits):
    """
    Draw a more human-like cartoon person with face expression and body language
    based on the traits dict from analyze_behaviours().
    """
    left, top, right, bottom = box
    width = right - left
    height = bottom - top
    cx = (left + right) // 2

    mood = traits["mood"]          # good / bad / neutral
    energy = traits["energy"]      # high / medium / low
    reliability = traits["reliability"]
    warmth = traits["warmth"]
    openness = traits["openness"]
    role = traits["role"]

    # --- Colours (panel + clothes) ----------------------------------------
    if traits["profile"] == "ultimate" or mood == "good":
        panel_color = (222, 243, 235)   # soft green
        shirt_color = (60, 87, 144)     # Boliden blue
    elif traits["profile"] == "worst" or mood == "bad":
        panel_color = (252, 228, 228)   # soft red/pink
        shirt_color = (179, 65, 60)     # muted red
    else:
        panel_color = (228, 236, 246)   # soft blue
        shirt_color = (117, 167, 212)   # lighter blue

    if role == "trainee":
        # trainees lite ljusare topp
        shirt_color = tuple(min(255, c + 20) for c in shirt_color)

    pants_color = (44, 62, 80)
    if reliability == "low":
        pants_color = (127, 140, 141)

    skin_color = (244, 222, 200)
    hair_color = (70, 50, 40)
    if warmth == "cold":
        skin_color = (232, 220, 210)

    # --- Panel background --------------------------------------------------
    margin = 8
    draw.rectangle(
        (left + margin, top + margin, right - margin, bottom - margin),
        fill=panel_color,
        outline=(208, 214, 225),
        width=2,
    )

    # --- Head position: lägre vid låg energi/dåligt läge ------------------
    base_head_cy = top + int(height * 0.24)
    if energy == "low" or mood == "bad":
        head_cy = base_head_cy + int(height * 0.02)
    elif energy == "high" and mood == "good":
        head_cy = base_head_cy - int(height * 0.01)
    else:
        head_cy = base_head_cy

    head_radius = int(height * 0.13)
    head_box = (
        cx - head_radius,
        head_cy - head_radius,
        cx + head_radius,
        head_cy + head_radius,
    )
    draw.ellipse(head_box, fill=skin_color, outline=(90, 90, 90), width=2)

    # --- Hair: bara på övre delen av huvudet -------------------------------
    hair_height = int(head_radius * 1.0)
    hair_box = (
        cx - head_radius,
        head_cy - head_radius,
        cx + head_radius,
        head_cy - head_radius + hair_height,
    )
    draw.ellipse(hair_box, fill=hair_color, outline=hair_color)

    # --- Eyes --------------------------------------------------------------
    eye_y = head_cy - int(head_radius * 0.12)
    eye_offset_x = int(head_radius * 0.45)
    eye_r = 4

    if mood == "bad" or energy == "low":
        # halvstängda / trötta ögon – bara linjer
        for dx in (-eye_offset_x, eye_offset_x):
            draw.line(
                (cx + dx - eye_r, eye_y,
                 cx + dx + eye_r, eye_y),
                fill=(40, 40, 40),
                width=2
            )
    else:
        # öppna ögon
        for dx in (-eye_offset_x, eye_offset_x):
            draw.ellipse(
                (cx + dx - eye_r, eye_y - eye_r,
                 cx + dx + eye_r, eye_y + eye_r),
                fill=(40, 40, 40),
            )

    # --- Brows -------------------------------------------------------------
    brow_y = eye_y - 10
    brow_len = 24

    if mood == "good":
        # lite uppåt/vänlig
        left_brow = (cx - eye_offset_x - 6, brow_y + 2,
                     cx - eye_offset_x + brow_len, brow_y - 1)
        right_brow = (cx + eye_offset_x - brow_len, brow_y - 1,
                      cx + eye_offset_x + 6, brow_y + 2)
    elif mood == "bad":
        # arg / bekymrad – nedåtvänd
        left_brow = (cx - eye_offset_x - 6, brow_y - 1,
                     cx - eye_offset_x + brow_len, brow_y + 4)
        right_brow = (cx + eye_offset_x - brow_len, brow_y + 4,
                      cx + eye_offset_x + 6, brow_y - 1)
    else:
        # neutrala
        left_brow = (cx - eye_offset_x - 6, brow_y,
                     cx - eye_offset_x + brow_len, brow_y)
        right_brow = (cx + eye_offset_x - brow_len, brow_y,
                      cx + eye_offset_x + 6, brow_y)

    draw.line(left_brow, fill=(50, 40, 40), width=2)
    draw.line(right_brow, fill=(50, 40, 40), width=2)

    # --- Mouth -------------------------------------------------------------
    mouth_y = head_cy + int(head_radius * 0.45)
    mouth_w = int(head_radius * 0.9)

    if mood == "good":
        draw.arc(
            (cx - mouth_w, mouth_y - 18, cx + mouth_w, mouth_y + 8),
            start=200, end=340, fill=(90, 50, 50), width=3
        )
    elif mood == "bad":
        draw.arc(
            (cx - mouth_w, mouth_y - 4, cx + mouth_w, mouth_y + 24),
            start=20, end=160, fill=(90, 50, 50), width=3
        )
    else:
        draw.line(
            (cx - mouth_w // 2, mouth_y, cx + mouth_w // 2, mouth_y),
            fill=(90, 50, 50), width=3
        )

    # --- Neck --------------------------------------------------------------
    neck_w = head_radius // 2
    neck_h = int(height * 0.05)
    draw.rectangle(
        (cx - neck_w // 2, head_cy + head_radius,
         cx + neck_w // 2, head_cy + head_radius + neck_h),
        fill=skin_color,
        outline=skin_color,
    )

    # --- Torso & hållning --------------------------------------------------
    body_top = head_cy + head_radius + neck_h
    body_h = int(height * 0.30)
    body_w = int(width * 0.32)

    if energy == "high" and mood == "good":
        tilt = -4   # lite framåtlutad, engagerad
    elif energy == "low" or mood == "bad":
        tilt = 4    # lite “hängig”
    else:
        tilt = 0

    body_left = cx - body_w // 2 + tilt
    body_right = cx + body_w // 2 + tilt

    draw.rectangle(
        (body_left, body_top, body_right, body_top + body_h),
        fill=shirt_color,
        outline=(80, 80, 80),
        width=2,
    )

    # --- Arms --------------------------------------------------------------
    shoulder_y = body_top + 18
    arm_len = int(height * 0.23)
    arm_width = 10

    if openness == "open" and mood == "good":
        if energy == "high":
            # armar upp/ut – mycket positiv
            draw.line(
                (body_left + 5, shoulder_y,
                 body_left - 25, shoulder_y - arm_len + 15),
                fill=shirt_color, width=arm_width
            )
            draw.line(
                (body_right - 5, shoulder_y,
                 body_right + 25, shoulder_y - arm_len + 15),
                fill=shirt_color, width=arm_width
            )
        else:
            # öppna armar snett nedåt
            draw.line(
                (body_left + 5, shoulder_y,
                 body_left - 30, shoulder_y + arm_len),
                fill=shirt_color, width=arm_width
            )
            draw.line(
                (body_right - 5, shoulder_y,
                 body_right + 30, shoulder_y + arm_len),
                fill=shirt_color, width=arm_width
            )
    elif openness == "closed" or mood == "bad":
        # korsade armar
        cross_y = shoulder_y + 18
        draw.line(
            (body_left + 5, cross_y + 12,
             cx + 10, cross_y - 10),
            fill=shirt_color, width=arm_width
        )
        draw.line(
            (cx - 10, cross_y - 10,
             body_right - 5, cross_y + 12),
            fill=shirt_color, width=arm_width
        )
    else:
        # neutralt – armar rakt ned
        draw.line(
            (body_left + 5, shoulder_y,
             body_left + 5, shoulder_y + arm_len),
            fill=shirt_color, width=arm_width
        )
        draw.line(
            (body_right - 5, shoulder_y,
             body_right - 5, shoulder_y + arm_len),
            fill=shirt_color, width=arm_width
        )

    # --- Legs & shoes ------------------------------------------------------
    leg_top = body_top + body_h
    leg_len = int(height * 0.26)
    leg_gap = 18
    leg_w = 16

    leg_tilt = 3 if energy == "low" and mood == "bad" else 0

    # vänster ben
    draw.rectangle(
        (cx - leg_gap - leg_w + leg_tilt, leg_top,
         cx - leg_gap + leg_w + leg_tilt, leg_top + leg_len),
        fill=pants_color,
    )
    # höger ben
    draw.rectangle(
        (cx + leg_gap - leg_w + leg_tilt, leg_top,
         cx + leg_gap + leg_w + leg_tilt, leg_top + leg_len),
        fill=pants_color,
    )

    shoe_h = 14
    draw.rectangle(
        (cx - leg_gap - 24 + leg_tilt, leg_top + leg_len,
         cx - leg_gap + 28 + leg_tilt, leg_top + leg_len + shoe_h),
        fill=(30, 30, 30),
    )
    draw.rectangle(
        (cx + leg_gap - 28 + leg_tilt, leg_top + leg_len,
         cx + leg_gap + 24 + leg_tilt, leg_top + leg_len + shoe_h),
        fill=(30, 30, 30),
    )


# =========================
# CREATE IMAGE
# =========================

def create_avatar_image(title: str, behaviours, role: str, profile: str, filename: str):
    """Create a full avatar image with figure on the left and behaviours on the right."""
    img_w, img_h = 1100, 800
    img = Image.new("RGB", (img_w, img_h), (245, 247, 250))
    draw = ImageDraw.Draw(img)

    # Title
    title_font = get_font(38)
    draw.text((40, 30), title, font=title_font, fill=(34, 46, 80))

    # Subtitle
    subtitle_font = get_font(20)
    subtitle = f"{role.capitalize()} - {profile.capitalize()} profile"
    draw.text((40, 70), subtitle, font=subtitle_font, fill=(90, 104, 128))

    # Traits & avatar
    traits = analyze_behaviours(behaviours, role, profile)
    avatar_box = (40, 110, 460, img_h - 40)
    draw_avatar_person(draw, avatar_box, traits)

    # Behaviours on right side
    text_left = 500
    text_top = 130
    max_width = img_w - text_left - 40
    behaviour_font = get_font(24)
    line_spacing = 32
    y = text_top

    if behaviours:
        for b in behaviours:
            b = b.strip()
            if not b:
                continue
            words = b.split()
            line = ""
            for w in words:
                test_line = (line + " " + w).strip()
                # Pillow 10+: use textbbox instead of textsize
                bbox = draw.textbbox((0, 0), test_line, font=behaviour_font)
                w_width = bbox[2] - bbox[0]
                if w_width > max_width and line:
                    draw.text((text_left, y), "• " + line,
                              font=behaviour_font, fill=(20, 20, 20))
                    y += line_spacing
                    line = w
                else:
                    line = test_line
            if line:
                draw.text((text_left, y), "• " + line,
                          font=behaviour_font, fill=(20, 20, 20))
                y += line_spacing
    else:
        draw.text((text_left, y), "No behaviours entered.",
                  font=behaviour_font, fill=(120, 120, 120))

    img.save(filename)


# =========================
# FLASK ROUTES
# =========================

@app.route("/", methods=["GET"])
def index():
    return render_template_string(html_template)


@app.route("/generate", methods=["POST"])
def generate():
    output_folder = "avatars_web_output"
    os.makedirs(output_folder, exist_ok=True)

    result_blocks = []

    # Avatar A
    title_a = (request.form.get("title_a") or "").strip()
    role_a = (request.form.get("role_a") or "mentor").strip().lower()
    profile_a = (request.form.get("profile_a") or "mixed").strip().lower()
    behaviours_a_text = request.form.get("behaviours_a") or ""
    behaviours_a = behaviours_a_text.split("\n")

    if title_a or behaviours_a_text.strip():
        if not title_a:
            title_a = "Avatar_A"
        file_a_name = safe_filename(title_a)
        file_a_path = os.path.join(output_folder, file_a_name)
        create_avatar_image(title_a, behaviours_a, role_a, profile_a, file_a_path)
        block = f"""
        <div class='section'>
            <h2>{title_a}</h2>
            <img class="avatar-preview" src="/download/{file_a_name}?inline=1" alt="{title_a}">
            <br>
            <a href="/download/{file_a_name}">Download PNG</a>
        </div>
        """
        result_blocks.append(block)

    # Avatar B
    title_b = (request.form.get("title_b") or "").strip()
    role_b = (request.form.get("role_b") or "trainee").strip().lower()
    profile_b = (request.form.get("profile_b") or "mixed").strip().lower()
    behaviours_b_text = request.form.get("behaviours_b") or ""
    behaviours_b = behaviours_b_text.split("\n")

    if title_b or behaviours_b_text.strip():
        if not title_b:
            title_b = "Avatar_B"
        file_b_name = safe_filename(title_b)
        file_b_path = os.path.join(output_folder, file_b_name)
        create_avatar_image(title_b, behaviours_b, role_b, profile_b, file_b_path)
        block = f"""
        <div class='section'>
            <h2>{title_b}</h2>
            <img class="avatar-preview" src="/download/{file_b_name}?inline=1" alt="{title_b}">
            <br>
            <a href="/download/{file_b_name}">Download PNG</a>
        </div>
        """
        result_blocks.append(block)

    if not result_blocks:
        return """
        <h2>No avatars generated</h2>
        <p>Please go back and enter at least a title or behaviours.</p>
        <p><a href="/">Back</a></p>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Generated Avatars – Boliden Mentorship</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f4f7fa; color: #1f2933; }}
            .section {{
                margin-bottom: 20px;
                padding: 15px 18px;
                background: #ffffff;
                border-radius: 10px;
                border: 1px solid #d0d7e2;
                box-shadow: 0 2px 4px rgba(0,0,0,0.03);
            }}
            .avatar-preview {{
                max-width: 380px;
                border-radius: 8px;
                border: 1px solid #d0d7e2;
                background: white;
            }}
            a {{ color: #3C577C; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>Generated Avatars</h1>
        {''.join(result_blocks)}
        <p><a href="/">Create more avatars</a></p>
    </body>
    </html>
    """
    return html


@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    filepath = os.path.join("avatars_web_output", filename)
    if not os.path.exists(filepath):
        return "File not found", 404

    inline = request.args.get("inline")
    if inline:
        return send_file(filepath, mimetype="image/png")
    else:
        return send_file(filepath, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
