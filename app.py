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
        The avatar&apos;s expression, posture and colours will reflect the behaviours you write.
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
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
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
    """
    Analyse the behaviour text and derive visual traits:
    - mood: good / bad / neutral
    - energy: high / medium / low
    - openness: open / closed
    - reliability: high / low
    - warmth: warm / cold
    """
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

    # --- Mood baseline from profile type ---
    if profile == "ultimate":
        mood = "good"
    elif profile == "worst":
        mood = "bad"
    else:
        mood = "neutral"

    # Adjust mood from text
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

    # Openness: combination of mood, warmth
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
        "raw_text": text
    }


# =========================
# AVATAR DRAWING
# =========================

def draw_avatar_person(draw: ImageDraw.ImageDraw, box, traits):
    """
    Draw a semi-cartoon person inside the given box.
    box: (left, top, right, bottom)
    traits: dict from analyze_behaviours()
    """
    left, top, right, bottom = box
    width = right - left
    height = bottom - top
    cx = (left + right) // 2

    mood = traits["mood"]
    energy = traits["energy"]
    reliability = traits["reliability"]
    warmth = traits["warmth"]
    openness = traits["openness"]
    role = traits["role"]

    # --- Colour theme based on Boliden-ish palette ---
    # Base Boliden blue: #3C577C, lighter blue: #75A7D4
    if traits["profile"] == "ultimate" or mood == "good":
        base_bg = (227, 242, 235)      # soft greenish
        shirt_color = (60, 87, 124)    # Boliden blue
    elif traits["profile"] == "worst" or mood == "bad":
