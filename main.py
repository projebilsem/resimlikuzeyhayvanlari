# -*- coding: utf-8 -*-
import pygame
import os
import sys
import random
import asyncio

# ==========================================
# 1. BASLATMA VE AYARLAR
# ==========================================
pygame.init()

# Web ortaminda mixer bazen hata verir, o yuzden guvenli baslat
try:
    pygame.mixer.init()
except Exception:
    pass

GENISLIK, YUKSEKLIK = 1000, 650
ekran = pygame.display.set_mode((GENISLIK, YUKSEKLIK))
pygame.display.set_caption("Kutup Gezgini: Bilgi Avcisi")
saat = pygame.time.Clock()

# Renkler
BEYAZ = (255, 255, 255)
SIYAH = (0, 0, 0)
MAVI = (30, 144, 255)
BUZ = (200, 230, 255)
KIRMIZI = (220, 20, 60)
YESIL = (34, 139, 34)
SARI = (255, 215, 0)
LACIVERT = (20, 35, 55)

# Fontlar
font_soru = pygame.font.SysFont("arial", 26, bold=True)
font_secenek = pygame.font.SysFont("arial", 22)
font_skor = pygame.font.SysFont("arial", 24, bold=True)
font_buyuk = pygame.font.SysFont("arial", 40, bold=True)
font_orta = pygame.font.SysFont("arial", 30, bold=True)

# ==========================================
# 2. DOSYA YUKLEME
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def dosya_yolu_bul(isim):
    adaylar = [
        os.path.join(BASE_DIR, isim),
        os.path.join(BASE_DIR, "resimler", isim),
        os.path.join(".", isim),
        os.path.join("./resimler", isim),
    ]
    for yol in adaylar:
        if os.path.exists(yol):
            return yol
    return None

def yukle_img(isim, genislik, yukseklik, saydam=True):
    yol = dosya_yolu_bul(isim)
    if yol:
        try:
            img = pygame.image.load(yol)
            img = img.convert_alpha() if saydam else img.convert()
            return pygame.transform.smoothscale(img, (genislik, yukseklik))
        except Exception:
            pass

    # Dosya bulunamazsa yedek gorsel
    yuzey = pygame.Surface((genislik, yukseklik), pygame.SRCALPHA)
    yuzey.fill((240, 240, 240, 180))
    pygame.draw.rect(yuzey, (120, 120, 120), yuzey.get_rect(), 2, border_radius=8)
    return yuzey

arkaplan = yukle_img("arkaplan.png", GENISLIK, YUKSEKLIK, saydam=False)
ayi_img = yukle_img("kutupayisi.png", 70, 70)
penguen_img = yukle_img("penguen.png", 50, 70)
mors_img = yukle_img("mors.png", 90, 60)
baykus_img = yukle_img("baykus.png", 60, 60)
npc_imgs = [penguen_img, mors_img, baykus_img]

# ==========================================
# 3. NESNELER
# ==========================================
class Platform:
    def __init__(self, x, y, g, h=20):
        self.rect = pygame.Rect(x, y, g, h)

    def ciz(self, pencere):
        pygame.draw.rect(pencere, BUZ, self.rect, border_radius=8)
        pygame.draw.rect(pencere, BEYAZ, self.rect, 2, border_radius=8)

class Meteor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.rect = pygame.Rect(
            random.randint(0, GENISLIK - 30),
            random.randint(-500, -50),
            25,
            25
        )
        self.hiz = random.randint(4, 8)

    def dus(self, zorluk):
        self.rect.y += self.hiz + zorluk
        if self.rect.y > YUKSEKLIK:
            self.reset()

    def ciz(self, pencere):
        pygame.draw.circle(pencere, KIRMIZI, self.rect.center, 12)
        pygame.draw.circle(pencere, SARI, self.rect.center, 6)

class Oyuncu:
    def __init__(self):
        self.genislik = 60
        self.yukseklik = 60
        self.ziplama_gucu = -14
        self.reset()

    def reset(self):
        self.rect = pygame.Rect(50, 500, self.genislik, self.yukseklik)
        self.hiz_y = 0

    def kontrol(self, platformlar):
        tus = pygame.key.get_pressed()

        if tus[pygame.K_LEFT] and self.rect.x > 0:
            self.rect.x -= 6
        if tus[pygame.K_RIGHT] and self.rect.x < GENISLIK - self.genislik:
            self.rect.x += 6

        self.hiz_y += 0.7
        self.rect.y += self.hiz_y

        on_ground = False
        for p in platformlar:
            if self.rect.colliderect(p.rect) and self.hiz_y > 0:
                if self.rect.bottom <= p.rect.bottom:
                    self.rect.bottom = p.rect.top
                    self.hiz_y = 0
                    on_ground = True

        if self.rect.bottom > YUKSEKLIK:
            self.rect.bottom = YUKSEKLIK
            self.hiz_y = 0
            on_ground = True

        if tus[pygame.K_SPACE] and on_ground:
            self.hiz_y = self.ziplama_gucu

# ==========================================
# 4. SORU BANKASI
# ==========================================
soru_bankasi = [
    {"s": "Kutup ayisinin derisi ne renktir?", "a": ["1-Beyaz", "2-Siyah", "3-Pembe"], "d": 2, "n": "Kutup ayilarinin derisi gunes isisini emmek icin siyahtir."},
    {"s": "Penguenler nerede yasar?", "a": ["1-Kuzey Kutbu", "2-Guney Kutbu", "3-Orman"], "d": 2, "n": "Penguenler dogal olarak Guney Yarim Kure'de yasar."},
    {"s": "Kutup ayisinin tuyleri aslinda ne renktir?", "a": ["1-Beyaz", "2-Seffaf", "3-Gri"], "d": 2, "n": "Tuyler seffaf ve ici bostur; beyaz gorunmesinin nedeni isigi yansitmasidir."},
    {"s": "Hangi hayvanin uzun disleri buzda tutunmaya yarar?", "a": ["1-Mors", "2-Balina", "3-Fok"], "d": 1, "n": "Morslar uzun dislerini buzda tutunmak icin kullanir."},
    {"s": "Kutup tilkisi kis aylarinda genellikle ne renk olur?", "a": ["1-Kahverengi", "2-Mavi", "3-Beyaz"], "d": 3, "n": "Kis aylarinda beyaz renge donuserek kamufle olur."},
    {"s": "Narvalin boynuzu aslinda nedir?", "a": ["1-Kemik", "2-Uzun bir dis", "3-Anten"], "d": 2, "n": "Narvalin boynuzu aslinda uzamis bir distir."},
    {"s": "Hangi kus basini cok genis bir aciyla cevirebilir?", "a": ["1-Marti", "2-Kar Baykusu", "3-Kartal"], "d": 2, "n": "Baykuslar baslarini cok genis bir aciyla cevirebilir."},
    {"s": "Kutup tavsaninin ayaklari neden buyuktur?", "a": ["1-Hizli ucmak", "2-Karda batmamak", "3-Yuzmek"], "d": 2, "n": "Genis ayaklari kar ustunde daha rahat hareket etmesini saglar."},
    {"s": "Okyanusun kanaryasi denen hayvan hangisidir?", "a": ["1-Beluga", "2-Mavi Balina", "3-Kopekbaligi"], "d": 1, "n": "Belugalar cikardiklari sesler nedeniyle bu adla anilir."},
    {"s": "Ren geyiklerinin burnu neden isinir?", "a": ["1-Utandigi icin", "2-Havayi isitmak icin", "3-Hasta oldugu icin"], "d": 2, "n": "Burundaki damar yapisi soguk havayi akcigerlere gitmeden once isitir."}
]

# ==========================================
# 5. YARDIMCI FONKSIYONLAR
# ==========================================
def oyun_durumu_olustur():
    oyuncu = Oyuncu()
    platformlar = [
        Platform(0, 600, 1000, 50),
        Platform(200, 480, 200),
        Platform(500, 380, 200),
        Platform(100, 250, 200),
        Platform(600, 200, 250),
    ]
    meteorlar = [Meteor() for _ in range(5)]

    return {
        "oyuncu": oyuncu,
        "platformlar": platformlar,
        "meteorlar": meteorlar,
        "soru_index": 0,
        "can": 3,
        "skor": 0,
        "durum": "ACILIS",   # ACILIS, OYUN, BILGI, HATA, BITTI
        "hata_metni": "",
        "npc_rect": None,
        "npc_img": None
    }

def npc_olustur(platformlar):
    p = random.choice(platformlar[1:])
    img = random.choice(npc_imgs)
    if img == mors_img:
        rect = pygame.Rect(p.rect.centerx - 40, p.rect.y - 55, 80, 50)
    elif img == penguen_img:
        rect = pygame.Rect(p.rect.centerx - 25, p.rect.y - 70, 50, 70)
    else:
        rect = pygame.Rect(p.rect.centerx - 30, p.rect.y - 60, 60, 60)
    return rect, img

def metni_satirlara_bol(font, metin, max_genislik):
    kelimeler = metin.split()
    satirlar = []
    aktif = ""

    for kelime in kelimeler:
        deneme = aktif + (" " if aktif else "") + kelime
        if font.size(deneme)[0] <= max_genislik:
            aktif = deneme
        else:
            if aktif:
                satirlar.append(aktif)
            aktif = kelime

    if aktif:
        satirlar.append(aktif)

    return satirlar

def panel_ciz(ekran, x, y, w, h, alpha=220):
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((10, 20, 35, alpha))
    pygame.draw.rect(panel, (230, 240, 255), panel.get_rect(), 3, border_radius=16)
    ekran.blit(panel, (x, y))

# ==========================================
# 6. ANA OYUN
# ==========================================
async def ana_oyun():
    veri = oyun_durumu_olustur()
    veri["npc_rect"], veri["npc_img"] = npc_olustur(veri["platformlar"])

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if veri["durum"] == "ACILIS":
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        veri["durum"] = "OYUN"

                elif veri["durum"] == "BITTI":
                    if event.key == pygame.K_SPACE:
                        veri = oyun_durumu_olustur()
                        veri["npc_rect"], veri["npc_img"] = npc_olustur(veri["platformlar"])

                elif veri["durum"] in ("BILGI", "HATA"):
                    cevap = 0
                    if event.key == pygame.K_1:
                        cevap = 1
                    elif event.key == pygame.K_2:
                        cevap = 2
                    elif event.key == pygame.K_3:
                        cevap = 3

                    if cevap:
                        if veri["durum"] == "BILGI":
                            soru = soru_bankasi[veri["soru_index"]]
                            if cevap == soru["d"]:
                                veri["skor"] += 10
                                veri["soru_index"] += 1

                                if veri["soru_index"] >= len(soru_bankasi):
                                    veri["durum"] = "BITTI"
                                else:
                                    veri["durum"] = "OYUN"
                                    veri["oyuncu"].reset()
                                    veri["npc_rect"], veri["npc_img"] = npc_olustur(veri["platformlar"])
                            else:
                                veri["durum"] = "HATA"
                                veri["hata_metni"] = soru["n"]
                                veri["can"] -= 1
                                if veri["can"] <= 0:
                                    veri["durum"] = "BITTI"

                        elif veri["durum"] == "HATA":
                            if veri["can"] > 0:
                                veri["durum"] = "OYUN"
                                veri["oyuncu"].reset()
                            else:
                                veri["durum"] = "BITTI"

        # OYUN GUNCELLEME
        if veri["durum"] == "OYUN":
            veri["oyuncu"].kontrol(veri["platformlar"])

            for meteor in veri["meteorlar"]:
                meteor.dus(veri["skor"] // 30)

                if veri["oyuncu"].rect.colliderect(meteor.rect):
                    veri["can"] -= 1
                    meteor.reset()
                    veri["oyuncu"].reset()

                    if veri["can"] <= 0:
                        veri["durum"] = "BITTI"

            if veri["npc_rect"] and veri["oyuncu"].rect.colliderect(veri["npc_rect"]):
                veri["durum"] = "BILGI"

        # CIZIM
        ekran.blit(arkaplan, (0, 0))

        for p in veri["platformlar"]:
            p.ciz(ekran)

        if veri["durum"] == "OYUN":
            for meteor in veri["meteorlar"]:
                meteor.ciz(ekran)

        if veri["npc_rect"] and veri["durum"] in ("OYUN", "BILGI"):
            ekran.blit(veri["npc_img"], veri["npc_rect"])

        ekran.blit(ayi_img, veri["oyuncu"].rect)

        skor_yazi = font_skor.render(
            f"Skor: {veri['skor']}   Can: {veri['can']}   Soru: {min(veri['soru_index'] + 1, len(soru_bankasi))}/{len(soru_bankasi)}",
            True,
            SIYAH
        )
        ekran.blit(skor_yazi, (20, 20))

        # Acilis ekrani
        if veri["durum"] == "ACILIS":
            panel_ciz(ekran, 150, 150, 700, 320, 215)
            baslik = font_buyuk.render("KUTUP GEZGINI: BILGI AVCISI", True, SARI)
            ekran.blit(baslik, (190, 190))

            satir1 = font_orta.render("Kutup ayisi ile platformlarda ilerle,", True, BEYAZ)
            satir2 = font_orta.render("hayvanlara ulas ve sorulari cevapla.", True, BEYAZ)
            satir3 = font_secenek.render("Hareket: Sol - Sag Ok | Zipla: Space", True, BUZ)
            satir4 = font_secenek.render("Baslamak icin SPACE veya ENTER tusuna bas.", True, YESIL)

            ekran.blit(satir1, (230, 270))
            ekran.blit(satir2, (220, 310))
            ekran.blit(satir3, (300, 370))
            ekran.blit(satir4, (260, 410))

        # Soru / Hata paneli
        if veri["durum"] in ("BILGI", "HATA"):
            panel_ciz(ekran, 90, 140, 820, 360, 230)

            if veri["durum"] == "BILGI":
                soru = soru_bankasi[veri["soru_index"]]
                satirlar = metni_satirlara_bol(font_soru, soru["s"], 760)

                y = 175
                for satir in satirlar:
                    ekran.blit(font_soru.render(satir, True, SARI), (120, y))
                    y += 36

                y += 20
                for secenek in soru["a"]:
                    ekran.blit(font_secenek.render(secenek, True, BEYAZ), (150, y))
                    y += 48

                ekran.blit(
                    font_secenek.render("Cevap icin 1, 2 veya 3 tusuna bas.", True, YESIL),
                    (150, 425)
                )

            else:
                ekran.blit(font_buyuk.render("YANLIS CEVAP!", True, KIRMIZI), (280, 175))

                satirlar = metni_satirlara_bol(font_secenek, veri["hata_metni"], 720)
                y = 270
                for satir in satirlar:
                    ekran.blit(font_secenek.render(satir, True, BEYAZ), (130, y))
                    y += 36

                ekran.blit(
                    font_secenek.render("Devam etmek icin 1, 2 veya 3 tuslarindan birine bas.", True, YESIL),
                    (130, 425)
                )

        # Bitis ekrani
        if veri["durum"] == "BITTI":
            panel_ciz(ekran, 170, 180, 660, 250, 220)

            if veri["can"] <= 0 and veri["soru_index"] < len(soru_bankasi):
                mesaj1 = font_buyuk.render("OYUN BITTI!", True, KIRMIZI)
                mesaj2 = font_orta.render("Canlarin tukenmis durumda.", True, BEYAZ)
            else:
                mesaj1 = font_buyuk.render("TEBRIKLER!", True, YESIL)
                mesaj2 = font_orta.render("Tum sorulari dogru tamamladin.", True, BEYAZ)

            mesaj3 = font_orta.render(f"Toplam Skor: {veri['skor']}", True, SARI)
            mesaj4 = font_secenek.render("Tekrar oynamak icin SPACE tusuna bas.", True, BUZ)

            ekran.blit(mesaj1, (330, 220))
            ekran.blit(mesaj2, (285, 290))
            ekran.blit(mesaj3, (390, 340))
            ekran.blit(mesaj4, (300, 390))

        pygame.display.flip()
        saat.tick(60)
        await asyncio.sleep(0)

    pygame.quit()
    try:
        sys.exit()
    except SystemExit:
        pass

asyncio.run(ana_oyun())
