#!/usr/bin/env python3
"""YouTube Studio 분석 데이터를 사용자의 Safari(로그인 상태)에서 읽어 JSON으로 저장한다.

전제: Safari에 YouTube Studio 로그인 + 설정 > 고급 > '메뉴 막대에서 웹 개발자용 기능 보기' 후
      개발자용 메뉴 > 'Apple 이벤트의 JavaScript 허용' 켜기.
사용자의 기존 탭은 건드리지 않도록 전용 창을 새로 열어 창 id로만 조작한다.

Usage:
  studio.py collect [--out DIR] [--channel UC...] [--periods lifetime,4_weeks] [--keep-window]
  studio.py video VIDEO_ID [--out DIR]      # 게시 이후 개요(실시간 포함) 원문 저장
"""
import argparse, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
EXTRACT_JS = os.path.join(HERE, "extract_table.js")
DRILL_JS = os.path.join(HERE, "drill_row.js")

VIDEO_METRICS = ["VIEWS", "WATCH_TIME", "SUBSCRIBERS_NET_CHANGE", "VIDEO_THUMBNAIL_IMPRESSIONS",
                 "VIDEO_THUMBNAIL_IMPRESSIONS_VTR", "AVERAGE_WATCH_TIME", "AVERAGE_WATCH_PERCENTAGE"]
DATASETS = {  # name: (dimension, metrics)
    "content_type": ("CREATOR_CONTENT_TYPE", ["VIEWS", "WATCH_TIME", "SUBSCRIBERS_NET_CHANGE",
                                              "VIDEO_THUMBNAIL_IMPRESSIONS", "VIDEO_THUMBNAIL_IMPRESSIONS_VTR"]),
    "videos": ("VIDEO", VIDEO_METRICS),
    "traffic": ("TRAFFIC_SOURCE_TYPE", ["VIEWS", "WATCH_TIME", "SUBSCRIBERS_NET_CHANGE"]),
    "country": ("COUNTRY", ["VIEWS", "WATCH_TIME"]),
}
SEARCH_ROW = ["YouTube 검색", "YouTube search"]


def osa(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


class Window:
    def __init__(self, url):
        self.id = int(osa(f'tell application "Safari"\nmake new document with properties {{URL:"{url}"}}\n'
                          f'return id of front window\nend tell'))

    def tab(self):
        return f"current tab of (first window whose id is {self.id})"

    def go(self, url, wait=9):
        osa(f'tell application "Safari" to set URL of {self.tab()} to "{url}"')
        time.sleep(wait)

    def url(self):
        return osa(f'tell application "Safari" to get URL of {self.tab()}')

    def js_file(self, path, replace=None):
        src = open(path, encoding="utf-8").read()
        for k, v in (replace or {}).items():
            src = src.replace(k, v)
        tmp = f"/tmp/ytca_{os.getpid()}.js"
        open(tmp, "w", encoding="utf-8").write(src)
        try:
            return osa(f'tell application "Safari" to do JavaScript (read POSIX file "{tmp}" as «class utf8») in {self.tab()}')
        finally:
            os.remove(tmp)

    def js(self, code):
        code = code.replace("\\", "\\\\").replace('"', '\\"')
        return osa(f'tell application "Safari" to do JavaScript "{code}" in {self.tab()}')

    def close(self):
        osa(f'tell application "Safari" to close (first window whose id is {self.id})')


def check_js_allowed():
    try:
        osa('tell application "Safari" to do JavaScript "1" in current tab of front window')
    except RuntimeError as e:
        if "JavaScript" in str(e) or "허용" in str(e):
            sys.exit("Safari에서 개발자용 메뉴 > 'Apple 이벤트의 JavaScript 허용'을 켜 주세요.")


def explore_url(ch, period, dim, metrics):
    m = "".join(f"&t_metrics={x}" for x in metrics)
    return (f"https://studio.youtube.com/channel/{ch}/analytics/tab-overview/period-default/explore"
            f"?entity_type=CHANNEL&entity_id={ch}&time_period={period}&explore_type=TABLE_AND_CHART"
            f"&metric=VIEWS&granularity=DAY{m}&dimension={dim}&o_column=VIEWS"
            f"&o_direction=ANALYTICS_ORDER_DIRECTION_DESC")


def read_table(w, tries=4):
    for _ in range(tries):
        d = json.loads(w.js_file(EXTRACT_JS) or "{}")
        if d.get("rows"):
            return d
        time.sleep(3)
    return d


def detect_channel(w):
    w.go("https://studio.youtube.com/", wait=8)
    m = re.search(r"/channel/(UC[\w-]{22})", w.url())
    if not m:
        sys.exit("채널 ID를 찾지 못했습니다. Safari에서 YouTube Studio에 로그인돼 있는지 확인하세요.")
    name = w.js("(document.querySelector('#entity-name, ytcp-navigation-drawer #channel-title, .entity-name') || {}).innerText || ''")
    return m.group(1), name.strip()


def collect(a):
    check_js_allowed()
    os.makedirs(a.out, exist_ok=True)
    w = Window("about:blank")
    try:
        ch, name = (a.channel, "") if a.channel else detect_channel(w)
        result = {"channel_id": ch, "channel_name": name, "collected_at": time.strftime("%Y-%m-%d %H:%M"), "periods": {}}
        for period in a.periods.split(","):
            pr = result["periods"][period] = {}
            for key, (dim, metrics) in DATASETS.items():
                w.go(explore_url(ch, period, dim, metrics))
                pr[key] = read_table(w)
                print(f"[{period}] {key}: {len(pr[key].get('rows', []))} rows  {pr[key].get('period', '')}", flush=True)
            # 검색어: 트래픽 소스 표에서 'YouTube 검색' 행으로 드릴다운
            w.go(explore_url(ch, period, "TRAFFIC_SOURCE_TYPE", ["VIEWS", "WATCH_TIME"]))
            for label in SEARCH_ROW:
                if w.js_file(DRILL_JS, {"__ROW__": label}) == "clicked":
                    time.sleep(6)
                    pr["search_terms"] = read_table(w)
                    break
            print(f"[{period}] search_terms: {len(pr.get('search_terms', {}).get('rows', []))} rows", flush=True)
        if not result["channel_name"]:
            result["channel_name"] = result["periods"][a.periods.split(",")[0]]["videos"].get("channel", "")
        path = os.path.join(a.out, "studio_data.json")
        json.dump(result, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("saved", path)
    finally:
        if not a.keep_window:
            w.close()


def video(a):
    check_js_allowed()
    os.makedirs(a.out, exist_ok=True)
    w = Window("about:blank")
    try:
        texts = {}
        for tab in ("tab-overview", "tab-reach_viewers"):
            w.go(f"https://studio.youtube.com/video/{a.video_id}/analytics/{tab}/period-since_publish", wait=10)
            texts[tab] = w.js("document.body.innerText")
        path = os.path.join(a.out, f"video_{a.video_id}.json")
        json.dump(texts, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("saved", path)
    finally:
        w.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--out", default="yt-analysis")
    c.add_argument("--channel")
    c.add_argument("--periods", default="lifetime,4_weeks")
    c.add_argument("--keep-window", action="store_true")
    v = sub.add_parser("video")
    v.add_argument("video_id")
    v.add_argument("--out", default="yt-analysis")
    a = ap.parse_args()
    {"collect": collect, "video": video}[a.cmd](a)
