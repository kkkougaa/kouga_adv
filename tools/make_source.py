#!/usr/bin/env python3
"""사이드스토어(알트스토어 형식) 소스 파일 만들기. 깃허브 액션에서 빌드 후 실행.

사용: python3 tools/make_source.py <설치파일> <버전> <빌드번호> <출력.json>
소스 주소: https://github.com/kkkougaa/kouga_adv/releases/download/latest/source.json
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = "kkkougaa/kouga_adv"
BASE = f"https://github.com/{REPO}/releases/download/latest"

ipa, version, build, out = sys.argv[1:5]
size = Path(ipa).stat().st_size
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
desc = "잠금화면 라이브 액티비티와 다이나믹 아일랜드에서 도트 캐릭터가 몬스터와 자동으로 싸우는 방치형 게임."

app = {
    "name": "도트 전사",
    "bundleIdentifier": "com.pixelknight.app",
    "developerName": "kouga_adv",
    "subtitle": "잠금화면 방치형 도트 전투",
    "localizedDescription": desc,
    "iconURL": f"{BASE}/icon.png",
    "tintColor": "2ec4b6",
    "category": "games",
    "screenshots": [],
    "versions": [{
        "version": version,
        "buildVersion": build,
        "date": now,
        "localizedDescription": f"자동 빌드 {build}",
        "downloadURL": f"{BASE}/PixelKnight.ipa",
        "size": size,
        "minOSVersion": "17.0",
    }],
    # 예전 형식 앱들을 위한 값
    "version": version,
    "versionDate": now,
    "versionDescription": f"자동 빌드 {build}",
    "downloadURL": f"{BASE}/PixelKnight.ipa",
    "size": size,
    "appPermissions": {"entitlements": [], "privacy": {}},
}

source = {
    "name": "도트 전사",
    "identifier": "com.pixelknight.source",
    "subtitle": "개인용 빌드",
    "description": desc,
    "iconURL": f"{BASE}/icon.png",
    "website": f"https://github.com/{REPO}",
    "tintColor": "2ec4b6",
    "apps": [app],
    "news": [],
}
Path(out).write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"소스 생성: 버전 {version} ({build}), {size} 바이트")
