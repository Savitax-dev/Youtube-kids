"""
YouTube Kids Channel — Thumbnail Generator
Tạo 4 thumbnail chuẩn YouTube (1280×720) cho mỗi ngày
Dùng Pillow để vẽ nền gradient, emoji lớn, text đậm màu sắc

Chạy: python3 thumbnails/generate_thumbnails.py [ngay_bat_dau] [ngay_ket_thuc]
Ví dụ: python3 thumbnails/generate_thumbnails.py 1 7   → tạo ngày 1-7
        python3 thumbnails/generate_thumbnails.py        → tạo tất cả 30 ngày
"""

import sys, math, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR   = Path(__file__).parent.parent
THUMB_DIR  = BASE_DIR / "thumbnails"
FONT_DIR   = BASE_DIR / "thumbnails" / "fonts"
THUMB_DIR.mkdir(exist_ok=True)
FONT_DIR.mkdir(exist_ok=True)

W, H = 1280, 720  # YouTube thumbnail size chuẩn

# ── Bảng màu cho 4 slot ────────────────────────────────────────────────────────
SLOT_STYLES = {
    "slot1": {  # Bài hát VN — cam-đỏ năng động
        "bg_top":    (255, 107, 53),
        "bg_bot":    (255, 59,  48),
        "accent":    (255, 223, 0),
        "text_main": (255, 255, 255),
        "text_sub":  (255, 242, 180),
        "badge_bg":  (255, 223, 0),
        "badge_txt": (200, 50,  0),
        "label":     "🎵 NHẠC THIẾU NHI",
        "corner":    "VN",
    },
    "slot2": {  # Giáo dục EN — xanh dương tươi
        "bg_top":    (37,  99,  235),
        "bg_bot":    (16,  185, 129),
        "accent":    (250, 204, 21),
        "text_main": (255, 255, 255),
        "text_sub":  (186, 230, 253),
        "badge_bg":  (250, 204, 21),
        "badge_txt": (30,  64,  175),
        "label":     "⭐ KIDS SONG",
        "corner":    "EN",
    },
    "slot3": {  # Truyện VN — tím hồng ấm
        "bg_top":    (168, 85,  247),
        "bg_bot":    (236, 72,  153),
        "accent":    (167, 243, 208),
        "text_main": (255, 255, 255),
        "text_sub":  (233, 213, 255),
        "badge_bg":  (167, 243, 208),
        "badge_txt": (109, 40,  217),
        "label":     "📖 TRUYỆN CỔ TÍCH",
        "corner":    "VN",
    },
    "slot4": {  # Lullaby EN — xanh đêm dịu nhẹ
        "bg_top":    (30,  27,  75),
        "bg_bot":    (55,  48,  163),
        "accent":    (196, 181, 253),
        "text_main": (255, 255, 255),
        "text_sub":  (196, 181, 253),
        "badge_bg":  (196, 181, 253),
        "badge_txt": (30,  27,  75),
        "label":     "🌙 LULLABY",
        "corner":    "EN",
    },
}

# ── Dữ liệu 30 ngày: emoji + tiêu đề ngắn ─────────────────────────────────────
DAY_DATA = [
    {"theme":"Con Vật",      "emoji":"🐶🐱🐔", "short_vn":"BÀI HÁT CON VẬT",        "short_en":"ANIMALS SONG",          "short_s3":"CHÚ THỎ TRẮNG",         "short_s4":"GOODNIGHT STAR"},
    {"theme":"Số Đếm",       "emoji":"🔢⭐🎈", "short_vn":"ĐẾM SỐ 1→10",             "short_en":"COUNT 1 TO 20",         "short_s3":"BA CON LỢN NHỎ",        "short_s4":"TWINKLE STAR"},
    {"theme":"Màu Sắc",      "emoji":"🌈🎨✨", "short_vn":"MÀU SẮC CẦU VỒNG",        "short_en":"RAINBOW COLORS",        "short_s3":"BÉ HỌC VẼ",             "short_s4":"RAINBOW LULLABY"},
    {"theme":"Vệ Sinh",      "emoji":"🦷🧼💧", "short_vn":"ĐÁNH RĂNG THÔI!",         "short_en":"BRUSH YOUR TEETH",      "short_s3":"RỬA TAY SẠCH SẼ",       "short_s4":"BEDTIME ROUTINE"},
    {"theme":"Bảng Chữ Cái", "emoji":"🔤📚🌟", "short_vn":"BẢNG CHỮ CÁI",            "short_en":"ABC PHONICS",           "short_s3":"CHỮ CÁI BIẾT NÓI",      "short_s4":"ALPHABET LULLABY"},
    {"theme":"Xe Cộ",        "emoji":"🚗🚂✈️", "short_vn":"XE CỘ VUI NHỘN",          "short_en":"WHEELS ON THE BUS",     "short_s3":"CHUYẾN TÀU THẦN KỲ",    "short_s4":"TRANSPORT SONG"},
    {"theme":"Tuần 1",       "emoji":"⭐🎉🏆", "short_vn":"LIÊN KHÚC TUẦN 1",        "short_en":"BEST SONGS WEEK 1",     "short_s3":"TOP CỔ TÍCH TUẦN 1",    "short_s4":"SWEET DREAMS VOL.1"},
    {"theme":"Buổi Sáng",    "emoji":"☀️🌸🎶", "short_vn":"CHÀO BUỔI SÁNG",          "short_en":"GOOD MORNING SONG",     "short_s3":"THỂ DỤC SÁNG",          "short_s4":"MORNING LULLABY"},
    {"theme":"Rau Củ Quả",   "emoji":"🥕🍎🌿", "short_vn":"BÀI HÁT RAU CỦ",         "short_en":"FRUITS & VEGGIES",      "short_s3":"BÉ ĂN NGON",            "short_s4":"HEALTHY FOOD SONG"},
    {"theme":"Trường Học",   "emoji":"🏫📝✏️", "short_vn":"EM YÊU TRƯỜNG LỚP",       "short_en":"I LOVE SCHOOL",         "short_s3":"NGÀY ĐẦU ĐI HỌC",       "short_s4":"SCHOOL LULLABY"},
    {"theme":"Hình Học",     "emoji":"🔷🔴⬛", "short_vn":"CÁC HÌNH DẠNG",           "short_en":"SHAPES SONG",           "short_s3":"KHÁM PHÁ HÌNH HỌC",     "short_s4":"SHAPES LULLABY"},
    {"theme":"Thời Tiết",    "emoji":"🌦️❄️🌈", "short_vn":"4 MÙA TRONG NĂM",         "short_en":"WEATHER SONG",          "short_s3":"GIỌT MƯA NHỎ BÉ",       "short_s4":"RAINY LULLABY"},
    {"theme":"Gia Đình",     "emoji":"👨‍👩‍👧💝🏠","short_vn":"GIA ĐÌNH HẠNH PHÚC",      "short_en":"FAMILY LOVE SONG",     "short_s3":"SỰ TÍCH CÂY KHẾ",       "short_s4":"FAMILY GOODNIGHT"},
    {"theme":"Tuần 2",       "emoji":"🎊📊🚀", "short_vn":"LIÊN KHÚC TUẦN 2",        "short_en":"BEST 2 WEEKS SONGS",    "short_s3":"TOP CỔ TÍCH TUẦN 2",    "short_s4":"2 WEEKS LULLABY"},
    {"theme":"Safari",       "emoji":"🦁🐘🦒", "short_vn":"SAFARI THÚ RỪNG",         "short_en":"WILD ANIMALS SONG",     "short_s3":"THẢO NGUYÊN PHIÊU LƯU", "short_s4":"JUNGLE LULLABY"},
    {"theme":"Vận Động",     "emoji":"💪🤸🎯", "short_vn":"VẬN ĐỘNG TAY CHÂN",       "short_en":"HEAD SHOULDERS SONG",   "short_s3":"YOGA CHO BÉ",           "short_s4":"EXERCISE LULLABY"},
    {"theme":"Nghệ Thuật",   "emoji":"🎨🖌️🌟", "short_vn":"TÔI YÊU VẼ TRANH",        "short_en":"I LOVE TO DRAW",        "short_s3":"CÂY BÚT THẦN",          "short_s4":"DREAMY ART LULLABY"},
    {"theme":"Đại Dương",    "emoji":"🐠🐙🌊", "short_vn":"ĐÁY ĐẠI DƯƠNG",           "short_en":"UNDER THE SEA",         "short_s3":"CHÚ CÁ BƠI LẠC",        "short_s4":"OCEAN WAVES LULLABY"},
    {"theme":"Vũ Trụ",       "emoji":"🚀⭐🪐", "short_vn":"KHÁM PHÁ VŨ TRỤ",         "short_en":"SPACE SONG",            "short_s3":"DU HÀNH VŨ TRỤ",        "short_s4":"STARRY NIGHT LULLABY"},
    {"theme":"Nghề Nghiệp",  "emoji":"👮🏥🚒", "short_vn":"CÁC NGHỀ NGHIỆP",         "short_en":"COMMUNITY HELPERS",     "short_s3":"BÁC SĨ NHÍ",            "short_s4":"DREAM JOBS LULLABY"},
    {"theme":"1h Đặc Biệt",  "emoji":"🎉🏆⭐", "short_vn":"1 GIỜ NHẠC THIẾU NHI",   "short_en":"1 HOUR KIDS SONGS",     "short_s3":"MARATHON CỔ TÍCH",       "short_s4":"3 HOURS LULLABY"},
    {"theme":"Trung Thu",    "emoji":"🏮🌕🦁", "short_vn":"TẾT TRUNG THU",           "short_en":"MOON FESTIVAL SONG",    "short_s3":"SỰ TÍCH CHÚ CUỘI",      "short_s4":"MOONLIGHT LULLABY"},
    {"theme":"Mùa Hè",       "emoji":"☀️🏖️🍦", "short_vn":"MÙA HÈ VUI NHỘN",         "short_en":"SUMMER FUN SONG",       "short_s3":"BÉ ĐI BIỂN",            "short_s4":"SUMMER LULLABY"},
    {"theme":"Côn Trùng",    "emoji":"🦋🐝🐛", "short_vn":"BÀI HÁT CÔN TRÙNG",       "short_en":"BUGS & INSECTS SONG",   "short_s3":"CHÚ ONG CHĂM CHỈ",      "short_s4":"GARDEN LULLABY"},
    {"theme":"An Toàn",      "emoji":"🚦🛡️✅", "short_vn":"KỸ NĂNG AN TOÀN",         "short_en":"SAFETY RULES SONG",     "short_s3":"LUẬT GIAO THÔNG",        "short_s4":"SAFE SLEEP LULLABY"},
    {"theme":"Câu Đố",       "emoji":"🧠💡🎯", "short_vn":"BÉ GIẢI ĐỐ THÔNG MINH",  "short_en":"FUN RIDDLES FOR KIDS",  "short_s3":"CUỘC THI TRÍ TUỆ",      "short_s4":"DREAMY RIDDLES"},
    {"theme":"Challenge",    "emoji":"🕺💃🎵", "short_vn":"CHALLENGE VẬN ĐỘNG",       "short_en":"KIDS DANCE CHALLENGE",  "short_s3":"THỎ VÀ RÙA CHẠY THI",   "short_s4":"ACTIVE LULLABY"},
    {"theme":"Âm Nhạc",      "emoji":"🎸🎹🎺", "short_vn":"NHẠC CỤ ÂM NHẠC",         "short_en":"INSTRUMENTS SONG",      "short_s3":"NHẠC CÔNG NHÍ",         "short_s4":"MUSIC BOX LULLABY"},
    {"theme":"Karaoke",      "emoji":"🎤🎶🌟", "short_vn":"BÉ HÁT KARAOKE",          "short_en":"KARAOKE KIDS VOL.1",    "short_s3":"LIÊN KHÚC CỔ TÍCH",     "short_s4":"SING ALONG LULLABY"},
    {"theme":"30 Ngày",      "emoji":"🏆🎊🎉", "short_vn":"2 GIỜ NHẠC THÁNG 1",      "short_en":"BEST 2H KIDS SONGS",    "short_s3":"TOP 10 CỔ TÍCH",        "short_s4":"5 HOURS LULLABY"},
]

SLOT_SHORT_KEYS = ["short_vn", "short_en", "short_s3", "short_s4"]
SLOTS           = ["slot1", "slot2", "slot3", "slot4"]


# ── Vẽ gradient background ────────────────────────────────────────────────────
def draw_gradient(img: Image.Image, top_color, bot_color):
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(top_color[0] * (1-t) + bot_color[0] * t)
        g = int(top_color[1] * (1-t) + bot_color[1] * t)
        b = int(top_color[2] * (1-t) + bot_color[2] * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


# ── Vẽ các vòng tròn trang trí ────────────────────────────────────────────────
def draw_decorations(draw: ImageDraw.Draw, accent_color):
    alpha = 30
    for cx, cy, r in [(W-120, 80, 160), (80, H-100, 120), (W//2, H+60, 200)]:
        r2 = r * 2
        bbox = [cx - r, cy - r, cx + r, cy + r]
        draw.ellipse(bbox, outline=(*accent_color, alpha), width=3)
    # Glow dots nhỏ
    for x, y, s in [(100,100,8),(W-150,H-80,6),(W-80,200,5),(200,H-60,7)]:
        draw.ellipse([x-s, y-s, x+s, y+s], fill=(*accent_color, 80))


# ── Load font (fallback DejaVu nếu không có custom font) ─────────────────────
def load_font(size: int, bold: bool = False):
    try:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        paths = [
            FONT_DIR / name,
            Path(f"/usr/share/fonts/truetype/dejavu/{name}"),
            Path(f"/usr/share/fonts/dejavu/{name}"),
        ]
        for p in paths:
            if p.exists():
                return ImageFont.truetype(str(p), size)
    except Exception:
        pass
    return ImageFont.load_default()


# ── Vẽ text có outline để nổi bật ────────────────────────────────────────────
def draw_text_outlined(draw, xy, text, font, fill, outline=(0,0,0), stroke=3):
    x, y = xy
    for dx in range(-stroke, stroke+1):
        for dy in range(-stroke, stroke+1):
            if dx != 0 or dy != 0:
                draw.text((x+dx, y+dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


# ── Tạo 1 thumbnail ──────────────────────────────────────────────────────────
def make_thumbnail(day: int, slot: str, title_short: str, emoji: str, theme: str) -> Image.Image:
    st   = SLOT_STYLES[slot]
    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # Background gradient
    draw_gradient(img, st["bg_top"], st["bg_bot"])

    # Decorative circles
    draw_decorations(draw, st["accent"])

    # Panel trắng bán trong suốt (center)
    panel = Image.new("RGBA", (W-120, H-140), (255,255,255,20))
    img.paste(panel, (60, 70), panel)

    draw2 = ImageDraw.Draw(img)

    # Label badge trên cùng
    font_badge = load_font(24, bold=True)
    badge_w    = 340
    badge_rect = [W//2 - badge_w//2, 32, W//2 + badge_w//2, 80]
    draw2.rounded_rectangle(badge_rect, radius=20, fill=st["badge_bg"])
    label_text = st["label"]
    bbox = draw2.textbbox((0,0), label_text, font=font_badge)
    tw = bbox[2] - bbox[0]
    draw2.text((W//2 - tw//2, 44), label_text, font=font_badge, fill=st["badge_txt"])

    # Emoji to lớn ở trái
    emoji_size  = 160
    try:
        # Vẽ emoji bằng PIL text (nếu có Noto Color Emoji)
        ef = load_font(emoji_size)
        draw2.text((60, H//2 - 90), emoji.split()[0], font=ef, fill=st["text_main"])
    except Exception:
        # Fallback: vẽ vòng tròn màu
        draw2.ellipse([60, H//2-90, 60+emoji_size, H//2-90+emoji_size], fill=(*st["accent"], 180))

    # Tiêu đề chính — text to, bold
    font_title = load_font(72, bold=True)
    font_sub   = load_font(36, bold=True)
    font_day   = load_font(22)

    # Wrap text nếu quá dài
    words = title_short.split()
    lines = []
    line  = ""
    for w in words:
        test = f"{line} {w}".strip()
        bb   = draw2.textbbox((0,0), test, font=font_title)
        if bb[2] - bb[0] > W - 300:
            if line:
                lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)

    y_text = H//2 - 80
    for ln in lines[:2]:
        draw_text_outlined(draw2, (250, y_text), ln, font_title,
                           fill=st["text_main"], outline=(0,0,0,200), stroke=3)
        bbox  = draw2.textbbox((0,0), ln, font=font_title)
        y_text += (bbox[3] - bbox[1]) + 8

    # Sub text — chủ đề ngày
    draw_text_outlined(draw2, (252, y_text + 10), theme.upper(), font_sub,
                       fill=st["text_sub"], outline=(0,0,0,160), stroke=2)

    # Ngày ở góc dưới trái
    draw2.rounded_rectangle([16, H-52, 110, H-12], radius=10, fill=(0,0,0,120))
    draw2.text((22, H-46), f"NGÀY {day}", font=font_day, fill=(255,255,255))

    # Corner badge VN/EN
    corner = st["corner"]
    draw2.rounded_rectangle([W-80, H-52, W-12, H-12], radius=10,
                            fill=st["badge_bg"])
    draw2.text((W-68, H-46), corner, font=load_font(22, bold=True), fill=st["badge_txt"])

    # Watermark kênh góc trên phải
    draw2.text((W-180, 18), "Kids Channel", font=load_font(20), fill=(255,255,255,160))

    return img


# ── Batch tạo thumbnails ──────────────────────────────────────────────────────
def generate_thumbnails(day_start: int = 1, day_end: int = 30):
    print(f"🖼️  Tạo thumbnail cho ngày {day_start}–{day_end}...")
    total = 0
    for day_idx in range(day_start - 1, day_end):
        day      = day_idx + 1
        day_data = DAY_DATA[day_idx]
        emoji    = day_data["emoji"]
        theme    = day_data["theme"]

        for slot_idx, slot in enumerate(SLOTS):
            key   = SLOT_SHORT_KEYS[slot_idx]
            title = day_data[key]
            img   = make_thumbnail(day, slot, title, emoji, theme)

            fname = f"day{day:02d}_slot{slot_idx+1}.jpg"
            out   = THUMB_DIR / fname
            img.save(str(out), "JPEG", quality=95, optimize=True)
            total += 1

        print(f"   ✅ Ngày {day:2d} ({theme}): 4 thumbnails")

    print(f"\n✅ Hoàn tất! {total} thumbnails tại: {THUMB_DIR}")


# ── Tạo Canva template guide ──────────────────────────────────────────────────
def generate_canva_guide():
    """Xuất file hướng dẫn Canva template dạng HTML."""
    styles_info = {
        "slot1": {"name":"Bài hát VN","colors":["#FF6B35","#FF3B30"],"accent":"#FFDF00","use":"Video nhạc tiếng Việt đăng 6:30 sáng"},
        "slot2": {"name":"Giáo dục EN","colors":["#2563EB","#10B981"],"accent":"#FACC15","use":"Video giáo dục tiếng Anh đăng 11:30"},
        "slot3": {"name":"Truyện VN","colors":["#A855F7","#EC4899"],"accent":"#A7F3D0","use":"Video truyện cổ tích tiếng Việt đăng 16:30"},
        "slot4": {"name":"Lullaby EN","colors":["#1E1B4B","#3730A3"],"accent":"#C4B5FD","use":"Video nhạc ngủ tiếng Anh đăng 20:00"},
    }

    canva_html = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>Canva Thumbnail Template Guide — YouTube Kids Channel</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0 }
body { font-family: -apple-system, sans-serif; background: #f8fafc; color: #1e293b; }
.page { max-width: 1000px; margin: 0 auto; padding: 2rem; }
h1 { font-size: 24px; margin-bottom: .5rem; }
.subtitle { color: #64748b; margin-bottom: 2rem; font-size: 14px; }
.grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 2rem; }
.card { background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
.card-preview { height: 180px; display: flex; align-items: center; justify-content: center; position: relative; }
.card-body { padding: 1.25rem; }
.card-body h2 { font-size: 16px; margin-bottom: .4rem; }
.card-body p  { font-size: 13px; color: #64748b; margin-bottom: .8rem; }
.colors { display: flex; gap: 8px; margin-bottom: .8rem; }
.color-chip { width: 32px; height: 32px; border-radius: 8px; border: 1px solid rgba(0,0,0,.1); }
.color-hex  { font-size: 11px; color: #64748b; text-align: center; margin-top: 2px; }
.spec-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px; }
.spec-item { background: #f8fafc; border-radius: 6px; padding: 6px 10px; }
.spec-label { color: #94a3b8; margin-bottom: 2px; }
.spec-val   { font-weight: 600; color: #1e293b; }
.guide-section { background: white; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
.guide-section h2 { font-size: 18px; margin-bottom: 1rem; }
.step { display: flex; gap: 12px; margin-bottom: 1rem; }
.step-num { width: 28px; height: 28px; border-radius: 50%; background: #6366f1; color: white; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; flex-shrink: 0; }
.step-content h3 { font-size: 14px; font-weight: 600; margin-bottom: 3px; }
.step-content p  { font-size: 13px; color: #64748b; line-height: 1.5; }
.preview-text { font-size: 22px; font-weight: 800; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,.5); text-align: center; padding: 12px; line-height: 1.2; }
.preview-badge { background: rgba(255,255,255,.25); border-radius: 20px; padding: 4px 12px; font-size: 11px; color: white; font-weight: 600; margin-bottom: 8px; }
.rule-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; }
.rule-card { background: #f8fafc; border-radius: 10px; padding: 1rem; }
.rule-card h4 { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.rule-card p  { font-size: 12px; color: #64748b; line-height: 1.5; }
</style>
</head>
<body>
<div class="page">
<h1>🎨 Canva Thumbnail Template Guide</h1>
<p class="subtitle">Hướng dẫn tạo thumbnail chuẩn YouTube Kids — 4 style cho 4 slot đăng mỗi ngày</p>

<div class="grid">
"""

    gradients = {
        "slot1": "linear-gradient(135deg, #FF6B35, #FF3B30)",
        "slot2": "linear-gradient(135deg, #2563EB, #10B981)",
        "slot3": "linear-gradient(135deg, #A855F7, #EC4899)",
        "slot4": "linear-gradient(135deg, #1E1B4B, #3730A3)",
    }
    labels = {
        "slot1":"🎵 NHẠC THIẾU NHI","slot2":"⭐ KIDS SONG",
        "slot3":"📖 TRUYỆN CỔ TÍCH","slot4":"🌙 LULLABY"
    }
    preview_titles = {
        "slot1":"BÀI HÁT CON VẬT 🐶","slot2":"ANIMALS SONG 🐾",
        "slot3":"BA CON LỢN NHỎ 🐷","slot4":"GOODNIGHT STAR ⭐"
    }

    for slot, info in styles_info.items():
        grad = gradients[slot]
        canva_html += f"""
  <div class="card">
    <div class="card-preview" style="background:{grad}">
      <div style="text-align:center">
        <div class="preview-badge">{labels[slot]}</div>
        <div class="preview-text">{preview_titles[slot]}</div>
      </div>
    </div>
    <div class="card-body">
      <h2>{info['name']}</h2>
      <p>{info['use']}</p>
      <div class="colors">
        {''.join(f'<div><div class="color-chip" style="background:{c}"></div><div class="color-hex">{c}</div></div>' for c in info['colors'] + [info['accent']])}
      </div>
      <div class="spec-grid">
        <div class="spec-item"><div class="spec-label">Kích thước</div><div class="spec-val">1280 × 720px</div></div>
        <div class="spec-item"><div class="spec-label">Font chữ</div><div class="spec-val">Nunito ExtraBold</div></div>
        <div class="spec-item"><div class="spec-label">Font size title</div><div class="spec-val">80–100px</div></div>
        <div class="spec-item"><div class="spec-label">Accent</div><div class="spec-val" style="color:{info['accent']};background:#1e293b;border-radius:4px;padding:2px 6px">{info['accent']}</div></div>
      </div>
    </div>
  </div>"""

    canva_html += """
</div>

<div class="guide-section">
  <h2>📋 Cách tạo thumbnail trong Canva (từng bước)</h2>
  <div class="step"><div class="step-num">1</div><div class="step-content"><h3>Tạo design mới</h3><p>Canva → "Create a design" → Custom size: <b>1280 × 720 px</b> → tên "YouTube Kids Thumbnail"</p></div></div>
  <div class="step"><div class="step-num">2</div><div class="step-content"><h3>Tạo Background gradient</h3><p>Chọn Background → Add element → "Gradient" → chọn 2 màu theo style table trên. Hoặc: thêm Rectangle full canvas → dùng "Gradient fill"</p></div></div>
  <div class="step"><div class="step-num">3</div><div class="step-content"><h3>Thêm emoji / nhân vật</h3><p>Upload PNG nhân vật hoạt hình (nền trong suốt) → kéo vào bên trái, chiếm 40% chiều rộng. Size: ~450px. <b>Quan trọng: nhân vật phải có biểu cảm cường điệu (mắt to, miệng cười rộng)</b></p></div></div>
  <div class="step"><div class="step-num">4</div><div class="step-content"><h3>Tiêu đề chính</h3><p>Font: <b>Nunito ExtraBold</b> hoặc <b>Baloo 2 ExtraBold</b> (Google Fonts). Size: 80–100px. Màu trắng + text shadow đen. Đặt bên phải nhân vật. Tối đa 3 từ mỗi dòng, 2 dòng.</p></div></div>
  <div class="step"><div class="step-num">5</div><div class="step-content"><h3>Badge nhãn slot</h3><p>Pill shape màu accent → text nhỏ (🎵 NHẠC THIẾU NHI / ⭐ KIDS SONG...). Đặt phía trên tiêu đề. Corner radius: 30px.</p></div></div>
  <div class="step"><div class="step-num">6</div><div class="step-content"><h3>Export</h3><p>File → Download → PNG hoặc JPG → Quality: 100%. Tên file: <b>day01_slot1.jpg</b> → đặt vào thư mục <code>thumbnails/</code></p></div></div>
</div>

<div class="guide-section">
  <h2>✅ 6 Quy tắc vàng thumbnail YouTube Kids</h2>
  <div class="rule-grid">
    <div class="rule-card"><h4>🎨 Màu sắc tương phản cao</h4><p>Nền đỏ/vàng + chữ trắng luôn nổi bật nhất trong feed. Tránh màu tối xỉn cho thumbnail thiếu nhi.</p></div>
    <div class="rule-card"><h4>👶 Mặt nhân vật chiếm 30%+</h4><p>Trẻ em bị thu hút bởi khuôn mặt. Nhân vật phải có biểu cảm rõ ràng: vui, ngạc nhiên, tò mò.</p></div>
    <div class="rule-card"><h4>📝 Tối đa 5 chữ lớn</h4><p>Thumbnail được xem ở màn hình nhỏ. Chỉ giữ tiêu đề ngắn gọn nhất, font cực to (80–100px).</p></div>
    <div class="rule-card"><h4>🔴 Màu viền / glow</h4><p>Thêm glow vàng/trắng xung quanh nhân vật để tách khỏi nền. Dùng "Drop Shadow" trong Canva.</p></div>
    <div class="rule-card"><h4>🌟 Sticker & sparkle</h4><p>Thêm 3–5 ngôi sao nhỏ, bong bóng, confetti xung quanh — tạo cảm giác vui nhộn, hấp dẫn trẻ em.</p></div>
    <div class="rule-card"><h4>🔁 A/B Test liên tục</h4><p>Làm 2 phiên bản thumbnail khác nhau cho cùng video. Dùng YouTube Studio → Analytics → Impressions CTR để so sánh sau 48h.</p></div>
  </div>
</div>

<div class="guide-section">
  <h2>🔗 Link Canva templates nhanh</h2>
  <p style="font-size:13px;color:#64748b;margin-bottom:1rem">Copy link sau vào trình duyệt để clone template về tài khoản Canva của bạn:</p>
  <ul style="list-style:none;display:flex;flex-direction:column;gap:8px">
    <li style="font-size:13px">🎵 <b>Slot 1 — Nhạc VN (đỏ-cam):</b> canva.com/design → Tạo mới với màu #FF6B35 / #FF3B30 / accent #FFDF00</li>
    <li style="font-size:13px">⭐ <b>Slot 2 — Giáo dục EN (xanh-xanh):</b> canva.com/design → Tạo mới với màu #2563EB / #10B981 / accent #FACC15</li>
    <li style="font-size:13px">📖 <b>Slot 3 — Truyện VN (tím-hồng):</b> canva.com/design → Tạo mới với màu #A855F7 / #EC4899 / accent #A7F3D0</li>
    <li style="font-size:13px">🌙 <b>Slot 4 — Lullaby EN (xanh đêm):</b> canva.com/design → Tạo mới với màu #1E1B4B / #3730A3 / accent #C4B5FD</li>
  </ul>
</div>

<p style="text-align:center;font-size:12px;color:#94a3b8;margin-top:2rem">YouTube Kids Channel — Thumbnail Style Guide v1.0</p>
</div></body></html>"""

    out_path = THUMB_DIR / "canva_template_guide.html"
    out_path.write_text(canva_html, encoding="utf-8")
    print(f"✅ Canva guide đã lưu: {out_path}")
    return out_path


if __name__ == "__main__":
    args = sys.argv[1:]
    day_start = int(args[0]) if len(args) >= 1 else 1
    day_end   = int(args[1]) if len(args) >= 2 else 30

    # Luôn tạo Canva guide
    generate_canva_guide()

    # Tạo thumbnails PNG
    generate_thumbnails(day_start, day_end)
