# Android WIPI APK 빌드

갤럭시 기기에서 기존 LGT WIPI 게임을 실행하기 위한 개인용 빌드 실험입니다.

**중요: 이 저장소는 현재 공개(Public)입니다.** 상용 게임 원본(와일드프론티어.zip)은 업로드하지 마세요. GitHub 저장소 Settings → General → Danger Zone → Change repository visibility에서 Private으로 변경한 뒤, `game/wildfrontier.zip`을 올려야 게임 내장 APK를 빌드할 수 있습니다.

## 자동 빌드
`.github/workflows/build-apk.yml`이 GitHub Actions에서 Android ARM64 빌드/서명을 수행합니다.
- `game/wildfrontier.zip` 없을 때: 일반 **WIPI Emulator APK**만 빌드합니다(사용자가 게임 파일을 직접 불러와야 함).
- 게임 ZIP 있을 때: `scripts/embed_game.py`로 게임을 내장·자동실행하도록 수정한 **와일드프론티어 APK**를 빌드합니다.

## 검증
APK 빌드 성공은 게임 호환성·실기기 정상 구동의 증거가 아닙니다. 화면/소리/저장은 실제 기기에서 별도 확인해야 합니다.

원본 오픈소스: https://github.com/ParkJeongseop/WIPI-Emulator (MIT) 
이 저장소에는 원본 게임 데이터 및 저작권 보유자의 자산을 포함하지 않습니다.
