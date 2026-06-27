#!/usr/bin/env python3
"""
Công cụ chuẩn bị GitHub Actions Secret
Chạy 1 lần trên máy tính của bạn, sau đó không cần máy nữa.

Bước 1: Chạy script này để lấy token base64
Bước 2: Copy kết quả vào GitHub Secrets
Bước 3: Push code lên GitHub → xong, không cần máy nữa!
"""

import pickle, base64, sys, json
from pathlib import Path

BASE_DIR   = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
TOKEN_FILE = CONFIG_DIR / "token.pickle"


def export_token_to_base64():
    """Xuất token.pickle thành chuỗi base64 để paste vào GitHub Secret."""
    if not TOKEN_FILE.exists():
        print("❌ Chưa có token.pickle")
        print("   → Chạy uploader/uploader.py một lần để tạo token trước")
        return None

    with open(TOKEN_FILE, "rb") as f:
        raw = f.read()
    encoded = base64.b64encode(raw).decode("utf-8")

    out_file = CONFIG_DIR / "token_b64.txt"
    out_file.write_text(encoded)

    print("=" * 60)
    print("✅ Token đã xuất thành công!")
    print()
    print("📋 HƯỚNG DẪN SETUP GITHUB ACTIONS:")
    print()
    print("1. Vào repo GitHub của bạn")
    print("   Settings → Secrets and variables → Actions")
    print("   → New repository secret")
    print()
    print("2. Tạo secret tên: YOUTUBE_TOKEN_B64")
    print("   Value: (nội dung file config/token_b64.txt)")
    print(f"   File: {out_file}")
    print()
    print("3. Tạo thêm 2 secrets cho Google Drive:")
    print("   GDRIVE_FOLDER_VN = (folder ID Google Drive chứa video VN)")
    print("   GDRIVE_FOLDER_EN = (folder ID Google Drive chứa video EN)")
    print()
    print("   Cách lấy folder ID:")
    print("   Mở Google Drive → vào thư mục → copy ID từ URL:")
    print("   https://drive.google.com/drive/folders/[FOLDER_ID_Ở_ĐÂY]")
    print()
    print("4. Push code lên GitHub:")
    print("   git add .")
    print("   git commit -m 'Setup YouTube Kids Channel automation'")
    print("   git push")
    print()
    print("5. Kiểm tra Actions tab trên GitHub")
    print("   → Workflow sẽ tự chạy đúng giờ VN mỗi ngày")
    print("=" * 60)

    return encoded


def generate_gdrive_setup_guide():
    """Tạo hướng dẫn cách tổ chức video trên Google Drive."""
    print()
    print("📁 CẤU TRÚC GOOGLE DRIVE ĐỀ XUẤT:")
    print()
    print("YouTube Kids Channel/")
    print("├── videos_vn/          ← GDRIVE_FOLDER_VN")
    print("│   ├── ngay01_slot1_vn.mp4")
    print("│   ├── ngay01_slot3_vn.mp4")
    print("│   ├── ngay02_slot1_vn.mp4")
    print("│   └── ... (60 file video VN)")
    print("└── videos_en/          ← GDRIVE_FOLDER_EN")
    print("    ├── ngay01_slot2_en.mp4")
    print("    ├── ngay01_slot4_en.mp4")
    print("    ├── ngay02_slot2_en.mp4")
    print("    └── ... (60 file video EN)")
    print()

    # Xuất danh sách file cần upload lên Drive
    schedule_file = CONFIG_DIR / "schedule_full_30days.json"
    if schedule_file.exists():
        with open(schedule_file) as f:
            schedule = json.load(f)

        vn_files = []
        en_files = []
        for day in schedule:
            for v in day["videos"]:
                if v["channel"] == "vn":
                    vn_files.append(v["filename"])
                else:
                    en_files.append(v["filename"])

        out = CONFIG_DIR / "gdrive_upload_list.txt"
        with open(out, "w") as f:
            f.write("# Upload lên Google Drive folder videos_vn/\n")
            for fn in vn_files:
                f.write(f"videos_vn/{fn}\n")
            f.write("\n# Upload lên Google Drive folder videos_en/\n")
            for fn in en_files:
                f.write(f"videos_en/{fn}\n")

        print(f"📋 Danh sách file cần upload Drive: {out}")
        print(f"   Tổng: {len(vn_files)} file VN + {len(en_files)} file EN")


def check_github_actions_quota():
    """Tính toán quota GitHub Actions sẽ dùng."""
    print()
    print("📊 TÍNH TOÁN GITHUB ACTIONS QUOTA:")
    print()
    print("   Free tier: 2,000 phút/tháng")
    print()
    print("   Mỗi lần chạy ≈ 3–5 phút (tải video + upload YouTube)")
    print("   4 lần/ngày × 30 ngày = 120 lần/tháng")
    print("   120 × 4 phút = 480 phút/tháng")
    print()
    print("   ✅ 480/2000 = 24% quota — rất thoải mái!")
    print("   ✅ Không cần trả tiền trong 30 ngày đầu")
    print()


if __name__ == "__main__":
    print("🔧 Chuẩn bị chuyển sang GitHub Actions...")
    print()
    export_token_to_base64()
    generate_gdrive_setup_guide()
    check_github_actions_quota()

    print()
    print("🎉 Sau khi hoàn thành setup, bạn có thể TẮT MÁY TÍNH!")
    print("   GitHub Actions sẽ tự động đăng video 4 lần/ngày")
    print("   suốt 30 ngày mà không cần bất kỳ can thiệp nào.")
