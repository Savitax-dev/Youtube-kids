"""
YouTube Kids Channel — Báo cáo phân tích hàng tuần
Lấy dữ liệu từ YouTube Analytics API và xuất báo cáo HTML đầy đủ
Chạy mỗi Chủ Nhật lúc 22:00 hoặc thủ công: python3 analytics/weekly_report.py
"""

import os, json, pickle, sys
from datetime import datetime, timedelta
from pathlib import Path

import pytz
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

BASE_DIR    = Path(__file__).parent.parent
CONFIG_DIR  = BASE_DIR / "config"
REPORT_DIR  = BASE_DIR / "analytics" / "reports"
HISTORY_FILE= BASE_DIR / "upload_history.json"
TOKEN_FILE  = CONFIG_DIR / "token_analytics.pickle"
CREDS_FILE  = CONFIG_DIR / "credentials.json"
CHANNEL_CFG = CONFIG_DIR / "channel_config.json"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


# ── Auth ──────────────────────────────────────────────────────────────────────
def get_services():
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    youtube   = build("youtube",          "v3",         credentials=creds)
    analytics = build("youtubeAnalytics", "v2",         credentials=creds)
    return youtube, analytics


# ── Lấy channel ID ────────────────────────────────────────────────────────────
def get_channel_id(youtube):
    res = youtube.channels().list(part="id,snippet,statistics", mine=True).execute()
    items = res.get("items", [])
    if not items:
        return None, {}
    ch = items[0]
    return ch["id"], ch.get("statistics", {})


# ── Lấy danh sách video trong khoảng ngày ─────────────────────────────────────
def get_videos_in_range(youtube, channel_id: str, start_date: str, end_date: str):
    """Trả về list video được đăng trong khoảng start_date – end_date."""
    videos = []
    page_token = None
    while True:
        res = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            type="video",
            publishedAfter=f"{start_date}T00:00:00Z",
            publishedBefore=f"{end_date}T23:59:59Z",
            maxResults=50,
            pageToken=page_token,
            order="date",
        ).execute()

        for item in res.get("items", []):
            videos.append({
                "video_id":   item["id"]["videoId"],
                "title":      item["snippet"]["title"],
                "published":  item["snippet"]["publishedAt"][:10],
                "thumbnail":  item["snippet"]["thumbnails"]["medium"]["url"],
            })
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return videos


# ── Lấy stats từng video ──────────────────────────────────────────────────────
def get_video_stats(youtube, video_ids: list):
    """Lấy views, likes, comments, duration cho list video."""
    stats = {}
    # API chỉ cho 50 video mỗi lần
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        res = youtube.videos().list(
            part="statistics,contentDetails",
            id=",".join(batch)
        ).execute()
        for item in res.get("items", []):
            vid_id = item["id"]
            s = item.get("statistics", {})
            stats[vid_id] = {
                "views":    int(s.get("viewCount", 0)),
                "likes":    int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
                "duration": item["contentDetails"]["duration"],
            }
    return stats


# ── Lấy analytics tổng hợp từ YouTube Analytics API ─────────────────────────
def get_channel_analytics(analytics, channel_id: str, start_date: str, end_date: str):
    """Lấy metrics tổng hợp cho kênh trong khoảng thời gian."""
    try:
        res = analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,comments",
            dimensions="day",
            sort="day",
        ).execute()
        return res.get("rows", [])
    except Exception as e:
        print(f"⚠️  Analytics API lỗi: {e}")
        return []


def get_top_videos_analytics(analytics, channel_id: str, start_date: str, end_date: str):
    """Lấy top 20 video theo views trong tuần."""
    try:
        res = analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,likes",
            dimensions="video",
            sort="-views",
            maxResults=20,
        ).execute()
        return res.get("rows", [])
    except Exception as e:
        print(f"⚠️  Top videos analytics lỗi: {e}")
        return []


# ── Parse ISO duration ────────────────────────────────────────────────────────
def parse_duration(iso: str) -> int:
    """PT4M30S → 270 giây"""
    import re
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso)
    if not m:
        return 0
    h, mi, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + s


def fmt_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


# ── Tính toán summary ─────────────────────────────────────────────────────────
def compute_summary(daily_rows: list, video_stats: dict, videos: list) -> dict:
    total_views    = sum(int(r[1]) for r in daily_rows) if daily_rows else sum(v["views"] for v in video_stats.values())
    total_minutes  = sum(int(r[2]) for r in daily_rows) if daily_rows else 0
    total_subs_gain= sum(int(r[4]) for r in daily_rows) if daily_rows else 0
    total_subs_lost= sum(int(r[5]) for r in daily_rows) if daily_rows else 0
    total_likes    = sum(v["likes"]    for v in video_stats.values())
    total_comments = sum(v["comments"] for v in video_stats.values())
    total_videos   = len(videos)

    avg_views_per_video = total_views // total_videos if total_videos else 0
    net_subs = total_subs_gain - total_subs_lost

    # CTR proxy: likes / views
    like_ratio = (total_likes / total_views * 100) if total_views else 0
    # Avg watch time (từ daily rows)
    avg_watch  = (sum(int(r[3]) for r in daily_rows) // len(daily_rows)) if daily_rows else 0

    return {
        "total_views": total_views,
        "total_minutes": total_minutes,
        "total_videos": total_videos,
        "avg_views_per_video": avg_views_per_video,
        "net_subs": net_subs,
        "subs_gained": total_subs_gain,
        "subs_lost": total_subs_lost,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "like_ratio": round(like_ratio, 2),
        "avg_watch_seconds": avg_watch,
    }


# ── Xuất báo cáo HTML ─────────────────────────────────────────────────────────
def generate_html_report(
    week_num: int,
    start_date: str,
    end_date: str,
    summary: dict,
    videos: list,
    video_stats: dict,
    daily_rows: list,
    top_video_rows: list,
    channel_stats: dict,
) -> str:

    # Sắp xếp video theo views
    videos_with_stats = []
    for v in videos:
        s = video_stats.get(v["video_id"], {})
        videos_with_stats.append({**v, **s})
    videos_with_stats.sort(key=lambda x: x.get("views", 0), reverse=True)

    top5   = videos_with_stats[:5]
    flop5  = videos_with_stats[-5:] if len(videos_with_stats) >= 5 else []

    # Daily chart data
    daily_labels = json.dumps([r[0] for r in daily_rows])
    daily_views  = json.dumps([int(r[1]) for r in daily_rows])
    daily_subs   = json.dumps([int(r[4]) for r in daily_rows])

    # Top video rows table
    top_rows_html = ""
    for i, v in enumerate(videos_with_stats[:10], 1):
        views    = v.get("views", 0)
        likes    = v.get("likes", 0)
        comments = v.get("comments", 0)
        like_r   = f"{likes/views*100:.1f}%" if views else "—"
        badge    = ["🥇","🥈","🥉"][i-1] if i <= 3 else f"#{i}"
        top_rows_html += f"""
        <tr>
          <td style="text-align:center;font-weight:500">{badge}</td>
          <td style="max-width:300px;font-size:13px">{v['title'][:55]}{'…' if len(v['title'])>55 else ''}</td>
          <td style="text-align:right">{views:,}</td>
          <td style="text-align:right">{likes:,}</td>
          <td style="text-align:right">{comments:,}</td>
          <td style="text-align:right">{like_r}</td>
          <td style="text-align:center;font-size:12px">{v['published']}</td>
        </tr>"""

    total_subs = int(channel_stats.get("subscriberCount", 0))

    # Nhận xét tự động
    def auto_insight(summary):
        insights = []
        if summary["avg_views_per_video"] >= 1000:
            insights.append("✅ Views/video đang rất tốt (≥1,000). Tiếp tục duy trì chất lượng!")
        elif summary["avg_views_per_video"] >= 300:
            insights.append("📈 Views/video ở mức trung bình. Thử cải thiện thumbnail và 5 giây đầu video.")
        else:
            insights.append("⚠️ Views/video còn thấp. Ưu tiên cải thiện SEO title và thumbnail ngay tuần tới.")

        if summary["like_ratio"] >= 3:
            insights.append("✅ Tỷ lệ Like/View tốt — nội dung đang được khán giả yêu thích.")
        else:
            insights.append("💡 Tỷ lệ Like còn thấp. Thêm CTA 'Nhấn Like nếu bé thích!' vào cuối video.")

        if summary["net_subs"] >= 500:
            insights.append("🚀 Subscriber tăng mạnh! Duy trì lịch đăng đều đặn.")
        elif summary["net_subs"] >= 100:
            insights.append("📊 Subscriber tăng ổn định. Thử cross-promote lên TikTok/Reels.")
        else:
            insights.append("📢 Subscriber tăng chậm. Tập trung vào 1–2 video viral thay vì đăng nhiều video trung bình.")

        if summary["total_minutes"] >= 10000:
            insights.append("⏱️ Watch time xuất sắc! YouTube algorithm đang ưu tiên kênh của bạn.")
        return insights

    insights_html = "".join(f'<li style="padding:6px 0;border-bottom:1px solid #f0f0f0;font-size:14px">{i}</li>' for i in auto_insight(summary))

    # Đề xuất hành động tuần tới
    actions_next_week = [
        f"Làm thêm video tương tự '{top5[0]['title'][:35]}…' — video này đang dẫn đầu tuần" if top5 else "Phân tích video nào có watch time cao nhất",
        "Tạo compilation 1 giờ từ top 5 video tuần này — dễ đạt high watch time",
        "A/B test thumbnail: làm 2 phiên bản khác nhau cho cùng 1 chủ đề rồi so sánh CTR",
        "Đăng Shorts 60s trích từ highlight video có views cao nhất → kéo traffic từ TikTok/Reels",
        "Check từ khóa trending trên YouTube Kids tuần này bằng TubeBuddy → tích hợp vào title tuần tới",
    ]
    actions_html = "".join(f'<li style="padding:5px 0;font-size:13px;color:#374151">{a}</li>' for a in actions_next_week)

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Báo Cáo Tuần {week_num} — YouTube Kids Channel</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0 }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; color: #1e293b; }}
  .page {{ max-width: 960px; margin: 0 auto; padding: 2rem 1.5rem; }}
  .header {{ background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; border-radius: 16px; padding: 2rem; margin-bottom: 1.5rem; }}
  .header h1 {{ font-size: 24px; margin-bottom: 6px; }}
  .header p {{ opacity: .85; font-size: 14px; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 1.5rem; }}
  .kpi {{ background: white; border-radius: 12px; padding: 1rem 1.1rem; box-shadow: 0 1px 4px rgba(0,0,0,.06); }}
  .kpi-val {{ font-size: 26px; font-weight: 700; color: #6366f1; }}
  .kpi-lbl {{ font-size: 12px; color: #64748b; margin-top: 3px; }}
  .kpi-sub {{ font-size: 11px; color: #94a3b8; margin-top: 2px; }}
  .card {{ background: white; border-radius: 12px; padding: 1.25rem 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,.06); margin-bottom: 1.2rem; }}
  .card h2 {{ font-size: 16px; font-weight: 600; margin-bottom: 1rem; color: #1e293b; }}
  .chart-wrap {{ position: relative; height: 220px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 8px 10px; background: #f8fafc; color: #64748b; font-weight: 500; font-size: 12px; border-bottom: 1px solid #e2e8f0; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #f1f5f9; color: #374151; }}
  tr:last-child td {{ border-bottom: none; }}
  .badge-vn {{ background: #fef2f2; color: #dc2626; font-size: 10px; padding: 1px 6px; border-radius: 4px; font-weight: 500; }}
  .badge-en {{ background: #eff6ff; color: #2563eb; font-size: 10px; padding: 1px 6px; border-radius: 4px; font-weight: 500; }}
  ul {{ padding-left: 0; list-style: none; }}
  .insight-list li {{ display: flex; gap: 8px; }}
  .footer {{ text-align: center; font-size: 12px; color: #94a3b8; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }}
  @media print {{ body {{ background: white }} .page {{ padding: 0 }} }}
</style>
</head>
<body>
<div class="page">

  <div class="header">
    <h1>📊 Báo Cáo Tuần {week_num}</h1>
    <p>{start_date} → {end_date} &nbsp;·&nbsp; YouTube Kids Channel Analytics</p>
    <p style="margin-top:8px;font-size:13px">Tổng subscriber kênh: <b>{total_subs:,}</b></p>
  </div>

  <div class="kpi-grid">
    <div class="kpi">
      <div class="kpi-val">{summary['total_views']:,}</div>
      <div class="kpi-lbl">Tổng lượt xem</div>
      <div class="kpi-sub">tuần này</div>
    </div>
    <div class="kpi">
      <div class="kpi-val">+{summary['net_subs']:,}</div>
      <div class="kpi-lbl">Subscriber mới</div>
      <div class="kpi-sub">+{summary['subs_gained']:,} / -{summary['subs_lost']:,}</div>
    </div>
    <div class="kpi">
      <div class="kpi-val">{summary['avg_views_per_video']:,}</div>
      <div class="kpi-lbl">Views/video TB</div>
      <div class="kpi-sub">{summary['total_videos']} video đăng</div>
    </div>
    <div class="kpi">
      <div class="kpi-val">{summary['total_minutes']:,}</div>
      <div class="kpi-lbl">Phút xem (Watch time)</div>
      <div class="kpi-sub">≈ {summary['total_minutes']//60:,} giờ</div>
    </div>
    <div class="kpi">
      <div class="kpi-val">{summary['like_ratio']}%</div>
      <div class="kpi-lbl">Like/View ratio</div>
      <div class="kpi-sub">{summary['total_likes']:,} lượt like</div>
    </div>
    <div class="kpi">
      <div class="kpi-val">{fmt_duration(summary['avg_watch_seconds'])}</div>
      <div class="kpi-lbl">Avg watch time</div>
      <div class="kpi-sub">trung bình/video</div>
    </div>
  </div>

  {'<div class="card"><h2>📈 Views & Subscribers theo ngày</h2><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div class="chart-wrap"><canvas id="viewChart"></canvas></div><div class="chart-wrap"><canvas id="subChart"></canvas></div></div></div>' if daily_rows else ''}

  <div class="card">
    <h2>🏆 Top 10 Video tuần này</h2>
    <div style="overflow-x:auto">
    <table>
      <thead><tr><th>#</th><th>Tiêu đề</th><th style="text-align:right">Views</th><th style="text-align:right">Likes</th><th style="text-align:right">Comments</th><th style="text-align:right">Like%</th><th style="text-align:center">Ngày đăng</th></tr></thead>
      <tbody>{top_rows_html}</tbody>
    </table>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:1.2rem">
    <div class="card">
      <h2>💡 Nhận xét tự động</h2>
      <ul class="insight-list">{insights_html}</ul>
    </div>
    <div class="card">
      <h2>🎯 Hành động tuần tới</h2>
      <ul style="padding-left:16px;line-height:1.8">{actions_html}</ul>
    </div>
  </div>

  <div class="card">
    <h2>📋 Tất cả video tuần {week_num}</h2>
    <div style="overflow-x:auto">
    <table>
      <thead><tr><th>Tiêu đề</th><th style="text-align:right">Views</th><th style="text-align:right">Likes</th><th style="text-align:center">Ngày đăng</th><th>Link</th></tr></thead>
      <tbody>
        {''.join(f"""<tr>
          <td style="max-width:280px;font-size:12px">{v['title'][:60]}{'…' if len(v['title'])>60 else ''}</td>
          <td style="text-align:right">{v.get('views',0):,}</td>
          <td style="text-align:right">{v.get('likes',0):,}</td>
          <td style="text-align:center;font-size:12px">{v['published']}</td>
          <td><a href="https://youtu.be/{v['video_id']}" target="_blank" style="color:#6366f1;font-size:12px">▶ Xem</a></td>
        </tr>""" for v in videos_with_stats)}
      </tbody>
    </table>
    </div>
  </div>

  <div class="footer">
    Báo cáo tạo tự động lúc {datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M')} (GMT+7)
    &nbsp;·&nbsp; YouTube Kids Channel Analytics System
  </div>

</div>

{'<script>const vCtx=document.getElementById("viewChart");new Chart(vCtx,{type:"bar",data:{labels:'+daily_labels+',datasets:[{label:"Views",data:'+daily_views+',backgroundColor:"#818cf8",borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{font:{size:10}}},y:{ticks:{font:{size:10}}}}}});const sCtx=document.getElementById("subChart");new Chart(sCtx,{type:"line",data:{labels:'+daily_labels+',datasets:[{label:"Subs mới",data:'+daily_subs+',borderColor:"#10b981",backgroundColor:"rgba(16,185,129,.1)",fill:true,tension:.4,pointRadius:3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{font:{size:10}}},y:{ticks:{font:{size:10}}}}}});</script>' if daily_rows else ''}

</body>
</html>"""
    return html


# ── Main ──────────────────────────────────────────────────────────────────────
def run_weekly_report(week_num: int = None, use_mock: bool = False):
    """
    Tạo báo cáo tuần.
    week_num: Số tuần (1-4). Nếu None thì tự tính từ ngày ra mắt.
    use_mock: True để chạy với dữ liệu giả (test không cần API)
    """
    # Tính khoảng ngày
    launch_file = CONFIG_DIR / "launch_date.txt"
    if launch_file.exists():
        launch_date = datetime.strptime(launch_file.read_text().strip(), "%Y-%m-%d").date()
    else:
        launch_date = datetime.now(VN_TZ).date()

    if week_num is None:
        days_since = (datetime.now(VN_TZ).date() - launch_date).days
        week_num   = max(1, (days_since // 7) + 1)

    week_start = launch_date + timedelta(weeks=week_num - 1)
    week_end   = week_start + timedelta(days=6)
    start_str  = week_start.strftime("%Y-%m-%d")
    end_str    = week_end.strftime("%Y-%m-%d")

    print(f"\n📊 Tạo báo cáo Tuần {week_num}: {start_str} → {end_str}")

    if use_mock:
        # Dữ liệu giả để test HTML output
        summary = {
            "total_views": 24_830, "total_minutes": 148_200,
            "total_videos": 28,    "avg_views_per_video": 887,
            "net_subs": 1_243,     "subs_gained": 1_302, "subs_lost": 59,
            "total_likes": 892,    "total_comments": 134,
            "like_ratio": 3.59,    "avg_watch_seconds": 185,
        }
        daily_rows = [
            [f"{week_start + timedelta(days=i)}", 2800+i*400, 18000+i*2000, 180+i*5, 160+i*20, 10+i, 120+i*10, 18+i*2]
            for i in range(7)
        ]
        videos = [
            {"video_id": f"mock_{j:03d}", "title": f"[Mock] Video #{j+1} — Chủ đề tuần {week_num}", "published": str(week_start + timedelta(days=j%7)), "thumbnail": ""}
            for j in range(28)
        ]
        video_stats = {
            v["video_id"]: {"views": max(100, 3000 - j*90), "likes": max(10, 120 - j*4), "comments": max(2, 30 - j), "duration": "PT4M30S"}
            for j, v in enumerate(videos)
        }
        channel_stats = {"subscriberCount": "5432"}
        top_video_rows = []
    else:
        youtube, analytics = get_services()
        channel_id, channel_stats = get_channel_id(youtube)
        if not channel_id:
            print("❌ Không tìm thấy kênh YouTube")
            return

        print(f"   Kênh: {channel_id}")
        videos      = get_videos_in_range(youtube, channel_id, start_str, end_str)
        vid_ids     = [v["video_id"] for v in videos]
        video_stats = get_video_stats(youtube, vid_ids) if vid_ids else {}
        daily_rows  = get_channel_analytics(analytics, channel_id, start_str, end_str)
        top_video_rows = get_top_videos_analytics(analytics, channel_id, start_str, end_str)
        summary     = compute_summary(daily_rows, video_stats, videos)

    html = generate_html_report(week_num, start_str, end_str, summary, videos, video_stats, daily_rows, top_video_rows, channel_stats)

    # Lưu file
    filename  = f"week{week_num:02d}_report_{start_str}.html"
    out_path  = REPORT_DIR / filename
    out_path.write_text(html, encoding="utf-8")

    print(f"✅ Báo cáo đã lưu: {out_path}")
    print(f"\n📊 TÓM TẮT TUẦN {week_num}:")
    print(f"   Views     : {summary['total_views']:,}")
    print(f"   Subs mới  : +{summary['net_subs']:,}")
    print(f"   Watch time: {summary['total_minutes']:,} phút")
    print(f"   Videos    : {summary['total_videos']}")
    print(f"   Avg views : {summary['avg_views_per_video']:,}/video")
    return out_path


if __name__ == "__main__":
    week = int(sys.argv[1]) if len(sys.argv) > 1 else None
    mock = "--mock" in sys.argv
    run_weekly_report(week_num=week, use_mock=mock)
