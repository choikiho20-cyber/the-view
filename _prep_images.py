# _research 원본(야놀자 ota/y*, 여기어때 ota/g*, 에어비앤비 airbnb/a*) → images/ (사이트가 쓰는 사진). 자르기 + 색 통일.
# 실행: python -X utf8 _prep_images.py   — 사진을 바꾸고 싶으면 아래 표만 고친다. 촬영본이 오면 images/<이름>.jpg 를 그냥 덮어쓴다.
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).parent
R = ROOT / "_research"
OUT = ROOT / "images"
OUT.mkdir(exist_ok=True)

# 이름: (원본, 자를 비율 상자 x0 y0 x1 y1 — None이면 전체)
PHOTOS = {
    "hero":           ("airbnb/a11_tour.jpg",      (0.00, 0.12, 1.00, 0.92)),   # 테라스 파라솔 아래 긴 식탁과 호수 (PC 첫 화면)
    "hero-m":         ("airbnb/a43_yard.jpg",      (0.22, 0.00, 0.78, 1.00)),   # 노을 디딤돌 길 세로 (폰 첫 화면)
    "front":          ("ota/y04_fac1.jpg",         None),                        # 벽돌집 정면, 파란 하늘
    "front-lawn":     ("ota/y09_fac5.jpg",         None),                        # 유리온실과 잔디
    "terrace":        ("ota/y06_fac3.jpg",         None),                        # 데크 파라솔
    "living":         ("airbnb/a17_living.jpg",    None),                        # 거실 천장→바닥 (스크롤 훑기)
    "living-sofa":    ("ota/g02.jpg",              None),
    "living-chair":   ("ota/g01.jpg",              None),
    "living-view":    ("airbnb/a19_living.jpg",    None),
    "kitchen":        ("ota/y18_room9.jpg",        None),
    "kitchen2":       ("airbnb/a76_kitchen.jpg",   None),
    "dining-table":   ("ota/y21_room12.jpg",       None),                        # 온실 식탁, 잔디 보임
    "glass":          ("airbnb/a69_patio.jpg",     None),                        # 온실 안, 호수 쪽으로 열린 문
    "glass-out":      ("airbnb/a22_dining.jpg",    None),                        # 온실 밖, 그릴
    "glass-night":    ("airbnb/a60_patio.jpg",     None),                        # 밤 조명 줄
    "glass-party":    ("airbnb/a70_patio.jpg",     None),                        # 칠순 풍선
    "glass-balloons": ("airbnb/a68_patio.jpg",     None),
    "glass-table":    ("airbnb/a69_patio.jpg",     (0.00, 0.20, 1.00, 1.00)),
    "bed-main":       ("ota/y16_room7.jpg",        None),                        # 안방 퀸
    "bed-twin":       ("airbnb/a30_bed2.jpg",      None),
    "bed-view":       ("ota/y15_room6.jpg",        None),                        # 창가 의자와 침대
    "bed-bunk":       ("airbnb/a04_tour.jpg",      None),
    "bath":           ("airbnb/a07_tour.jpg",      None),
    "bath2":          ("airbnb/a08_tour.jpg",      None),
    "lawn-lake":      ("airbnb/a36_yard.jpg",      (0.00, 0.36, 1.00, 1.00)),   # 정원 끝 울타리와 호수 (하늘 잘라냄)
    "lawn-lake2":     ("airbnb/a52_yard.jpg",      None),
    "lawn-path":      ("airbnb/a53_yard.jpg",      None),                        # 디딤돌 길과 호수
    "garden-roses":   ("airbnb/a41_yard.jpg",      None),
    "garden-arch":    ("airbnb/a55_yard.jpg",      None),                        # 장미 아치, 대문
    "garden-gate":    ("airbnb/a55_yard.jpg",      (0.10, 0.00, 0.90, 1.00)),
    "garden-flowers": ("airbnb/a44_yard.jpg",      None),
    "sunset":         ("airbnb/a43_yard.jpg",      None),
    "sunset-grill":   ("airbnb/a26_dining.jpg",    None),
    "grill":          ("airbnb/a24_dining.jpg",    None),
    "pool":           ("airbnb/a47_yard.jpg",      None),
    "winter":         ("airbnb/a66_patio.jpg",     None),
    "lake-table":     ("airbnb/a13_tour.jpg",      None),
    "morning":        ("airbnb/a49_yard.jpg",      None),
    "chair-view":     ("ota/g03.jpg",              None),
    "piano":          ("ota/y17_room8.jpg",        None),
}


def grade(im):
    im = ImageEnhance.Color(im).enhance(0.84)
    im = ImageEnhance.Contrast(im).enhance(0.95)
    r, g, b = im.split()
    r = r.point(lambda v: min(255, int(v * 1.02 + 2)))
    b = b.point(lambda v: int(v * 0.97))
    return Image.merge("RGB", (r, g, b))


for name, (src, box) in PHOTOS.items():
    im = Image.open(R / src).convert("RGB")
    if box:
        W, H = im.size
        im = im.crop((int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)))
    im = grade(im)
    if im.width < 1600 and im.width >= 700:  # ponytail: 단순 확대+샤픈. 화면 꽉 채우는 장면은 촬영본으로 교체
        im = im.resize((1600, int(im.height * 1600 / im.width)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 50, 2))
    elif im.width > 2048:
        im.thumbnail((2048, 4096))
    im.save(OUT / f"{name}.jpg", quality=90)
    print(name, im.size)
