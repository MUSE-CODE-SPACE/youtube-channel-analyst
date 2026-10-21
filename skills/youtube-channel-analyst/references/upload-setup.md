# Channel & upload setup audit

A checklist for "is my channel set up right?" / "유튜브 설정해줘". Read the current state first, report it as a table (항목 · 현재 · 권장 · 근거), then change only what the user approved. Every change here is outward-facing.

Evidence levels — say them out loud, don't sell folklore as fact:
- **공식**: documented by YouTube.
- **경험칙**: widely repeated by creators, plausible, not confirmed by YouTube.
- **근거 약함**: YouTube has said otherwise, or no mechanism is known. Mention only if the user asks.

## 1. Survival setup (설정 → 채널)

| Item | Where | Recommend | Evidence |
|---|---|---|---|
| Advanced features (고급 기능) | 채널 → 기능 사용 자격 요건 | All three levels "사용 설정됨". Level 3 needs ID or video verification — the user does it themselves (never automate ID upload). | 공식: needed for Test & Compare and more daily uploads. Claims that unverified channels get less reach = 경험칙. |
| Channel keywords | 채널 → 기본 정보 → 키워드 | 10–20 terms, all directly about the channel's topic. Pull them from the channel's own top search terms (`report.md` §search terms) + YouTube autocomplete. Remove stale ones. | 경험칙 (relevance > count). |
| Country | 채널 → 기본 정보 | The real country. | 공식 |
| Audience (아동용) | 채널 → 고급 설정 | Set "아니요, 아동용 아님" at channel level for adult/tech channels, so uploads don't need it each time. | 공식 |
| Upload cadence | — | A fixed, sustainable rhythm (e.g. longform weekly on the same day + shorts on other days). Increase gradually; cutting abruptly is what hurts. | 경험칙. Compare cadence vs. views in the weekly `--compare` run, don't assume. |

## 2. Upload defaults (설정 → 업로드 기본 설정)

| Item | Recommend | Evidence |
|---|---|---|
| Default visibility | 비공개 — prevents publishing an unfinished video by accident. Upload automations must then set 공개/예약 explicitly. | 공식 (setting exists); safety only. |
| Default tags | 5–10 core channel terms; remove stale topics. | Tags are a minor signal (공식: "mostly for misspellings"). |
| Default description | Only lines that belong under *every* video (links to code repo, app, playlist). Skip if there's nothing true to put there. | 공식 |
| Category | The real one (tech channels: 과학기술 or 교육). | 공식 |
| Video language / title & description language | The narration language (e.g. 한국어). Improves auto captions and language matching. | 공식 |
| Auto chapters | Keep on, but write manual chapters (`0:00 …`) in every longform description — manual chapters override auto ones. | 공식 (override); retention effect = 경험칙. |

## 3. Per-video checks (edit page → 자세히 보기)

- **Shorts 리믹스**: "동영상 및 오디오 리믹스 허용" (default). Remixed shorts link back to the source. 공식 (link-back); growth effect = 경험칙.
- **Playlists**: every longform in a series playlist, ordered. Series playlists keep viewers watching in a row. 공식-ish (session watch time).
- **Shorts → related video**: every short linked to the matching longform (see SKILL.md "Reading the signals").
- **Test & Compare** (longform only, needs advanced features): upload 2–3 thumbnails, YouTube picks by watch-time share. Prefer this to guessing; plain big-keyword thumbnails often win. 공식 feature; result varies.
- **Schedule instead of instant publish**: schedule when the user's audience is active (Studio → 분석 → 시청자층 "시청자가 YouTube를 이용하는 시간"). 
  - The "keep it private 2–24h before publishing so the algorithm can analyze it" tip = **근거 약함**: no confirmed mechanism; YouTube's creator liaison has said uploading private/unlisted first neither helps nor hurts. Scheduling is still useful for timing and for finishing metadata calmly.

## 4. Studio automation recipe (Safari, dedicated window)

Settings dialog: click left-nav "설정" → `ytcp-settings-dialog`. Left menu items by text (일반 / 채널 / 업로드 기본 설정). Sub-tabs are `tp-yt-paper-tab` — match with `includes()` and `offsetParent` (hidden tabs of other sections share names, e.g. two "고급 설정").
- Read state: `d.innerText`; checkbox/radio state = `aria-checked` on `tp-yt-paper-radio-button`, `ytcp-checkbox-lit`.
- Chip fields (keywords, tags): `ytcp-chip-bar input` → focus → `execCommand('insertText', 'a,b,c,')` + `input` event + Enter keydown. Remove a chip: its `#delete-icon`.
- Dropdowns: click `ytcp-dropdown-trigger` (find by label text, or inside `#audio-language` / `#metadata-language` / `#category-select`) → click visible `tp-yt-paper-item` by text.
- Save: the dialog's visible "저장" button → toast "설정 저장됨". Verify by reloading and reopening the dialog — don't trust the toast alone.
- Per-video remix/category: `studio.youtube.com/video/<ID>/edit` → "자세히 보기" → radios by text.
- zsh: in shell, `====` triggers `=cmd` expansion — use `echo '----'`. Write JS to files with quoted heredocs.
