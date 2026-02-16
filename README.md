# arxiv_ph_rcmd

## 빠른 시작 (Codex 사용자)
1. 로컬로 클론 후 폴더 진입
   - `cd /path/to/arxiv_ph_rcmd`
2. 바로 실행
   - `./start`

기본 동작:
- `context/zotero_recommendation_profile.md`가 없으면 템플릿(`templates/zotero_recommendation_profile.sample.md`)으로 자동 초기화됩니다.
- 그래서 Zotero 키 없이도 추천 실행이 가능합니다.

## 실행
- `./start` (기존/템플릿 기준 파일을 사용해 추천만 실행)
- `./start -r` (Zotero 기준 파일 갱신 + 추천 실행)
- `npm start`
- 또는 `bash ./start.sh`

## 동작 순서
1. `./start`:
   - 기존 `context/zotero_recommendation_profile.md` 사용
   - 파일이 없으면 템플릿으로 자동 생성
   - 지난 2일 arXiv astro-ph(+하위 섹션) 수집
   - 5편 추천 메시지를 터미널에 직접 출력
2. `./start -r`:
   - Zotero API로 라이브러리 메타데이터/초록 수집
   - Codex 프롬프트로 연구 프로필(추천 기준) 재생성
   - 지난 2일 arXiv astro-ph(+하위 섹션) 수집
   - 5편 추천 메시지를 터미널에 직접 출력

## 주요 파일
- `scripts/fetch_zotero_library.py`
- `scripts/fetch_arxiv_astro_ph.py`
- `prompts/01_build_zotero_profile.prompt.md`
- `prompts/02_recommend_astro_ph_last2days.prompt.md`
- `templates/zotero_recommendation_profile.sample.md`
- `context/zotero_recommendation_profile.md`
- `data/arxiv_astro_ph_last2days_summary.md`
- 전송용 메시지는 실행 시 터미널 출력으로 바로 표시됩니다.

## Codex 실행 파일 경로
- 기본값:
  - `/Applications/Codex.app/Contents/Resources/codex`
- 위 경로가 없으면 시스템 PATH의 `codex`를 자동 탐색합니다.
- 필요 시 수동 지정:
  - `CODEX_BIN=/custom/path/to/codex ./start`

## API 키
- `./start -r` 실행 시에만 Zotero API 키가 필요합니다.
- 기본적으로 `.zotero_api_key` 파일을 읽습니다.
- 또는 환경변수 `ZOTERO_API_KEY`를 우선 사용합니다.
- `start.sh` 실행 시 `.zotero_api_key` 권한을 자동으로 `600`으로 맞춥니다.
- 보안상 키를 커맨드 인자(`--api-key`)로 넘기지 않고 환경변수로만 전달합니다.
- 선택적으로 `.zotero_user_id` 또는 `ZOTERO_USER_ID`를 지정하면 키 조회 API 호출을 생략할 수 있습니다.
