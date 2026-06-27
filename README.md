# YouTube Kids Channel — Hệ thống tự động đăng video

## Cấu trúc dự án
```
youtube-auto/
├── config/
│   ├── credentials.json      ← Google OAuth credentials (TỰ TẠO)
│   ├── schedule.json         ← Lịch đăng 30 ngày
│   └── channel_config.json   ← Cấu hình kênh VN + EN
├── scheduler/
│   └── scheduler.py          ← Lên lịch đăng tự động
├── uploader/
│   └── uploader.py           ← Upload video lên YouTube
├── scripts/
│   ├── setup.sh              ← Cài đặt môi trường
│   └── generate_schedule.py  ← Tạo lịch 30 ngày tự động
├── videos_queue/             ← Thư mục chứa video chờ đăng
│   ├── vn/                   ← Video tiếng Việt
│   └── en/                   ← Video tiếng Anh
└── requirements.txt
```

## Bước 1: Thiết lập Google API
1. Vào https://console.cloud.google.com
2. Tạo project mới → "YouTube Kids Channel"
3. Enable "YouTube Data API v3"
4. Tạo OAuth 2.0 credentials → Download JSON
5. Đặt file tại: `config/credentials.json`

## Bước 2: Cài đặt
```bash
bash scripts/setup.sh
```

## Bước 3: Chạy scheduler
```bash
python scheduler/scheduler.py
```
