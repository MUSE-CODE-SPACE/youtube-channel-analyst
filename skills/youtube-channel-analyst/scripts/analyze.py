#!/usr/bin/env python3
"""studio_data.json → 지표 계산 + 자동 신호(signals) → report.md / summary.json

Usage: analyze.py DIR   (DIR/studio_data.json 을 읽어 DIR/report.md, DIR/summary.json 생성)
"""
import json, os, re, sys

d_dir = sys.argv[1]
data = json.load(open(os.path.join(d_dir, "studio_data.json"), encoding="utf-8"))
P = data["periods"]
RECENT = "4_weeks" if "4_weeks" in P else list(P)[-1]
LIFE = "lifetime" if "lifetime" in P else list(P)[0]

COLMAP = {  # Studio 열 이름(ko/en) → 키
    "조회수": "views", "Views": "views",
    "시청 시간(단위: 시간)": "watch_h", "Watch time (hours)": "watch_h",
    "구독자": "subs", "Subscribers": "subs",
    "썸네일 노출수": "impr", "Impressions": "impr",
    "썸네일 클릭률": "ctr", "Impressions click-through rate": "ctr",
    "평균 시청 지속 시간": "avd", "Average view duration": "avd",
    "평균 조회율": "avp", "Average percentage viewed": "avp",
}
SHORTS_NAMES = {"Shorts"}
LONG_NAMES = {"동영상", "Videos"}


def num(s):
    s = (s or "").strip().replace(",", "")
    if s in ("", "—", "-"):
        return None
    if re.fullmatch(r"\d+:\d\d(:\d\d)?", s):
        return sum(int(x) * 60 ** i for i, x in enumerate(reversed(s.split(":"))))
    s = s.rstrip("%")
    m = re.fullmatch(r"(-?[\d.]+)\s*(천|만|K|M)?", s)
    if not m:
        return None
    v = float(m.group(1))
    return v * {"천": 1e3, "만": 1e4, "K": 1e3, "M": 1e6}.get(m.group(2), 1)


def table(period, key):
    t = P.get(period, {}).get(key) or {}
    cols = [COLMAP.get(c, c) for c in t.get("columns", [])]
    out = []
    for r in t.get("rows", []):
        row = {"title": r["title"], "video_id": r.get("video_id")}
        for c, v in zip(cols, r["values"]):
            if c:
                row[c] = num(v)
        out.append(row)
    total = next((r for r in out if r["title"] in ("합계", "Total")), {})
    body = [r for r in out if r is not total]
    return total, body, t.get("period", "")


def pct(a, b):
    return 100.0 * a / b if a is not None and b else None


def f(v, nd=0, suf=""):
    if v is None:
        return "—"
    return (f"{v:,.{nd}f}" if nd else f"{v:,.0f}") + suf


summary, signals = {"channel": data.get("channel_name"), "channel_id": data["channel_id"],
                    "collected_at": data["collected_at"]}, []
md = [f"# 유튜브 채널 분석 — {data.get('channel_name') or data['channel_id']}",
      f"수집: {data['collected_at']} · 채널 ID `{data['channel_id']}`", ""]

# ── 1. 개요 + 쇼츠 vs 롱폼 ──
md.append("## 1. 개요와 쇼츠 vs 롱폼")
for period in (LIFE, RECENT):
    tot, rows, rng = table(period, "content_type")
    if not tot:
        continue
    md.append(f"\n### {('전체 기간' if period == 'lifetime' else '최근 28일' if period == '4_weeks' else period)} ({rng})")
    md.append(f"조회 {f(tot.get('views'))} · 시청 {f(tot.get('watch_h'), 1)}시간 · 구독 {f(tot.get('subs'), suf='명')}"
              f" · 노출 {f(tot.get('impr'))} · 클릭률 {f(tot.get('ctr'), 1, '%')}\n")
    md.append("| 유형 | 조회 | 조회 비중 | 구독 | 조회 1천당 구독 | 클릭률 |\n|---|---|---|---|---|---|")
    split = {}
    for r in rows:
        if not r.get("views") and not r.get("subs"):
            continue
        per_k = 1000.0 * (r.get("subs") or 0) / r["views"] if r.get("views") else None
        split[r["title"]] = {"views": r.get("views"), "subs": r.get("subs"), "subs_per_1k": per_k, "ctr": r.get("ctr")}
        md.append(f"| {r['title']} | {f(r.get('views'))} | {f(pct(r.get('views'), tot.get('views')), 1, '%')} | "
                  f"{f(r.get('subs'))} | {f(per_k, 2)} | {f(r.get('ctr'), 1, '%')} |")
    summary.setdefault("content_type", {})[period] = {"total": tot, "split": split, "range": rng}
    s = next((v for k, v in split.items() if k in SHORTS_NAMES), None)
    l = next((v for k, v in split.items() if k in LONG_NAMES), None)
    if period == LIFE and s and l and s["subs_per_1k"] and l["subs_per_1k"]:
        ratio = l["subs_per_1k"] / s["subs_per_1k"]
        if ratio >= 2:
            signals.append(f"롱폼 구독 전환이 쇼츠의 {ratio:.1f}배(조회 1천당 {l['subs_per_1k']:.1f} vs {s['subs_per_1k']:.1f}명). "
                           f"쇼츠는 노출용, 구독은 롱폼에서 나온다 → 쇼츠마다 관련 롱폼 연결 필수.")
        elif ratio <= 0.5:
            signals.append(f"쇼츠 구독 전환이 롱폼의 {1/ratio:.1f}배 — 쇼츠 중심 운영이 효율적.")

# ── 2. 유입 경로 변화 ──
md.append("\n## 2. 유입 경로 (전체 기간 → 최근 28일)")
lt, lrows, _ = table(LIFE, "traffic")
rt, rrows, _ = table(RECENT, "traffic")
lmap = {r["title"]: pct(r.get("views"), lt.get("views")) for r in lrows}
rmap = {r["title"]: pct(r.get("views"), rt.get("views")) for r in rrows}
md.append("| 유입 경로 | 전체 기간 | 최근 28일 | 변화 |\n|---|---|---|---|")
traffic = []
for name in sorted(set(lmap) | set(rmap), key=lambda k: -(rmap.get(k) or 0)):
    a, b = lmap.get(name), rmap.get(name)
    delta = (b or 0) - (a or 0)
    traffic.append({"source": name, "lifetime_pct": a, "recent_pct": b, "delta_pp": delta})
    if (a or 0) < 0.5 and (b or 0) < 0.5:
        continue
    md.append(f"| {name} | {f(a, 1, '%')} | {f(b, 1, '%')} | {delta:+.1f}%p |")
summary["traffic"] = traffic
for t in traffic:
    if t["delta_pp"] <= -15:
        signals.append(f"'{t['source']}' 유입이 {t['lifetime_pct']:.0f}% → {t['recent_pct'] or 0:.0f}%로 급감({t['delta_pp']:+.0f}%p).")
    elif t["delta_pp"] >= 15:
        signals.append(f"'{t['source']}' 유입이 {t['lifetime_pct'] or 0:.0f}% → {t['recent_pct']:.0f}%로 급증({t['delta_pp']:+.0f}%p) — 이 경로에 맞춘 제목·주제 강화.")
search_share = rmap.get("YouTube 검색") or rmap.get("YouTube search")
if search_share and search_share >= 35:
    signals.append(f"최근 조회의 {search_share:.0f}%가 검색 — 검색어(아래 3장)를 제목 앞부분에 넣는 SEO가 가장 큰 레버.")

# ── 3. 검색어 ──
md.append("\n## 3. 검색어 상위 (최근 28일 / 전체 기간)")
st_r = table(RECENT, "search_terms")[1][:20]
st_l = table(LIFE, "search_terms")[1][:20]
md.append("| # | 최근 28일 | 조회 | 전체 기간 | 조회 |\n|---|---|---|---|---|")
for i in range(max(len(st_r), len(st_l))):
    a = st_r[i] if i < len(st_r) else {}
    b = st_l[i] if i < len(st_l) else {}
    md.append(f"| {i+1} | {a.get('title', '')} | {f(a.get('views'))} | {b.get('title', '')} | {f(b.get('views'))} |")
summary["search_terms"] = {"recent": [(r["title"], r.get("views")) for r in st_r],
                           "lifetime": [(r["title"], r.get("views")) for r in st_l]}

# ── 4. 영상별 ──
def kind(title, avd):
    m = re.match(r"(\d+):(\d\d)(?::(\d\d))? ", title)
    sec = None
    if m:
        p = [int(x) for x in m.groups() if x is not None]
        sec = p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]
    # 쇼츠 최대 길이 3분 기준 추정(정확한 합계는 1장의 콘텐츠 유형 표를 쓴다)
    return ("S" if sec is not None and sec <= 180 else "L"), sec


_, vids_r, _ = table(RECENT, "videos")
_, vids_l, _ = table(LIFE, "videos")
for v in vids_r + vids_l:
    v["kind"], v["dur_s"] = kind(v["title"], v.get("avd"))
    v["clean_title"] = re.sub(r"^\d+:\d\d(:\d\d)? ", "", v["title"]).replace("|", "/")

md.append("\n## 4. 영상별")
md.append("\n### 최근 28일 조회 상위 10\n| 유형 | 제목 | 조회 | 구독 | 클릭률 | 평균 조회율 |\n|---|---|---|---|---|---|")
for v in vids_r[:10]:
    md.append(f"| {'쇼츠' if v['kind'] == 'S' else '롱폼'} | {v['clean_title'][:48]} | {f(v.get('views'))} | {f(v.get('subs'))} | {f(v.get('ctr'), 1, '%')} | {f(v.get('avp'), 1, '%')} |")

conv = sorted([v for v in vids_l if (v.get("views") or 0) >= 100 and v.get("subs")],
              key=lambda v: -(v["subs"] / v["views"]))[:8]
md.append("\n### 구독 전환 상위 (전체 기간, 조회 100회 이상)\n| 유형 | 제목 | 조회 | 구독 | 1천당 구독 |\n|---|---|---|---|---|")
for v in conv:
    md.append(f"| {'쇼츠' if v['kind'] == 'S' else '롱폼'} | {v['clean_title'][:48]} | {f(v['views'])} | {f(v['subs'])} | {1000 * v['subs'] / v['views']:.1f} |")

ch_ctr = (summary.get("content_type", {}).get(LIFE, {}).get("total") or {}).get("ctr")
thumb = sorted([v for v in vids_l if (v.get("impr") or 0) >= 1000 and v.get("ctr") is not None and ch_ctr and v["ctr"] < ch_ctr * 0.7],
               key=lambda v: -(v.get("impr") or 0))[:8]
if thumb:
    md.append(f"\n### 썸네일·제목 교체 후보 (노출 1천↑, 클릭률이 채널 평균 {ch_ctr:.1f}%의 70% 미만)\n| 제목 | 노출 | 클릭률 |\n|---|---|---|")
    for v in thumb:
        md.append(f"| {v['clean_title'][:56]} | {f(v['impr'])} | {f(v['ctr'], 1, '%')} |")
    signals.append(f"노출은 많은데 클릭률이 낮은 영상 {len(thumb)}개 — 썸네일·제목만 바꿔도 조회가 늘 후보(4장 표).")

ret = sorted([v for v in vids_l if v["kind"] == "L" and (v.get("views") or 0) >= 50 and v.get("avp") is not None], key=lambda v: -v["avp"])[:5]
if ret:
    md.append("\n### 롱폼 평균 조회율 상위\n| 제목 | 길이 | 평균 조회율 | 조회 |\n|---|---|---|---|")
    for v in ret:
        md.append(f"| {v['clean_title'][:52]} | {v['title'].split(' ')[0]} | {f(v['avp'], 1, '%')} | {f(v['views'])} |")

summary["videos_recent_top"] = [{k: v.get(k) for k in ("video_id", "clean_title", "kind", "views", "subs", "ctr", "avp", "impr")} for v in vids_r[:15]]
summary["conversion_top"] = [{k: v.get(k) for k in ("video_id", "clean_title", "kind", "views", "subs")} for v in conv]
summary["thumbnail_candidates"] = [{k: v.get(k) for k in ("video_id", "clean_title", "impr", "ctr")} for v in thumb]

# ── 5. 시청자 국가 ──
ct, crow, _ = table(LIFE, "country")
if crow:
    top = crow[0]
    share = pct(top.get("views"), ct.get("views"))
    md.append(f"\n## 5. 시청자 국가\n상위: " + ", ".join(f"{r['title']} {f(pct(r.get('views'), ct.get('views')), 1, '%')}" for r in crow[:5]))
    summary["country_top"] = [(r["title"], pct(r.get("views"), ct.get("views"))) for r in crow[:5]]

md.insert(3, "## 자동 신호\n" + ("\n".join(f"- {s}" for s in signals) if signals else "- (특이 신호 없음)") + "\n")
summary["signals"] = signals
open(os.path.join(d_dir, "report.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
json.dump(summary, open(os.path.join(d_dir, "summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(os.path.join(d_dir, "report.md"))
