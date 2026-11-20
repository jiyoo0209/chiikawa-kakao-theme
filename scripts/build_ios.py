"""
iOS 카카오톡 테마(.ktheme = zip) 만들기.
apply_images.py 를 먼저 돌린 뒤 실행 → 안드로이드용으로 만든 이미지·색을 그대로 iOS 형식으로 옮김.

사용: python scripts/build_ios.py out/<이름>.ktheme
"""
import io
import os
import re
import sys
import zipfile

from PIL import Image, ImageDraw, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TH = os.path.join(ROOT, "src", "main", "theme")
D3 = os.path.join(TH, "drawable-xxhdpi")
RES = os.path.join(ROOT, "src", "main", "res")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out", "theme.ktheme")

# ── 설정·색 읽기 ──────────────────────────────────────────────
props = {}
with open(os.path.join(ROOT, "theme.properties"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            props[k.strip()] = v.strip()

colors = {}
with open(os.path.join(TH, "values", "colors.xml"), encoding="utf-8") as f:
    for name, val in re.findall(r'<color name="([a-z_]+)">#([0-9A-Fa-f]{6,8})</color>', f.read()):
        colors[name] = "#" + val[-6:].upper()   # iOS 는 #RRGGBB (알파는 따로)


def c(name, default="#000000"):
    return colors.get(name, default)


def darker(hexcol, k=0.9):
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % (int(r * k), int(g * k), int(b * k))


# ── 이미지 준비 ───────────────────────────────────────────────
files = {}   # 'Images/xxx@3x.png' -> PIL image


def put(name, im3x, also_2x=True):
    files[f"Images/{name}@3x.png"] = im3x
    if also_2x:
        w, h = im3x.size
        files[f"Images/{name}@2x.png"] = im3x.resize((max(1, round(w * 2 / 3)), max(1, round(h * 2 / 3))), Image.LANCZOS)


def load(path):
    return Image.open(path).convert("RGBA")


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


# 목록 배경: 안드로이드처럼 너비 맞춤 + 아래 정렬, 남는 위쪽은 배경색
src = load(os.path.join(D3, "theme_background_image.png"))
W, H = 1125, 2250
im = src.resize((W, round(src.height * W / src.width)), Image.LANCZOS)
bg = Image.new("RGBA", (W, H), hexrgb(c("theme_background_color")) + (255,))
bg.alpha_composite(im.crop((0, max(0, im.height - H), W, im.height)), (0, max(0, H - im.height)))
put("mainBgImage", bg.convert("RGB"), also_2x=False)

put("chatroomBgImage", ImageOps.fit(load(os.path.join(D3, "theme_chatroom_background_image.png")), (1125, 2250), Image.LANCZOS).convert("RGB"), also_2x=False)
put("passcodeBgImage", ImageOps.fit(load(os.path.join(D3, "theme_passcode_background_image.png")), (1200, 1200), Image.LANCZOS).convert("RGB"), also_2x=False)

prof_src = None
for ext in (".png", ".jpg", ".jpeg", ".webp"):
    p = os.path.join(ROOT, "images", "profile" + ext)
    if os.path.exists(p):
        prof_src = load(p)
        break
if prof_src is None:
    prof_src = load(os.path.join(D3, "theme_profile_01_image.png"))
put("profileImg01", ImageOps.fit(prof_src, (360, 360), Image.LANCZOS), also_2x=False)

TABS = {"friends": "Friends", "chats": "Chats", "now": "Now", "shopping": "Shopping", "more": "More", "call": "Call", "piccoma": "Piccoma"}
for a, i in TABS.items():
    put(f"maintabIco{i}", load(os.path.join(D3, f"theme_maintab_ico_{a}_image.png")).resize((114, 114), Image.LANCZOS))
    put(f"maintabIco{i}Selected", load(os.path.join(D3, f"theme_maintab_ico_{a}_focused_image.png")).resize((114, 114), Image.LANCZOS))

for n in range(1, 5):
    put(f"passcodeImgCode0{n}", load(os.path.join(D3, f"theme_passcode_0{n}_image.png")).resize((132, 132), Image.LANCZOS), also_2x=False)
    put(f"passcodeImgCode0{n}Selected", load(os.path.join(D3, f"theme_passcode_0{n}_checked_image.png")).resize((132, 132), Image.LANCZOS), also_2x=False)

kp = Image.new("RGBA", (720, 720), (0, 0, 0, 0))
ImageDraw.Draw(kp).ellipse((20, 20, 700, 700), fill=hexrgb(c("theme_passcode_keypad_pressed_color")) + (110,))
put("passcodeKeypadPressed", kp.resize((180, 180), Image.LANCZOS), also_2x=False)

put("findBtnAddFriend", load(os.path.join(D3, "theme_find_add_friend_button_image.png")).resize((126, 102), Image.LANCZOS))
files["Images/commonIcoTheme.png"] = load(os.path.join(RES, "mipmap-xxxhdpi", "ic_launcher.png")).resize((162, 162), Image.LANCZOS)


# 말풍선: 안드로이드 9-patch → iOS 늘림 이미지 + 캡/여백(pt) 계산
def bubble(name):
    np_ = load(os.path.join(D3, name))
    w, h = np_.size
    top = [x for x in range(1, w - 1) if np_.getpixel((x, 0))[3] > 0]
    left = [y for y in range(1, h - 1) if np_.getpixel((0, y))[3] > 0]
    bot = [x for x in range(1, w - 1) if np_.getpixel((x, h - 1))[3] > 0]
    rgt = [y for y in range(1, h - 1) if np_.getpixel((w - 1, y))[3] > 0]
    art = np_.crop((1, 1, w - 1, h - 1))
    # 크기를 3의 배수로 (pt 단위로 딱 떨어지게)
    W3, H3 = -(-art.width // 3) * 3, -(-art.height // 3) * 3
    canvas = Image.new("RGBA", (W3, H3), (0, 0, 0, 0))
    canvas.alpha_composite(art, (0, 0))
    sx = (top[0] - 1 + top[-1] - 1) // 2      # 늘어나는 열/행 (가운데)
    sy = (left[0] - 1 + left[-1] - 1) // 2
    cap = (sx // 3, sy // 3)
    ins = (round((rgt[0] - 1) / 3), round((bot[0] - 1) / 3),
           round((H3 - (rgt[-1])) / 3), round((W3 - (bot[-1])) / 3))   # top, left, bottom, right
    return canvas, cap, ins


def darken(im, k=0.92):
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b)).point(lambda v: int(v * k))
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


bub = {}
for side, ios in (("me", "Send"), ("you", "Receive")):
    for n in ("01", "02"):
        im, cap, ins = bubble(f"theme_chatroom_bubble_{side}_{n}_image.9.png")
        put(f"chatroomBubble{ios}{n}", im)
        put(f"chatroomBubble{ios}{n}Selected", darken(im))
        bub[(ios, n)] = (cap, ins)


def capstr(ios, n):
    (cx, cy), _ = bub[(ios, n)]
    return f"{cx}px {cy}px"


def insstr(ios, n):
    _, (t, l, b, r) = bub[(ios, n)]
    return f"{t}px {l}px {b}px {r}px"


# ── CSS ──────────────────────────────────────────────────────
name = props.get("themeName", "My Theme").replace("'", "")
pkg = props.get("packageId", "mytheme")
css = f"""/*
 Manifest
 */
ManifestStyle
{{
    -kakaotalk-theme-name: '{name}';
    -kakaotalk-theme-version: '26.1.0';
    -kakaotalk-theme-url: 'http://www.kakao.com';
    -kakaotalk-author-name: 'me';
    -kakaotalk-theme-id: 'com.kakao.talk.theme.{pkg}ios';
}}

TabBarStyle-Main
{{
    background-color: #FFFFFF;
    -ios-friends-normal-icon-image: 'maintabIcoFriends.png';
    -ios-friends-selected-icon-image: 'maintabIcoFriendsSelected.png';
    -ios-chats-normal-icon-image: 'maintabIcoChats.png';
    -ios-chats-selected-icon-image: 'maintabIcoChatsSelected.png';
    -ios-now-normal-icon-image: 'maintabIcoNow.png';
    -ios-now-selected-icon-image: 'maintabIcoNowSelected.png';
    -ios-piccoma-normal-icon-image: 'maintabIcoPiccoma.png';
    -ios-piccoma-selected-icon-image: 'maintabIcoPiccomaSelected.png';
    -ios-shopping-normal-icon-image: 'maintabIcoShopping.png';
    -ios-shopping-selected-icon-image: 'maintabIcoShoppingSelected.png';
    -ios-call-normal-icon-image: 'maintabIcoCall.png';
    -ios-call-selected-icon-image: 'maintabIcoCallSelected.png';
    -ios-more-normal-icon-image: 'maintabIcoMore.png';
    -ios-more-selected-icon-image: 'maintabIcoMoreSelected.png';
    -ios-openchats-normal-icon-image: 'maintabIcoNow.png';
    -ios-openchats-selected-icon-image: 'maintabIcoNowSelected.png';
}}

HeaderStyle-Main
{{
    -ios-text-color: {c('theme_header_color')};
    -ios-tab-text-color: {c('theme_feature_browse_tab_color')};
    -ios-tab-highlighted-text-color: {c('theme_feature_browse_tab_focused_color')};
}}

MainViewStyle-Primary
{{
    background-color: {c('theme_background_color')};
    -ios-background-image: 'mainBgImage.png';
    -ios-text-color: {c('theme_title_color')};
    -ios-highlighted-text-color: {c('theme_title_pressed_color')};
    -ios-description-text-color: {c('theme_description_color')};
    -ios-description-highlighted-text-color: {c('theme_description_pressed_color')};
    -ios-paragraph-text-color: {c('theme_paragraph_color')};
    -ios-paragraph-highlighted-text-color: {c('theme_paragraph_pressed_color')};
    -ios-normal-background-color: {c('theme_background_color')};
    -ios-normal-background-alpha: 0.0;
    -ios-selected-background-color: {c('theme_header_color')};
    -ios-selected-background-alpha: 0.05;
}}

MainViewStyle-Secondary
{{
    background-color: {c('theme_body_secondary_cell_color')};
}}

SectionTitleStyle-Main
{{
    border-color: {c('theme_header_color')};
    border-alpha: 0.09;
    -ios-text-color: {c('theme_section_title_color')};
    -ios-text-alpha: 1.0;
}}

FeatureStyle-Primary
{{
    -ios-text-color: {c('theme_feature_primary_color')};
}}

ButtonStyle-AddFriend
{{
    -ios-image: 'findBtnAddFriend.png';
}}

DefaultProfileStyle
{{
    -ios-profile-images: 'profileImg01.png';
}}

BackgroundStyle-ChatRoom
{{
    background-color: {c('theme_chatroom_background_color')};
    -ios-background-image: 'chatroomBgImage.png';
}}

InputBarStyle-Chat
{{
    background-color: #FFFFFF;
    -ios-send-normal-background-color: {c('theme_chatroom_input_bar_send_button_color')};
    -ios-send-normal-foreground-color: {c('theme_chatroom_input_bar_send_icon_color')};
    -ios-send-highlighted-background-color: {darker(c('theme_chatroom_input_bar_send_button_color'))};
    -ios-send-highlighted-foreground-color: {c('theme_chatroom_input_bar_send_icon_color')};
    -ios-button-normal-foreground-color: {c('theme_chatroom_input_bar_menu_icon_color')};
    -ios-button-highlighted-foreground-color: {darker(c('theme_chatroom_input_bar_menu_icon_color'))};
    -ios-button-text-color: #191919;
    -ios-button-normal-background-color: #000000;
    -ios-button-normal-background-alpha: 0.04;
}}

MessageCellStyle-Send
{{
    -ios-background-image: 'chatroomBubbleSend01.png' {capstr('Send', '01')};
    -ios-selected-background-image: 'chatroomBubbleSend01Selected.png' {capstr('Send', '01')};
    -ios-group-background-image: 'chatroomBubbleSend02.png' {capstr('Send', '02')};
    -ios-group-selected-background-image: 'chatroomBubbleSend02Selected.png' {capstr('Send', '02')};
    -ios-title-edgeinsets: {insstr('Send', '01')};
    -ios-group-title-edgeinsets: {insstr('Send', '02')};
    -ios-text-color: {c('theme_chatroom_bubble_me_color')};
    -ios-selected-text-color: {c('theme_chatroom_bubble_me_color')};
    -ios-unread-text-color: {c('theme_chatroom_unread_count_color')};
}}

MessageCellStyle-Receive
{{
    -ios-background-image: 'chatroomBubbleReceive01.png' {capstr('Receive', '01')};
    -ios-selected-background-image: 'chatroomBubbleReceive01Selected.png' {capstr('Receive', '01')};
    -ios-group-background-image: 'chatroomBubbleReceive02.png' {capstr('Receive', '02')};
    -ios-group-selected-background-image: 'chatroomBubbleReceive02Selected.png' {capstr('Receive', '02')};
    -ios-title-edgeinsets: {insstr('Receive', '01')};
    -ios-group-title-edgeinsets: {insstr('Receive', '02')};
    -ios-text-color: {c('theme_chatroom_bubble_you_color')};
    -ios-selected-text-color: {c('theme_chatroom_bubble_you_color')};
    -ios-unread-text-color: {c('theme_chatroom_unread_count_color')};
}}

BackgroundStyle-Passcode
{{
    background-color: {c('theme_passcode_background_color')};
    -ios-background-image: 'passcodeBgImage.png';
}}

LabelStyle-PasscodeTitle
{{
    -ios-text-color: {c('theme_passcode_color')};
}}

PasscodeStyle
{{
    -ios-bullet-first-image: 'passcodeImgCode01.png';
    -ios-bullet-second-image: 'passcodeImgCode02.png';
    -ios-bullet-third-image: 'passcodeImgCode03.png';
    -ios-bullet-fourth-image: 'passcodeImgCode04.png';
    -ios-bullet-selected-first-image: 'passcodeImgCode01Selected.png';
    -ios-bullet-selected-second-image: 'passcodeImgCode02Selected.png';
    -ios-bullet-selected-third-image: 'passcodeImgCode03Selected.png';
    -ios-bullet-selected-fourth-image: 'passcodeImgCode04Selected.png';
    -ios-keypad-background-color: {c('theme_passcode_keypad_background_color')};
    -ios-keypad-text-normal-color: {c('theme_passcode_keypad_color')};
    -ios-keypad-number-highlighted-image : 'passcodeKeypadPressed.png';
}}

BackgroundStyle-MessageNotificationBar
{{
    background-color: {c('theme_notification_background_color')};
}}

LabelStyle-MessageNotificationBarName
{{
    -ios-text-color: {c('theme_notification_color')};
}}

LabelStyle-MessageNotificationBarMessage
{{
    -ios-text-color: {c('theme_paragraph_color')};
}}

BackgroundStyle-DirectShareBar
{{
    background-color: {c('theme_direct_share_background_color')};
}}

LabelStyle-DirectShareBarName
{{
    -ios-text-color: {c('theme_direct_share_color')};
}}

LabelStyle-DirectShareBarMessage
{{
    -ios-text-color: {c('theme_description_color')};
}}

BottomBannerStyle {{
    background-color: {c('theme_header_color')};
}}

BottomBannerStyle-Light {{
    background-color: {c('theme_header_color')};
}}
"""

# ── zip(.ktheme) 쓰기: 최상단에 KakaoTalkTheme.css 와 Images/ ──
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("KakaoTalkTheme.css", css.encode("utf-8"))
    d = zipfile.ZipInfo("Images/", date_time=(2020, 1, 1, 0, 0, 0))
    d.create_system = 0                       # MS-DOS 방식 + 폴더 표시 (아이폰 압축 해제가 파일로 오해하지 않게)
    d.external_attr = (0o40755 << 16) | 0x10
    z.writestr(d, b"")
    for path, im in sorted(files.items()):
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        z.writestr(path, buf.getvalue())
print(f"iOS 테마: {OUT}  (이미지 {len(files)}장)")
