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

## 도트 교체
`sprites/*.txt` 만 고치면 됨. 프레임 지시어 설명은 `sprites/player.txt` 맨 위 주석 참고.
로컬 확인: `pip install -r tools/requirements.txt && python3 tools/build_sprites.py` → `Generated/preview.png`
