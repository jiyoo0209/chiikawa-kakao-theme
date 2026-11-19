# 카카오톡 안드로이드 테마 (개인용)

`images` 폴더에 사진을 올리면 GitHub가 자동으로 카톡 테마 APK를 만들어 줍니다.
카카오 공식 안드로이드 테마 템플릿(26.1.0)이 기반이에요.

> ⚠️ 개인 사용 전용입니다. 캐릭터 사진이 들어가므로 저장소는 **비공개(private)** 로 두고 APK를 배포하지 마세요.

---

## 1. 사진 올리기 (폰 브라우저에서 가능)

1. 저장소에서 `images` 폴더로 들어가기
2. 오른쪽 위 **Add file → Upload files**
3. 사진 파일 이름을 아래 표의 이름으로 바꿔서 올리기 (png / jpg / webp 모두 OK)
4. 맨 아래 **Commit changes** 누르기

사진은 자동으로 크기에 맞게 잘리니 원본 그대로 올리면 됩니다. 필요한 것만 올리고, 없는 건 기본(크림 옐로) 이미지가 쓰여요.

| 파일 이름 | 들어가는 곳 | 팁 |
|---|---|---|
| `background` | 친구·채팅 목록 배경 | 세로 사진, 가운데 기준으로 잘림 |
| `chatroom_background` | 채팅방 배경 | 세로 사진 |
| `splash` | 테마 앱 첫 화면 | 세로 사진 |
| `passcode_background` | 잠금화면 위쪽 배경 | 정사각형 추천 |
| `profile` | 프로필 사진 없는 친구의 기본 프로필 | 정사각형 |
| `app_icon` | 테마 앱 아이콘 | 정사각형 |
| `tab_friends` / `tab_friends_on` | 하단 탭: 친구 (평소 / 선택됐을 때) | 배경 투명한 png 추천 |
| `tab_chats` / `tab_chats_on` | 하단 탭: 채팅 | 〃 |
| `tab_now` / `tab_now_on` | 하단 탭: 오픈채팅 | 〃 |
| `tab_shopping` / `tab_shopping_on` | 하단 탭: 쇼핑 | 〃 |
| `tab_more` / `tab_more_on` | 하단 탭: 더보기 | 〃 |
| `passcode` / `passcode_on` | 잠금 비밀번호 동그라미 (빈칸 / 입력됨) | 투명 png. `passcode_1`~`passcode_4` 로 자리별 다르게도 가능 |

예: `background.jpg`, `tab_chats_on.png`

`_on` 파일이 없으면 평소 아이콘을 선택 상태에도 그대로 씁니다.

## 2. APK 받기

- 올리고 2~4분 뒤 저장소 오른쪽의 **Releases** → 최신 빌드 → `.apk` 파일 누르기
- 빌드 진행 상황은 **Actions** 탭에서 볼 수 있어요 (초록 체크 = 완료)
- 비공개 저장소라서 폰 브라우저에서 GitHub에 로그인돼 있어야 다운로드돼요

## 3. 설치·적용

1. 받은 apk 열기 → "출처를 알 수 없는 앱" 허용 → 설치
   (Play 프로텍트 경고가 떠도 직접 만든 앱이라 괜찮아요 → "무시하고 설치")
2. 설치된 테마 앱 열기 → **테마 적용하기**
   또는 카톡 **설정 → 화면 → 테마** 에서 선택

사진을 바꿔서 다시 빌드하면 버전이 올라가서 **기존 테마 위에 그대로 덮어쓰기 설치**돼요.

## 4. 이름·색상 바꾸기

- **테마 이름**: `theme.properties` 파일의 `themeName` 수정 (연필 아이콘 → 수정 → Commit)
- **글자·배경·말풍선 글자 색**: `src/main/theme/values/colors.xml` 의 `#코드` 수정. 줄마다 한국어 설명이 달려 있어요.
  - 자주 바꾸는 것: `theme_background_color`(목록 배경), `theme_chatroom_background_color`(채팅방 배경), `theme_header_color`(상단 제목), `theme_chatroom_input_bar_send_button_color`(전송 버튼)
- **말풍선 모양/색**은 9-patch 이미지(`src/main/theme/drawable-xxhdpi/theme_chatroom_bubble_*.9.png`)라 직접 교체는 비추천이에요.

## 참고

- `keystore/theme.jks` 는 APK 서명용 키예요. 지우거나 바꾸면 기존 테마를 삭제한 뒤 새로 설치해야 해요.
- 직접 빌드: `python scripts/apply_images.py && ./gradlew assembleRelease`
