---
name: youtube-channel-analyst
description: "Analyze the user's own YouTube channel from real YouTube Studio data and turn it into a strategy: shorts vs longform subscriber conversion, traffic-source shifts, top search terms, CTR/thumbnail fix candidates, retention, and what to upload next. Reads Studio through the user's logged-in Safari (macOS) — no API key or OAuth. Use when the user asks to analyze their YouTube channel/analytics, check how a video is doing, or decide what video to make next based on data. Korean: 유튜브 분석, 채널 분석, 스튜디오 데이터, 다음 영상 뭐 올릴까."
---

# YouTube Channel Analyst

Real numbers from the user's own YouTube Studio → a short, decisive strategy. Never invent metrics; every number in the final answer must come from `studio_data.json`.

## Requirements (check first)

- macOS + Safari, logged into YouTube Studio with the channel's account.
- Safari: Settings → Advanced → "Show features for web developers", then Develop menu → **"Allow JavaScript from Apple Events"**. If the collector exits with the JavaScript message, ask the user to turn it on (one-time).
- The scripts open their **own Safari window** and close it afterwards — the user's tabs are never touched. Don't drive the front tab.

## Workflow

1. **Collect** (≈2 min; lifetime + last 28 days):
   ```bash
   python3 <SKILL_DIR>/scripts/studio.py collect --out <WORKDIR>/yt-analysis
   ```
   Auto-detects the channel from the logged-in Studio. Multiple channels on the account → pass `--channel UC…`. Other periods: `--periods lifetime,4_weeks` accepts Studio `time_period` values.
2. **Analyze**:
   ```bash
   python3 <SKILL_DIR>/scripts/analyze.py <WORKDIR>/yt-analysis
   ```
   Writes `report.md` (tables + auto signals) and `summary.json`. Read `report.md` fully before writing anything.
3. **Recent upload check** (optional — videos younger than ~2 days aren't in the 28-day table yet):
   ```bash
   python3 <SKILL_DIR>/scripts/studio.py video <VIDEO_ID> --out <WORKDIR>/yt-analysis
   ```
   Saves the "since publish" overview + reach text (views vs typical, realtime, traffic sources). Read the numbers out of the text; note "데이터 처리 중" when retention isn't ready.
4. **Write the strategy** (Korean unless the user writes otherwise). Keep it short and decisive:
   - **진단 (3줄)**: the 2–3 strongest signals with their numbers (conversion ratio shorts vs longform, traffic shift, search share).
   - **잘 되는 것**: top performers and *why* (search term match, new-tool name, measurement format, etc.).
   - **이번 주 할 일 3개**: concrete, checkable (e.g. "썸네일 교체: <title> — 노출 7,265 / CTR 1.1%", "쇼츠 N개에 관련 롱폼 연결").
   - **다음 영상 추천 1개**: tie it to the data — a rising search term the channel already ranks for, or a new tool name nobody has covered in the viewer's language yet. Give title draft + shorts/longform pairing.
   - What to measure after upload (and when: ~48h).
5. Offer (one line) a PDF/HTML version of the report if the user wants to share it.

## Weekly tracking (experiments, e.g. "run my channel by this for a month")

- Keep one snapshot folder per run: `<WORKDIR>/yt-analysis/YYYY-MM-DD/` (pass it as `--out`). The first one is the baseline (Day 0).
- From the second run on, compare with the latest previous snapshot:
  ```bash
  python3 <SKILL_DIR>/scripts/analyze.py <WORKDIR>/yt-analysis/<today> --compare <WORKDIR>/yt-analysis/<previous>
  ```
  This adds "0. 지난번 대비" (28-day views, subs, CTR, shorts/longform conversion, traffic shares, new search terms) at the top of the report.
- Keep `<WORKDIR>/yt-analysis/actions.md`: after each run append the date, the 3 actions you recommended, and (next run) whether the user did them. Judge each action against the next run's deltas — say plainly when something didn't move the numbers.
- 28-day windows overlap week to week; call out changes that are within noise (small channels: a single video can swing everything).

## Reading the signals

- **Subs per 1k views** (content-type table) is the conversion metric. Longform ≫ shorts is common: shorts = reach, longform = subscribers → link every short to a related longform and pin the longform link in the short's comments.
- **Traffic shift**: Shorts-feed share collapsing while search grows means the channel now lives on search → put the exact search term at the start of titles; cover new tool names early.
- **Thumbnail candidates**: high impressions + CTR < 70% of channel average. Shorts have no thumbnail CTR (shows 0.0% / —) — ignore them there.
- Per-video shorts/longform tag in §4 is a duration heuristic (≤3 min = shorts); trust §1 (content type) for totals.
- Tables list the top 50 videos by views; the 28-day window lags ~2 days.

## Notes

- Studio UI language: Korean and English column names are mapped; other languages need `COLMAP` entries in `analyze.py`.
- If a table comes back empty, Studio was slow — rerun `collect` (it retries per table). If the DOM changed, inspect with `extract_table.js` (`yta-explore-table-row`, `.dimension-column`, `.metric-column .value`).
- Write-side Studio edits (titles, related video links) are possible with the same Safari approach but are outward-facing — confirm with the user first. Localized-title editor and end-screen editor don't respond to synthetic clicks.
