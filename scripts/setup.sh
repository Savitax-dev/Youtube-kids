#!/bin/bash
# ── Setup script cho YouTube Kids Channel Automation ──────────────────────────

echo "🚀 Cài đặt YouTube Kids Channel Automation..."
echo ""

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 chưa được cài. Vui lòng cài tại https://python.org"
    exit 1
fi

echo "✅ Python: $(python3 --version)"

# Cài thư viện
echo ""
echo "📦 Cài đặt thư viện Python..."
pip3 install -r requirements.txt

# Tạo thư mục cần thiết
echo ""
echo "📁 Tạo cấu trúc thư mục..."
mkdir -p videos_queue/vn
mkdir -p videos_queue/en
mkdir -p thumbnails
mkdir -p config
mkdir -p logs

# Tạo lịch đầy đủ 30 ngày
echo ""
echo "📅 Tạo lịch 30 ngày..."
python3 scripts/generate_schedule.py

echo ""
echo "════════════════════════════════════════════"
echo "✅ Cài đặt hoàn tất!"
echo ""
echo "📋 BƯỚC TIẾP THEO:"
echo "   1. Tải credentials.json từ Google Cloud Console"
echo "      → Đặt tại: config/credentials.json"
echo ""
echo "   2. Đặt video vào thư mục:"
echo "      → videos_queue/vn/  (video tiếng Việt)"
echo "      → videos_queue/en/  (video tiếng Anh)"
echo "      → Xem danh sách filename tại: config/filenames_to_produce.txt"
echo ""
echo "   3. Test dry run (không upload thực):"
echo "      python3 uploader/uploader.py --dry-run"
echo ""
echo "   4. Upload thực và bật scheduler:"
echo "      python3 scheduler/scheduler.py"
echo ""
echo "   💡 Để chạy nền (không tắt khi đóng terminal):"
echo "      nohup python3 scheduler/scheduler.py > logs/scheduler.log 2>&1 &"
echo "════════════════════════════════════════════"

echo ""
echo "   5. Tạo 120 thumbnails cho 30 ngày:"
echo "      python3 thumbnails/generate_thumbnails.py"
echo ""
echo "   6. Xem báo cáo tuần (sau khi kênh hoạt động):"
echo "      python3 analytics/weekly_report.py 1        # Tuần 1 thực tế"
echo "      python3 analytics/weekly_report.py 1 --mock # Test với dữ liệu mẫu"
