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
        save(cover(src, w, h).convert("RGB"), folder, f"theme_{key}_image.png")
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
    for dens, s in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        sq = cover(src, s, s)
        save(sq, f"mipmap-{dens}", "ic_launcher.png")
        mask = Image.new("L", (s * 4, s * 4), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, s * 4 - 1, s * 4 - 1), fill=255)
        rnd = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        rnd.paste(sq, (0, 0), mask.resize((s, s), Image.LANCZOS))
        save(rnd, f"mipmap-{dens}", "ic_launcher_round.png")
        a = int(s * 2.25)  # 적응형 아이콘: 사진을 전체 레이어로 사용
        full = cover(src, a, a)
        save(full, f"mipmap-{dens}", "ic_launcher_background.png")
        save(Image.new("RGBA", (a, a), (0, 0, 0, 0)), f"mipmap-{dens}", "ic_launcher_foreground.png")
    applied.append(os.path.basename(p))

# 6) 테마 이름 ------------------------------------------------------------------
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
