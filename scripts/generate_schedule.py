"""
Tạo tự động toàn bộ schedule.json cho 30 ngày
Chạy một lần để sinh ra file lịch đầy đủ 120 video
"""

import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"

# ── Danh sách 30 ngày với chủ đề và video ────────────────────────────────────

SCHEDULE_TEMPLATE = [
    # Tuần 1
    {"day":1,  "theme":"Con vật",        "topic_vn":"Bài hát con vật đáng yêu",        "topic_en":"Animals Song for Kids",          "story":"Truyện: Chú thỏ trắng",          "lullaby":"Goodnight Little Star"},
    {"day":2,  "theme":"Số đếm",         "topic_vn":"Bé học đếm số từ 1 đến 10",       "topic_en":"Count 1 to 20 — Number Song",    "story":"Cổ tích: Ba con lợn nhỏ",        "lullaby":"Twinkle Twinkle Little Star"},
    {"day":3,  "theme":"Màu sắc",        "topic_vn":"Bài hát màu sắc cầu vồng",        "topic_en":"Colors of the Rainbow Song",     "story":"Bé học vẽ màu sắc",              "lullaby":"Rainbow Lullaby"},
    {"day":4,  "theme":"Vệ sinh",        "topic_vn":"Bài hát đánh răng buổi sáng",     "topic_en":"Brush Your Teeth Song",          "story":"Bé tập rửa tay sạch sẽ",         "lullaby":"Wash Hands Bedtime"},
    {"day":5,  "theme":"Bảng chữ cái",  "topic_vn":"Bảng chữ cái tiếng Việt",         "topic_en":"ABC Song — Phonics for Kids",    "story":"Truyện chữ cái biết nói",        "lullaby":"Alphabet Lullaby A to Z"},
    {"day":6,  "theme":"Xe cộ",          "topic_vn":"Bài hát xe cộ vui nhộn",          "topic_en":"Wheels on the Bus + Vehicles",   "story":"Cổ tích: Chuyến tàu thần kỳ",   "lullaby":"Transport Songs Compilation"},
    {"day":7,  "theme":"Tổng kết tuần 1","topic_vn":"Liên khúc thiếu nhi tuần 1",      "topic_en":"Best Kids Songs Week 1",         "story":"Top truyện cổ tích tuần 1",      "lullaby":"Sweet Dreams Compilation Vol.1"},
    # Tuần 2
    {"day":8,  "theme":"Buổi sáng",      "topic_vn":"Bài hát chào buổi sáng",          "topic_en":"Good Morning Song for Kids",     "story":"Bé tập thể dục buổi sáng",       "lullaby":"Morning Routine Lullaby"},
    {"day":9,  "theme":"Rau củ quả",     "topic_vn":"Bài hát rau củ đáng yêu",         "topic_en":"Fruits & Vegetables Song",       "story":"Bé ăn ngon lớn khỏe",            "lullaby":"Healthy Food Lullaby"},
    {"day":10, "theme":"Trường học",     "topic_vn":"Bài hát em yêu trường lớp",       "topic_en":"I Love School Song",             "story":"Truyện: Ngày đầu đi học của Mít","lullaby":"School Day Lullaby"},
    {"day":11, "theme":"Hình học",       "topic_vn":"Bài hát các hình dạng",           "topic_en":"Shapes Song for Preschoolers",   "story":"Bé khám phá hình học",           "lullaby":"Shapes & Colors Lullaby"},
    {"day":12, "theme":"Thời tiết",      "topic_vn":"Bài hát 4 mùa trong năm",         "topic_en":"Weather Song — Sun Rain Snow",   "story":"Truyện: Giọt mưa nhỏ bé",       "lullaby":"Rainy Day Lullaby"},
    {"day":13, "theme":"Gia đình",       "topic_vn":"Bài hát gia đình hạnh phúc",      "topic_en":"Family Song — We Love You",     "story":"Cổ tích: Sự tích cây khế",       "lullaby":"Family Lullaby Good Night"},
    {"day":14, "theme":"Tổng kết tuần 2","topic_vn":"Liên khúc thiếu nhi Vol.2",       "topic_en":"2 Weeks of Kids Songs Best Of", "story":"Top 3 truyện cổ tích tuần 2",    "lullaby":"2 Weeks Lullaby Collection"},
    # Tuần 3
    {"day":15, "theme":"Safari",         "topic_vn":"Bài hát Safari — Thú rừng",       "topic_en":"Wild Animals Song — Safari",     "story":"Phiêu lưu đến thảo nguyên",      "lullaby":"Jungle Lullaby — Sleepy Safari"},
    {"day":16, "theme":"Vận động",       "topic_vn":"Bài hát vận động tay chân",       "topic_en":"Head Shoulders Knees and Toes", "story":"Yoga nhỏ cho bé yêu",            "lullaby":"Exercise & Relax Lullaby"},
    {"day":17, "theme":"Nghệ thuật",     "topic_vn":"Bài hát tôi yêu vẽ tranh",        "topic_en":"I Love to Draw — Art Song",     "story":"Cổ tích: Cây bút thần",          "lullaby":"Dreamy Art Lullaby"},
    {"day":18, "theme":"Đại dương",      "topic_vn":"Bài hát dưới đáy đại dương",      "topic_en":"Under the Sea Song for Kids",   "story":"Truyện: Chú cá nhỏ bơi lạc",    "lullaby":"Ocean Waves Lullaby"},
    {"day":19, "theme":"Vũ trụ",         "topic_vn":"Bài hát khám phá vũ trụ",         "topic_en":"Space Song — Planets & Stars",  "story":"Bé Nam và chuyến du hành vũ trụ","lullaby":"Starry Night Lullaby"},
    {"day":20, "theme":"Nghề nghiệp",    "topic_vn":"Bài hát các nghề nghiệp",         "topic_en":"Community Helpers Song",         "story":"Một ngày của bác sĩ nhí",        "lullaby":"Dream Jobs Lullaby"},
    {"day":21, "theme":"1 giờ đặc biệt", "topic_vn":"1 GIỜ nhạc thiếu nhi hay nhất",  "topic_en":"1 HOUR Kids Songs Collection",  "story":"Marathon truyện cổ tích 3 tuần", "lullaby":"3 Hours Lullaby for Deep Sleep"},
    # Tuần 4
    {"day":22, "theme":"Trung Thu",      "topic_vn":"Bài hát Tết Trung Thu",           "topic_en":"Moon Festival Song",             "story":"Sự tích Chú Cuội cung trăng",    "lullaby":"Moonlight Lullaby"},
    {"day":23, "theme":"Mùa hè",         "topic_vn":"Bài hát mùa hè vui nhộn",         "topic_en":"Summer Fun Song",                "story":"Bé đi biển ngày hè",             "lullaby":"Summer Night Lullaby"},
    {"day":24, "theme":"Côn trùng",      "topic_vn":"Bài hát về côn trùng",            "topic_en":"Bugs and Insects Song",          "story":"Cổ tích: Chú ong vàng chăm chỉ","lullaby":"Garden Lullaby"},
    {"day":25, "theme":"An toàn",        "topic_vn":"Bài hát kỹ năng an toàn",         "topic_en":"Safety Rules for Kids",          "story":"Bé học luật giao thông",         "lullaby":"Safe & Sound Lullaby"},
    {"day":26, "theme":"Câu đố",         "topic_vn":"Bé giải đố thông minh",           "topic_en":"Fun Riddles for Kids",           "story":"Cuộc thi trí tuệ của các bé",    "lullaby":"Dreamy Riddles Lullaby"},
    {"day":27, "theme":"Challenge",      "topic_vn":"Challenge vận động cho bé",       "topic_en":"Kids Dance Challenge",           "story":"Cổ tích: Thỏ và Rùa chạy thi",  "lullaby":"Active Kids Lullaby"},
    {"day":28, "theme":"Âm nhạc",        "topic_vn":"Bài hát về các loại nhạc cụ",     "topic_en":"Musical Instruments Song",       "story":"Nhạc công nhí tài năng",         "lullaby":"Music Box Lullaby"},
    {"day":29, "theme":"Karaoke",        "topic_vn":"Bé hát karaoke thiếu nhi",        "topic_en":"Karaoke Kids Songs Vol.1",       "story":"Liên khúc truyện cổ tích tuần 4","lullaby":"Sing Along Lullaby"},
    {"day":30, "theme":"Tổng kết 30 ngày","topic_vn":"2 GIỜ nhạc thiếu nhi hay nhất tháng 1","topic_en":"BEST 2 Hours Kids Songs Month 1","story":"Top 10 truyện cổ tích tháng 1","lullaby":"5 Hours Lullaby for Babies"},
]


def make_vn_description(title: str, day: int) -> str:
    return (
        f"{title}\n\n"
        f"✨ Phù hợp cho bé từ 2-10 tuổi\n"
        f"🎵 Giai điệu vui nhộn dễ nhớ\n"
        f"🌈 Hoạt hình màu sắc rực rỡ\n"
        f"📚 Nội dung giáo dục bổ ích\n\n"
        f"👍 Like và SUBSCRIBE để xem thêm nhiều video bổ ích!\n"
        f"🔔 Bật thông báo để không bỏ lỡ video mới mỗi ngày!\n\n"
        f"📋 Playlist: Nhạc Thiếu Nhi Hay Nhất | Kênh Thiếu Nhi VN\n\n"
        f"#thiếunhi #bàihátthi#unhi #hoạthình #nhạcthiếunhi #trẻem #giáodụcthiếunhi"
    )

def make_en_description(title: str, day: int) -> str:
    return (
        f"{title}\n\n"
        f"✨ Perfect for children ages 2-10\n"
        f"🎵 Catchy melody children love\n"
        f"🌈 Bright colorful 3D animation\n"
        f"📚 Educational content for kids\n\n"
        f"👍 Like and SUBSCRIBE for more fun videos!\n"
        f"🔔 Turn on notifications — new video every day!\n\n"
        f"📋 Playlist: Best Kids Songs | Children's Animation Channel\n\n"
        f"#kidssongs #nurseryrhymes #kidsanimation #educationalkids #toddlersongs #childrensongs"
    )


def generate_full_schedule():
    """Sinh toàn bộ schedule.json 30 ngày (120 video)."""
    full_schedule = []

    for day_data in SCHEDULE_TEMPLATE:
        day    = day_data["day"]
        offset = day - 1
        theme  = day_data["theme"]

        vn_song_title = f"{day_data['topic_vn']} 🎵 | Nhạc Thiếu Nhi Vui Nhộn | Hoạt Hình"
        en_song_title = f"{day_data['topic_en']} 🎵 | Kids Songs | Children's Animation"
        vn_story_title = f"{day_data['story']} | Hoạt Hình Thiếu Nhi Việt Nam"
        en_lullaby_title = f"{day_data['lullaby']} 🌙 | Bedtime Lullaby for Kids | Sleep Music"

        videos = [
            {
                "slot": "slot1",
                "channel": "vn",
                "filename": f"ngay{day:02d}_slot1_vn.mp4",
                "title": vn_song_title[:100],
                "description": make_vn_description(vn_song_title, day),
                "tags": ["thiếu nhi", "bài hát thiếu nhi", "hoạt hình", theme.lower(),
                         day_data['topic_vn'].lower()[:30], "nhạc thiếu nhi"],
                "thumbnail": f"thumbnails/day{day:02d}_slot1.jpg"
            },
            {
                "slot": "slot2",
                "channel": "en",
                "filename": f"ngay{day:02d}_slot2_en.mp4",
                "title": en_song_title[:100],
                "description": make_en_description(en_song_title, day),
                "tags": ["kids songs", "nursery rhymes", "children animation", "educational kids",
                         theme.lower(), "toddler songs"],
                "thumbnail": f"thumbnails/day{day:02d}_slot2.jpg"
            },
            {
                "slot": "slot3",
                "channel": "vn",
                "filename": f"ngay{day:02d}_slot3_vn.mp4",
                "title": vn_story_title[:100],
                "description": make_vn_description(vn_story_title, day),
                "tags": ["truyện cổ tích", "hoạt hình thiếu nhi", "cổ tích việt nam",
                         theme.lower(), "truyện thiếu nhi"],
                "thumbnail": f"thumbnails/day{day:02d}_slot3.jpg"
            },
            {
                "slot": "slot4",
                "channel": "en",
                "filename": f"ngay{day:02d}_slot4_en.mp4",
                "title": en_lullaby_title[:100],
                "description": make_en_description(en_lullaby_title, day),
                "tags": ["lullaby", "bedtime songs", "kids sleep music", "nursery rhymes",
                         "baby lullaby", "sleep song for kids"],
                "thumbnail": f"thumbnails/day{day:02d}_slot4.jpg"
            }
        ]

        full_schedule.append({
            "day": day,
            "date_offset": offset,
            "theme": theme,
            "videos": videos
        })

    output = CONFIG_DIR / "schedule_full_30days.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(full_schedule, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã tạo schedule đầy đủ: {output}")
    print(f"   Tổng: {len(full_schedule)} ngày × 4 video = {len(full_schedule)*4} video")

    # Cũng in danh sách tên file cần sản xuất
    filenames_output = CONFIG_DIR / "filenames_to_produce.txt"
    with open(filenames_output, "w", encoding="utf-8") as f:
        f.write("# Danh sách TẤT CẢ file video cần sản xuất\n")
        f.write("# Đặt vào thư mục: videos_queue/vn/ hoặc videos_queue/en/\n\n")
        for day_entry in full_schedule:
            f.write(f"# === Ngày {day_entry['day']}: {day_entry['theme']} ===\n")
            for v in day_entry["videos"]:
                folder = v["channel"]
                f.write(f"videos_queue/{folder}/{v['filename']}\n")
            f.write("\n")

    print(f"✅ Danh sách filename: {filenames_output}")
    return full_schedule


if __name__ == "__main__":
    generate_full_schedule()
