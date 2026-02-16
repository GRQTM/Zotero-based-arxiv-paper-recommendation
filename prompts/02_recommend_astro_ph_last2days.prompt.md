You are selecting astro-ph papers for the user.

Goal:
- Read `context/zotero_recommendation_profile.md`.
- Read all entries from `data/arxiv_astro_ph_last2days.json`.
- Recommend exactly 5 papers that best match the user's inferred research profile.

Hard requirements:
1. Process every paper entry in `data/arxiv_astro_ph_last2days.json` before ranking.
2. Use the scoring criteria and keyword rules from `context/zotero_recommendation_profile.md`.
3. Include all astro-ph subsections already present in the dataset (do not narrow the scope).
4. Write the response in Korean.

Selection constraints:
- Pick 5 papers only.
- Avoid near-duplicates in topic.
- Prefer papers that are both relevant and actionable for the user's ongoing work.

For each selected paper, include:
- 제목
- 저자
- arXiv ID / 링크
- 3~5문장 요약
- 추천 이유 (사용자 연구와의 연결고리)
- 적합도 점수 (0~100)

Also include:
- `스캔한 전체 논문 수`
- `최종 추천 5편 평균 적합도`
- `아쉽게 제외한 후보 3편` (제외 이유 1줄씩)

Output:
- Write the full result directly to stdout (terminal output) in Korean.
- Do not write or modify any files.
- Use this exact final section title:
  - `## 전송용 추천 메시지`

Message format for the final section:
- short greeting
- top 5 list (for each paper, include all fields below in Korean):
  - 제목
  - 저자 (최대 3명만 표기, 나머지는 "외 N명")
  - 링크
  - 내용 요약 (2~3문장)
  - 추천 이유 (1~2문장)
- closing line with next scan suggestion

After finishing:
- Print a short Korean completion summary.
