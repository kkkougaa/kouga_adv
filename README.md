# 도트 전사 (라이브 액티비티 방치형 전투)

잠금화면 라이브 액티비티 / 다이나믹 아일랜드에서 도트 캐릭터가 자동으로 싸우는 개인용 아이폰 게임.

## 구조
- `sprites/` 도트 정의 (문자 격자, 한 글자 = 한 색). `palette.txt` 가 색표.
- `tools/build_sprites.py` 도트 → 그림 파일 + 타이머 꼼수용 글꼴 + 스위프트 목록 (`Generated/` 에 생성)
- `Shared/` 앱과 확장이 같이 쓰는 코드 (전투 계산, 라이브 액티비티 데이터, 버튼 인텐트, 화면)
- `App/` 앱 본체 / `Widget/` 라이브 액티비티 확장
- `project.yml` 엑스코드젠 설정 (깃허브 액션에서 프로젝트 생성)

## 빌드
`main` 에 올리면 깃허브 액션이 서명 안 된 `PixelKnight.ipa` 를 만들어서
실행 결과물과 `latest` 릴리스에 올림 → 페더로 서명해서 설치.

## 사이드스토어 소스
사이드스토어(또는 페더)에 이 주소를 소스로 추가:
`https://github.com/kkkougaa/kouga_adv/releases/download/latest/source.json`
빌드할 때마다 버전이 `0.1.<빌드번호>` 로 올라가서 업데이트로 잡힘.

## 도트 교체
원본 도트 시트는 `sprites/source/sheet.png` (도트 한 칸 = 7.5px, 4x3 칸).
`python3 tools/import_sheet.py` 를 돌리면 시트에서 그대로 읽어 `sprites/*.txt` 와 팔레트를 다시 만듦.
`sprites/*.txt` 를 직접 고쳐도 됨. 프레임 지시어 설명은 `sprites/player.txt` 맨 위 주석 참고.
로컬 확인: `pip install -r tools/requirements.txt && python3 tools/build_sprites.py` → `Generated/preview.png`
