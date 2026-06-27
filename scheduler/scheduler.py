"""
YouTube Kids Channel — Scheduler tự động
Chạy nền, kiểm tra lịch và upload video đúng giờ.
Khởi động 1 lần, chạy suốt 30 ngày không cần can thiệp.
"""

import json
import time
import logging
import schedule
import subprocess
from datetime import datetime
from pathlib import Path

import pytz

BASE_DIR     = Path(__file__).parent.parent
CONFIG_DIR   = BASE_DIR / "config"
CHANNEL_CFG  = CONFIG_DIR / "channel_config.json"
SCHEDULE_FILE= CONFIG_DIR / "schedule.json"
HISTORY_FILE = BASE_DIR / "upload_history.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SCHEDULER] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(BASE_DIR / "scheduler_log.txt"), encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def get_today_day_number() -> int:
    """Tính ngày hiện tại trong lịch 30 ngày (bắt đầu từ ngày kênh ra mắt)."""
    launch_file = CONFIG_DIR / "launch_date.txt"
    if not launch_file.exists():
        # Lần đầu chạy — lưu ngày hôm nay làm ngày ra mắt
        today = datetime.now().strftime("%Y-%m-%d")
        launch_file.write_text(today)
        log.info(f"📅 Ngày ra mắt kênh: {today}")
        return 1

    launch_date_str = launch_file.read_text().strip()
    launch_date = datetime.strptime(launch_date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    diff = (today - launch_date).days + 1
    return min(diff, 30)  # Cap ở ngày 30


def get_already_uploaded() -> set:
    """Trả về set các key 'day-slot-channel' đã upload."""
    if not HISTORY_FILE.exists():
        return set()
    with open(HISTORY_FILE, encoding="utf-8") as f:
        history = json.load(f)
    return {f"{r['day']}-{r['slot']}-{r['channel']}" for r in history}


def run_upload_for_slot(slot_name: str):
    """Chạy uploader cho slot cụ thể trong ngày hôm nay."""
    from uploader.uploader import upload_video, get_authenticated_service, _save_upload_record

    day_num       = get_today_day_number()
    already_done  = get_already_uploaded()

    with open(SCHEDULE_FILE, encoding="utf-8") as f:
        schedule_data = json.load(f)

    with open(CHANNEL_CFG, encoding="utf-8") as f:
        channel_cfg = json.load(f)

    # Tìm ngày hôm nay trong lịch
    today_data = next((d for d in schedule_data if d["day"] == day_num), None)
    if not today_data:
        log.warning(f"Không tìm thấy lịch cho ngày {day_num}")
        return

    log.info(f"⏰ Đến giờ đăng slot {slot_name} — Ngày {day_num}: {today_data['theme']}")

    videos_this_slot = [v for v in today_data["videos"] if v["slot"] == slot_name]
    if not videos_this_slot:
        log.info(f"Không có video nào cho slot {slot_name} ngày {day_num}")
        return

    youtube = get_authenticated_service()

    for video in videos_this_slot:
        channel = video["channel"]
        key = f"{day_num}-{slot_name}-{channel}"

        if key in already_done:
            log.info(f"✅ Đã upload rồi, bỏ qua: {video['title'][:40]}...")
            continue

        video_path = str(BASE_DIR / "videos_queue" / channel / video["filename"])
        ch_cfg = channel_cfg["channels"][channel]
        tags   = list(set(video.get("tags", []) + ch_cfg["default_tags"]))

        # Đăng ngay lập tức (public) thay vì schedule
        vid_id = upload_video(
            youtube=youtube,
            video_path=video_path,
            title=video["title"],
            description=video["description"],
            tags=tags,
            made_for_kids=ch_cfg["made_for_kids"],
            privacy="public",        # Đăng ngay khi đến giờ
            publish_at=None,
            thumbnail_path=None,
        )

        if vid_id:
            _save_upload_record(day_num, slot_name, channel, vid_id, datetime.now().isoformat())
            log.info(f"🎉 Đã đăng: https://youtu.be/{vid_id}")

        time.sleep(3)


def setup_daily_schedule():
    """Thiết lập lịch đăng tự động mỗi ngày."""
    with open(CHANNEL_CFG, encoding="utf-8") as f:
        cfg = json.load(f)

    upload_times = cfg["upload_times"]
    tz_str = cfg["timezone"]

    log.info("🗓️  Thiết lập lịch tự động:")
    for slot, time_str in upload_times.items():
        schedule.every().day.at(time_str).do(run_upload_for_slot, slot_name=slot)
        log.info(f"   ✅ {slot}: {time_str} ({tz_str})")

    # Báo cáo analytics mỗi tối 21:00
    schedule.every().day.at("21:00").do(daily_analytics_report)
    log.info("   ✅ Analytics report: 21:00 hàng ngày")


def daily_analytics_report():
    """In báo cáo hàng ngày về trạng thái upload."""
    if not HISTORY_FILE.exists():
        return
    with open(HISTORY_FILE, encoding="utf-8") as f:
        history = json.load(f)

    today = datetime.now().strftime("%Y-%m-%d")
    today_uploads = [r for r in history if r["uploaded_at"].startswith(today)]

    log.info(f"\n📊 BÁO CÁO NGÀY {today}")
    log.info(f"   Đã đăng hôm nay: {len(today_uploads)} video")
    log.info(f"   Tổng cộng: {len(history)} video")

    for r in today_uploads:
        log.info(f"   ✅ [{r['channel'].upper()}] {r['url']}")


def run_scheduler():
    """Chạy scheduler — vòng lặp vô hạn kiểm tra mỗi phút."""
    log.info("🚀 YouTube Kids Channel Scheduler đã khởi động!")
    log.info(f"   Ngày hôm nay: Ngày {get_today_day_number()} trong lịch")
    log.info("   Nhấn Ctrl+C để dừng\n")

    setup_daily_schedule()

    while True:
        schedule.run_pending()
        time.sleep(30)  # Kiểm tra mỗi 30 giây


if __name__ == "__main__":
    # Kiểm tra nhanh hệ thống trước khi chạy
    log.info("🔍 Kiểm tra cấu hình...")

    if not CHANNEL_CFG.exists():
        log.error("❌ Không tìm thấy channel_config.json")
        exit(1)
    if not SCHEDULE_FILE.exists():
        log.error("❌ Không tìm thấy schedule.json")
        exit(1)
    if not (CONFIG_DIR / "credentials.json").exists():
        log.error("❌ Không tìm thấy credentials.json — Vui lòng xem README.md")
        exit(1)

    log.info("✅ Cấu hình OK — Bắt đầu scheduler")
    run_scheduler()
