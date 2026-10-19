# youtube-channel-analyst

**내 유튜브 채널을 Claude Code가 직접 분석해 주는 스킬** — API 키도, OAuth도 없이 로그인된 Safari에서 YouTube Studio 데이터를 읽어 "다음에 뭘 올려야 하는지"까지 정리합니다.

> "유튜브 채널 분석해줘" · "다음 영상 뭐 올릴까?" · "어제 올린 쇼츠 반응 어때?"

[English](#english)

## 무엇을 보나

| 항목 | 내용 |
|---|---|
| 쇼츠 vs 롱폼 | 조회 비중, 구독 수, **조회 1천당 구독(구독 전환율)**, 클릭률 |
| 유입 경로 변화 | 전체 기간 → 최근 28일 (예: Shorts 피드 급감, 검색 급증 감지) |
| 검색어 | 내 채널로 들어온 YouTube 검색어 상위 20 |
| 영상별 | 최근 조회 상위, 구독 전환 상위, **썸네일·제목 교체 후보**(노출↑ 클릭률↓), 롱폼 조회율 상위 |
| 새 영상 | 게시 이후 실적(평소 대비 배수, 실시간 조회, 유입) |

수집한 숫자로 자동 신호를 만들고, Claude가 진단 · 이번 주 할 일 3개 · 다음 영상 추천을 써 줍니다. 숫자는 전부 내 Studio에서 읽은 값만 씁니다.

## 설치

```sh
# 방법 1 — skills CLI (Claude Code, Codex 등 Agent Skills 지원 에이전트)
npx skills add MUSE-CODE-SPACE/youtube-channel-analyst

# 방법 2 — Claude Code 플러그인
/plugin marketplace add MUSE-CODE-SPACE/youtube-channel-analyst
/plugin install youtube-channel-analyst@muse-skills

# 방법 3 — 직접 복사
git clone https://github.com/MUSE-CODE-SPACE/youtube-channel-analyst
cp -R youtube-channel-analyst/skills/youtube-channel-analyst ~/.claude/skills/
```

## 준비 (1회)

1. **macOS + Safari**에서 YouTube Studio에 채널 계정으로 로그인
2. Safari 설정 → 고급 → **"웹 개발자용 기능 보기"** 켜기
3. 메뉴 막대 **개발자용 → "Apple 이벤트의 JavaScript 허용"** 켜기

스크립트는 **전용 Safari 창을 새로 열어 작업하고 닫습니다** — 쓰던 탭은 건드리지 않습니다. 데이터는 내 컴퓨터(`yt-analysis/`)에만 저장됩니다.

## 직접 실행

```sh
python3 skills/youtube-channel-analyst/scripts/studio.py collect --out yt-analysis   # 약 2분
python3 skills/youtube-channel-analyst/scripts/analyze.py yt-analysis              # → yt-analysis/report.md
python3 skills/youtube-channel-analyst/scripts/studio.py video <VIDEO_ID>          # 갓 올린 영상 확인
```

- 채널이 여러 개면 `--channel UC...`
- **매주 추적**: 날짜별 폴더에 저장하고 `analyze.py <이번> --compare <지난번>` → 리포트 맨 앞에 '지난번 대비' 변화표
- Studio 언어: 한국어·영어 지원

## 한계

- macOS + Safari 전용 (claude.ai 웹 스킬로는 동작하지 않음)
- 영상별 표는 조회 상위 50개, 최근 28일 데이터는 약 2일 늦게 반영
- YouTube Studio 화면 구조가 바뀌면 `extract_table.js` 셀렉터 수정이 필요할 수 있음

---

## English

A Claude Code skill that analyzes **your own** YouTube channel from real YouTube Studio data — no API key, no OAuth. It drives a dedicated window in your logged-in Safari (macOS), collects lifetime + last-28-day tables (content type, videos, traffic sources, countries, YouTube search terms), computes shorts-vs-longform subscriber conversion, traffic shifts, thumbnail/title fix candidates, and lets Claude write a short strategy with what to upload next.

Setup: log into YouTube Studio in Safari → Settings › Advanced › show web developer features → Develop › **Allow JavaScript from Apple Events**. Install with `npx skills add MUSE-CODE-SPACE/youtube-channel-analyst` or the Claude Code plugin commands above, then ask *"analyze my YouTube channel"*. Studio UI in Korean or English is supported.

## License

MIT
