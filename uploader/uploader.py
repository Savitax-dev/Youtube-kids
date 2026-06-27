"""
YouTube Kids Channel — Uploader tự động
Sử dụng YouTube Data API v3 để upload và lên lịch video
"""

import os
import json
import time
import pickle
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pytz
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ── Cấu hình logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("upload_log.txt", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ── Đường dẫn ─────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent.parent
CONFIG_DIR   = BASE_DIR / "config"
VIDEOS_DIR   = BASE_DIR / "videos_queue"
TOKEN_FILE   = CONFIG_DIR / "token.pickle"
CREDS_FILE   = CONFIG_DIR / "credentials.json"
CHANNEL_CFG  = CONFIG_DIR / "channel_config.json"
SCHEDULE_FILE= CONFIG_DIR / "schedule.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]

YOUTUBE_CATEGORY_EDUCATION = "26"  # Education category


# ── OAuth helper ──────────────────────────────────────────────────────────────
def get_authenticated_service():
    """Xác thực OAuth 2.0 và trả về YouTube service object."""
    creds = None

    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            log.info("Token đã được refresh tự động.")
        else:
            if not CREDS_FILE.exists():
                raise FileNotFoundError(
                    f"Không tìm thấy {CREDS_FILE}. "
                    "Vui lòng tải credentials.json từ Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
            log.info("Đã xác thực thành công lần đầu.")

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)


# ── Tính thời gian publish ────────────────────────────────────────────────────
def get_publish_time(date_offset: int, slot_time: str, timezone: str = "Asia/Ho_Chi_Minh") -> str:
    """
    Tính thời gian đăng video theo múi giờ Việt Nam.
    Trả về chuỗi ISO 8601 để YouTube API dùng.
    
    Ví dụ: date_offset=0, slot_time="06:30" → ngày mai 06:30 VN
    """
    tz = pytz.timezone(timezone)
    # Bắt đầu từ ngày mai để có thời gian chuẩn bị
    start_date = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date += timedelta(days=1)  # Bắt đầu từ ngày mai

    target_date = start_date + timedelta(days=date_offset)
    hour, minute = map(int, slot_time.split(":"))
    target_datetime = target_date.replace(hour=hour, minute=minute, second=0)

    # Convert sang UTC cho YouTube API
    utc_time = target_datetime.astimezone(pytz.utc)
    return utc_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")


# ── Upload 1 video ─────────────────────────────────────────────────────────────
def upload_video(
    youtube,
    video_path: str,
    title: str,
    description: str,
    tags: list,
    category_id: str = YOUTUBE_CATEGORY_EDUCATION,
    made_for_kids: bool = True,
    privacy: str = "private",
    publish_at: Optional[str] = None,
    thumbnail_path: Optional[str] = None,
) -> Optional[str]:
    """
    Upload video lên YouTube.
    
    Args:
        youtube: YouTube service đã xác thực
        video_path: Đường dẫn file video
        title: Tiêu đề video
        description: Mô tả video
        tags: Danh sách tags
        made_for_kids: True cho kênh thiếu nhi (bắt buộc để tuân thủ COPPA)
        privacy: "private" | "public" | "unlisted"
        publish_at: ISO 8601 string — nếu có sẽ lên lịch đăng
        thumbnail_path: Đường dẫn thumbnail (tùy chọn)
    
    Returns:
        video_id nếu thành công, None nếu lỗi
    """
    if not Path(video_path).exists():
        log.error(f"Không tìm thấy file video: {video_path}")
        return None

    # Nếu có publish_at thì đặt privacy = "private" để YouTube
    # tự động chuyển sang public đúng giờ
    status_dict = {
        "privacyStatus": "private" if publish_at else privacy,
        "selfDeclaredMadeForKids": made_for_kids,
    }
    if publish_at:
        status_dict["publishAt"] = publish_at

    body = {
        "snippet": {
            "title": title[:100],           # YouTube giới hạn 100 ký tự
            "description": description[:5000],
            "tags": tags[:500],             # YouTube giới hạn 500 tags
            "categoryId": category_id,
            "defaultLanguage": "vi" if "thiếu nhi" in title.lower() else "en",
        },
        "status": status_dict,
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/*",
        resumable=True,          # Resumable upload — tránh lỗi mạng
        chunksize=1024 * 1024 * 5,  # 5MB mỗi chunk
    )

    log.info(f"Bắt đầu upload: {title}")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    video_id = None
    retry_count = 0
    max_retries = 3

    while True:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                log.info(f"  Upload tiến độ: {progress}%")
            if response:
                video_id = response["id"]
                log.info(f"✅ Upload thành công! Video ID: {video_id}")
                log.info(f"   URL: https://youtu.be/{video_id}")
                break
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                retry_count += 1
                if retry_count > max_retries:
                    log.error(f"❌ Upload thất bại sau {max_retries} lần retry")
                    return None
                wait = 2 ** retry_count
                log.warning(f"Lỗi server, thử lại sau {wait}s... (lần {retry_count})")
                time.sleep(wait)
            else:
                log.error(f"❌ HTTP Error {e.resp.status}: {e.content}")
                return None

    # Upload thumbnail nếu có
    if video_id and thumbnail_path and Path(thumbnail_path).exists():
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            ).execute()
            log.info(f"✅ Thumbnail đã được set cho video {video_id}")
        except HttpError as e:
            log.warning(f"⚠️  Không thể set thumbnail: {e}")

    return video_id


# ── Upload theo lịch ──────────────────────────────────────────────────────────
def upload_schedule(dry_run: bool = False):
    """
    Đọc schedule.json và upload tất cả video theo lịch.
    
    Args:
        dry_run: Nếu True, chỉ in ra thông tin, không upload thực sự
    """
    # Load cấu hình
    with open(CHANNEL_CFG, encoding="utf-8") as f:
        channel_cfg = json.load(f)
    with open(SCHEDULE_FILE, encoding="utf-8") as f:
        schedule = json.load(f)

    upload_times = channel_cfg["upload_times"]
    timezone     = channel_cfg["timezone"]

    # Xác thực (chỉ 1 lần cho cả session)
    youtube = None
    if not dry_run:
        youtube = get_authenticated_service()
        log.info("✅ Đã kết nối YouTube API thành công")

    total = 0
    success = 0

    for day_data in schedule:
        day_num      = day_data["day"]
        date_offset  = day_data["date_offset"]
        theme        = day_data["theme"]
        log.info(f"\n{'='*60}")
        log.info(f"📅 Ngày {day_num}: {theme}")

        for video in day_data["videos"]:
            total += 1
            slot       = video["slot"]
            channel    = video["channel"]
            filename   = video["filename"]
            ch_lang    = channel_cfg["channels"][channel]

            # Tìm file video
            video_dir  = VIDEOS_DIR / channel
            video_path = str(video_dir / filename)

            # Lấy cấu hình channel
            tags  = list(set(video.get("tags", []) + ch_lang["default_tags"]))
            priv  = ch_lang["default_privacy"]
            kids  = ch_lang["made_for_kids"]

            # Tính thời gian đăng
            slot_time    = upload_times[slot]
            publish_time = get_publish_time(date_offset, slot_time, timezone)

            # Thumbnail
            thumb = None
            if "thumbnail" in video:
                thumb_path = str(BASE_DIR / video["thumbnail"])
                thumb = thumb_path if Path(thumb_path).exists() else None

            log.info(
                f"  📹 [{channel.upper()}] {video['title'][:50]}...\n"
                f"     File   : {filename}\n"
                f"     Đăng lúc: {publish_time} (slot {slot})"
            )

            if dry_run:
                log.info("     [DRY RUN - không upload thực]")
                success += 1
                continue

            # Kiểm tra file tồn tại
            if not Path(video_path).exists():
                log.warning(f"  ⚠️  File chưa có, bỏ qua: {video_path}")
                continue

            vid_id = upload_video(
                youtube=youtube,
                video_path=video_path,
                title=video["title"],
                description=video["description"],
                tags=tags,
                made_for_kids=kids,
                privacy=priv,
                publish_at=publish_time,
                thumbnail_path=thumb,
            )

            if vid_id:
                success += 1
                # Lưu mapping video_id
                _save_upload_record(day_num, video["slot"], channel, vid_id, publish_time)
            
            # Chờ 3 giây giữa các video để tránh quota
            time.sleep(3)

    log.info(f"\n{'='*60}")
    log.info(f"📊 Kết quả: {success}/{total} video đã upload thành công")


def _save_upload_record(day: int, slot: str, channel: str, video_id: str, publish_at: str):
    """Lưu lịch sử upload để theo dõi."""
    record_file = BASE_DIR / "upload_history.json"
    records = []
    if record_file.exists():
        with open(record_file, encoding="utf-8") as f:
            records = json.load(f)

    records.append({
        "day": day,
        "slot": slot,
        "channel": channel,
        "video_id": video_id,
        "publish_at": publish_at,
        "uploaded_at": datetime.now().isoformat(),
        "url": f"https://youtu.be/{video_id}"
    })

    with open(record_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        log.info("🔍 Chạy ở chế độ DRY RUN — không upload thực sự")
    upload_schedule(dry_run=dry_run)
