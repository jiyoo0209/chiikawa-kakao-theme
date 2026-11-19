"""
images/ 폴더에 올린 사진을 카톡 테마 리소스 크기에 맞게 잘라서 넣고,
theme.properties 의 테마 이름을 적용한다. (GitHub Actions 빌드 전에 자동 실행)
"""
import os
import re
import sys
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")
TH = os.path.join(ROOT, "src", "main", "theme")
RES = os.path.join(ROOT, "src", "main", "res")
EXTS = (".png", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG", ".WEBP")


def find(name):
    for ext in EXTS:
        p = os.path.join(IMG, name + ext)
        if os.path.exists(p):
            return p
    return None


def load(p):
    im = Image.open(p)
    im = ImageOps.exif_transpose(im)  # 폰 사진 회전 정보 반영
    return im.convert("RGBA")


def cover(im, w, h):
    """화면을 꽉 채우도록 가운데 기준으로 잘라냄"""
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=(0.5, 0.5))


def contain(im, size, scale=1.0):
    """정사각형 안에 비율 유지해서 넣음 (아이콘용, 배경 투명)"""
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    inner = max(1, int(size * scale))
    im = ImageOps.contain(im, (inner, inner), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((size - im.width) // 2, (size - im.height) // 2))
    return canvas


def save(im, folder, filename):
    d = os.path.join(TH, folder) if not folder.startswith("mipmap") else os.path.join(RES, folder)
    os.makedirs(d, exist_ok=True)
    im.save(os.path.join(d, filename), optimize=True)


applied = []

# 1) 큰 배경 이미지들 ---------------------------------------------------------
FULL = {
    "splash": [
        ("drawable-xhdpi", 720, 1280), ("drawable-xxhdpi", 1440, 2560), ("drawable-sw600dp", 1440, 2560),
        ("drawable-land-xhdpi", 1280, 720), ("drawable-land-xxhdpi", 2560, 1440), ("drawable-sw600dp-land", 2560, 1440),
    ],
    "background": [("drawable-xxhdpi", 1440, 2880), ("drawable-sw600dp", 1440, 2880)],
    "chatroom_background": [("drawable-xxhdpi", 1440, 2880), ("drawable-sw600dp", 1440, 2880)],
    "passcode_background": [("drawable-xxhdpi", 1440, 1440), ("drawable-sw600dp", 1440, 1440)],
}
for key, targets in FULL.items():
    p = find(key)
    if not p:
        continue
    src = load(p)
    for folder, w, h in targets:
        if key == "background":
            # 카톡은 목록 배경을 화면 너비에 맞추고 하단(탭 바 위)에 붙여서 보여줌 → 비율 유지
            img = src.resize((w, round(w * src.height / src.width)), Image.LANCZOS)
        else:
            img = cover(src, w, h)
        save(img.convert("RGB"), folder, f"theme_{key}_image.png")
    applied.append(os.path.basename(p))

# 2) 기본 프로필 ----------------------------------------------------------------
p = find("profile")
if p:
    save(cover(load(p), 240, 240), "drawable-xxhdpi", "theme_profile_01_image.png")
    applied.append(os.path.basename(p))

# 3) 하단 탭 아이콘 (tab_친구 등) ---------------------------------------------
TABS = ["friends", "chats", "now", "shopping", "more", "call", "piccoma"]
for tab in TABS:
    off = find(f"tab_{tab}")
    on = find(f"tab_{tab}_on")
    if not off and not on:
        continue
    off_im = load(off or on)
    on_im = load(on or off)
    for folder, size in (("drawable-xxhdpi", 114), ("drawable-sw600dp", 152)):
        save(contain(off_im, size, 0.9), folder, f"theme_maintab_ico_{tab}_image.png")
        save(contain(on_im, size, 0.9), folder, f"theme_maintab_ico_{tab}_focused_image.png")
    applied += [os.path.basename(x) for x in (off, on) if x]

# 4) 잠금화면 비밀번호 동그라미 ------------------------------------------------
for n in range(1, 5):
    off = find(f"passcode_{n}") or find("passcode")
    on = find(f"passcode_{n}_on") or find("passcode_on")
    if off:
        save(contain(load(off), 132), "drawable-xxhdpi", f"theme_passcode_0{n}_image.png")
        applied.append(os.path.basename(off))
    if on:
        save(contain(load(on), 132), "drawable-xxhdpi", f"theme_passcode_0{n}_checked_image.png")
        applied.append(os.path.basename(on))

# 5) 앱 아이콘 ------------------------------------------------------------------
p = find("app_icon")
if p:
    src = load(p)
    ICON_BG = (255, 247, 220, 255)  # 투명한 부분을 채울 아이콘 배경색 (크림)
    for dens, s in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        sq = Image.new("RGBA", (s, s), ICON_BG)
        sq.alpha_composite(contain(src, s, 0.86))
        save(sq, f"mipmap-{dens}", "ic_launcher.png")
        mask = Image.new("L", (s * 4, s * 4), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, s * 4 - 1, s * 4 - 1), fill=255)
        rd = Image.new("RGBA", (s, s), ICON_BG)
        rd.alpha_composite(contain(src, s, 0.76))
        rnd = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        rnd.paste(rd, (0, 0), mask.resize((s, s), Image.LANCZOS))
        save(rnd, f"mipmap-{dens}", "ic_launcher_round.png")
        # 적응형 아이콘(안드로이드 8+): 레이어 108dp 중 가운데 약 66%만 보이므로
        # 그림은 앞 레이어의 안전 영역 안에 넣고, 뒤 레이어는 단색으로 채움
        a = int(s * 2.25)
        save(Image.new("RGBA", (a, a), ICON_BG), f"mipmap-{dens}", "ic_launcher_background.png")
        save(contain(src, a, 0.58), f"mipmap-{dens}", "ic_launcher_foreground.png")
    applied.append(os.path.basename(p))

# 6) 채팅 말풍선 (9-patch) ------------------------------------------------------
#    둥근 말풍선 + 진한 테두리. 대화 묶음의 첫 말풍선(_01)에는
#    images/bubble_you(.png) 캐릭터를 꼬리 자리(아래 모서리)에 붙임.
#    bubble_me 가 없으면 bubble_you 를 좌우 반전해서 내 말풍선에 사용.
BUBBLE_DIR = "drawable-xxhdpi"
B_R = 54            # 모서리 둥글기 (px, xxhdpi)
B_LW = 6            # 테두리 두께
B_LINE = (60, 45, 35, 255)
B_FILL = {"me": (255, 217, 106, 255), "you": (255, 255, 255, 255)}
B_W, B_H = 2 * B_R + 24, 2 * B_R + 30   # 말풍선 본체 크기 (최소 크기)
CH = 90             # 캐릭터 크기
CH_OUT = 54         # 캐릭터가 말풍선 밖으로 나가는 폭
CH_DROP = 12        # 캐릭터가 말풍선 아래로 내려오는 높이
PAD_X, PAD_Y = 42, 30


def bubble_body(fill):
    S = 4
    im = Image.new("RGBA", (B_W * S, B_H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    h = B_LW * S / 2
    d.rounded_rectangle((h, h, B_W * S - h - 1, B_H * S - h - 1), radius=B_R * S,
                        fill=fill, outline=B_LINE, width=B_LW * S)
    return im.resize((B_W, B_H), Image.LANCZOS)


def ninepatch_you(fill, char):
    """친구 말풍선(왼쪽) 9-patch. char 가 있으면 왼쪽 아래에 캐릭터 합성."""
    ox = CH_OUT                      # 말풍선 본체 시작 x (왼쪽 캐릭터 자리 확보)
    W, H = ox + B_W, B_H + CH_DROP
    art = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    art.alpha_composite(bubble_body(fill), (ox, 0))
    if char is not None:
        c = contain(char, CH)
        art.alpha_composite(c, (ox - CH_OUT + 0, H - CH))
    out = Image.new("RGBA", (W + 2, H + 2), (0, 0, 0, 0))
    out.alpha_composite(art, (1, 1))
    px = out.load()
    BLACK = (0, 0, 0, 255)
    # 가로 늘어나는 구간: 본체 윗변 가운데
    for x in range(ox + B_R + 2, ox + B_W - B_R - 2):
        px[x + 1, 0] = BLACK
    # 세로 늘어나는 구간: 캐릭터보다 위쪽
    for y in range(B_R, min(B_H - B_R, H - CH) - 2):
        px[0, y + 1] = BLACK
    # 글자 영역(내용 패딩)
    for x in range(ox + PAD_X, ox + B_W - PAD_X):
        px[x + 1, H + 1] = BLACK
    for y in range(PAD_Y, B_H - PAD_Y):
        px[W + 1, y + 1] = BLACK
    return out


def mirror_ninepatch(im):
    """좌우 반전하되, 왼쪽(늘림)/오른쪽(패딩) 표시 열은 제자리 유지"""
    f = im.transpose(Image.FLIP_LEFT_RIGHT)
    W = im.width
    for y in range(im.height):
        f.putpixel((0, y), im.getpixel((0, y)))
        f.putpixel((W - 1, y), im.getpixel((W - 1, y)))
    return f


p_you, p_me = find("bubble_you"), find("bubble_me")
ch_you = load(p_you) if p_you else None
ch_me = load(p_me) if p_me else (ch_you.transpose(Image.FLIP_LEFT_RIGHT) if ch_you else None)
for who in ("you", "me"):
    char = ch_you if who == "you" else (ch_me.transpose(Image.FLIP_LEFT_RIGHT) if ch_me else None)
    # 내 말풍선은 친구 말풍선을 만든 뒤 반전 → 캐릭터도 미리 한 번 뒤집어 둠
    for n, c in (("01", char), ("02", None)):
        np_ = ninepatch_you(B_FILL[who], c)
        if who == "me":
            np_ = mirror_ninepatch(np_)
        np_.save(os.path.join(TH, BUBBLE_DIR, f"theme_chatroom_bubble_{who}_{n}_image.9.png"))
applied += [os.path.basename(x) for x in (p_you, p_me) if x]

# 7) 테마 이름 ------------------------------------------------------------------
props = {}
with open(os.path.join(ROOT, "theme.properties"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            props[k.strip()] = v.strip()

pkg = props.get("packageId", "")
if not re.fullmatch(r"[a-z][a-z0-9_]*", pkg):
    sys.exit(f"theme.properties 의 packageId 는 영문 소문자로 시작하고 소문자·숫자·_ 만 쓸 수 있어요: '{pkg}'")

name_ko = props.get("themeName", "My Theme")
name_en = props.get("themeNameEn", name_ko)
for folder, name in (("values", name_en), ("values-ja", name_en), ("values-ko", name_ko)):
    path = os.path.join(TH, folder, "strings.xml")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = escape(name).replace("'", "\\'")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
            f'    <string name="theme_title">{n}</string>\n'
            f'    <string name="app_name">{n}</string>\n</resources>\n'
        )

print("테마 이름:", name_ko, "/", name_en, "/ 패키지: com.kakao.talk.theme." + pkg)
print("적용된 사진:", ", ".join(sorted(set(applied))) if applied else "(없음 — 기본 이미지 사용)")
