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
pygame.mixer.init()

# Ekran boyutları main.py içindeki değerlere sabitlendi
GENISLIK, YUKSEKLIK = 1000, 650
ekran = pygame.display.set_mode((GENISLIK, YUKSEKLIK))
pygame.display.set_caption("Kutup Gezgini: Bilgi Avcisi")
saat = pygame.time.Clock()

# Renkler
BEYAZ, SIYAH = (255, 255, 255), (0, 0, 0)
MAVI, BUZ = (30, 144, 255), (200, 230, 255)
KIRMIZI, YESIL, SARI = (220, 20, 60), (34, 139, 34), (255, 215, 0)

# Yazi Tipleri (Standart fontlar)
font_soru = pygame.font.SysFont("arial", 26, bold=True)
font_secenek = pygame.font.SysFont("arial", 22)
font_skor = pygame.font.SysFont("arial", 24, bold=True)
font_buyuk = pygame.font.SysFont("arial", 40, bold=True)

# ==========================================
# 2. DOSYA YUKLEME
# ==========================================
# Web ortamında dizin yapıları farklılık gösterebilir
yol = os.path.dirname(__file__)
resim_yolu = os.path.join(yol, 'resimler')

def yukle_img(isim, g, y):
    # Hem 'resimler/' klasörünü hem de ana dizini kontrol eder
    yollar = [os.path.join(resim_yolu, isim), os.path.join(yol, isim), isim]
    for p in yollar:
        if os.path.exists(p):
            try:
                return pygame.transform.scale(pygame.image.load(p).convert_alpha(), (g, y))
            except:
                pass
    # Dosya bulunamazsa yedek kutu oluşturur
    print(f"Uyari: {isim} yuklenemedi, yedek olusturuluyor.")
    s = pygame.Surface((g, y))
    s.fill((random.randint(100,255), 200, 255))
    return s

arkaplan = yukle_img('arkaplan.png', GENISLIK, YUKSEKLIK)
ayi_img = yukle_img('kutupayisi.png', 70, 70)
npc_imgs = [
    yukle_img('penguen.png', 50, 60), 
    yukle_img('mors.png', 80, 50), 
    yukle_img('baykus.png', 50, 50)
]

# ==========================================
# 3. NESNELER (SINIFLAR)
# ==========================================
class Platform:
    def __init__(self, x, y, g, h=20):
        self.rect = pygame.Rect(x, y, g, h)
    def ciz(self, pencere):
        pygame.draw.rect(pencere, BUZ, self.rect, border_radius=5)
        pygame.draw.rect(pencere, BEYAZ, self.rect, 2, border_radius=5)

class Meteor:
    def __init__(self):
        self.reset()
    def reset(self):
        self.rect = pygame.Rect(random.randint(0, GENISLIK-30), random.randint(-500, -50), 25, 25)
        self.hiz = random.randint(4, 8)
    def dus(self, zorluk):
        self.rect.y += self.hiz + zorluk
        if self.rect.y > YUKSEKLIK: self.reset()
    def ciz(self, pencere):
        pygame.draw.circle(pencere, KIRMIZI, self.rect.center, 12)

class Oyuncu:
    def __init__(self):
        self.reset()
    def reset(self):
        self.rect = pygame.Rect(50, 500, 60, 60)
        self.hiz_y = 0
        self.ziplama_gucu = -14
    def kontrol(self, platformlar):
        tus = pygame.key.get_pressed()
        if tus[pygame.K_LEFT] and self.rect.x > 0: self.rect.x -= 6
        if tus[pygame.K_RIGHT] and self.rect.x < GENISLIK-60: self.rect.x += 6
        
        self.hiz_y += 0.7
        self.rect.y += self.hiz_y
        
        on_ground = False
        for p in platformlar:
            if self.rect.colliderect(p.rect) and self.hiz_y > 0:
                self.rect.bottom = p.rect.top
                self.hiz_y = 0
                on_ground = True
        
        if (tus[pygame.K_SPACE] or tus[pygame.K_UP]) and on_ground:
            self.hiz_y = self.ziplama_gucu

# ==========================================
# 4. SORU BANKASI
# ==========================================
soru_bankasi = [
    {"s": "Kutup ayisiyim derim ne renktir?", "a": ["1-Beyaz", "2-Siyah", "3-Pembe"], "d": 2, "n": "Kutup ayilarinin derisi gunes isisini emmek icin siyahtir!"},
    {"s": "Penguenler nerede yasar?", "a": ["1-Kuzey Kutbu", "2-Guney Kutbu", "3-Orman"], "d": 2, "n": "Penguenler sadece Guney yarim kurede yasarlar."},
    {"s": "Kutup ayisinin tuyleri aslinda ne renktir?", "a": ["1-Beyaz", "2-Seffaf", "3-Gri"], "d": 2, "n": "Tuyler seffaf ve ici bostur, isigi yansittigi icin beyaz gorunur."},
    {"s": "Hangi hayvanin uzun disleri buz kirmaya yarar?", "a": ["1-Mors", "2-Balina", "3-Fok"], "d": 1, "n": "Morslar dislerini buza tutunmak ve delik acmak icin kullanir."},
    {"s": "Kutup tilkisi kisin ne renk olur?", "a": ["1-Kahverengi", "2-Mavi", "3-Beyaz"], "d": 3, "n": "Karda kamufle olmak icin bembeyaz olurlar."},
    {"s": "Narvalin boynuzu aslinda nedir?", "a": ["1-Kemik", "2-Uzun bir dis", "3-Anten"], "d": 2, "n": "O boynuz aslinda 2-3 metreye kadar uzayabilen bir distir!"},
    {"s": "Hangi kus 270 derece kafasini cevirebilir?", "a": ["1-Marti", "2-Kar Baykusu", "3-Kartal"], "d": 2, "n": "Kar baykuslari gozlerini oynatamaz, bu yuzden kafalarini cevirirler."},
    {"s": "Kutup tavsaninin ayaklari neden buyuktur?", "a": ["1-Hizli ucmak", "2-Karda batmamak", "3-Yuzmek"], "d": 2, "n": "Genis ayaklar 'kar ayakkabisi' gorevi gorerek batmayi engeller."},
    {"s": "Okyanusun kanaryasi denen beyaz balina hangisidir?", "a": ["1-Beluga", "2-Mavi Balina", "3-Kopekbaligi"], "d": 1, "n": "Belugalar cok fazla ses cikardiklari icin bu adi almistir."},
    {"s": "Ren geyiklerinin burnu neden kizarir/isinir?", "a": ["1-Utandigi icin", "2-Havayi isitmak icin", "3-Hasta oldugu icin"], "d": 2, "n": "Burunlarindaki damarlar soguk havayi isitır."}
]

# ==========================================
# 5. ANA OYUN MANTIGI
# ==========================================
async def ana_oyun():
    oyuncu = Oyuncu()
    platlar = [
        Platform(0, 600, 1000, 50), 
        Platform(200, 480, 200), 
        Platform(500, 380, 200), 
        Platform(100, 250, 200), 
        Platform(600, 200, 250)
    ]
    meteorlar = [Meteor() for _ in range(5)]
    soru_index, can, skor, durum = 0, 3, 0, "OYUN"
    hata_metni = ""
    
    def npc_olustur():
        p = random.choice(platlar[1:])
        return pygame.Rect(p.rect.centerx-25, p.rect.y-60, 50, 60), random.choice(npc_imgs)

    npc_rect, npc_img = npc_olustur()

    running = True
    while running:
        ekran.blit(arkaplan, (0,0))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
            
            if event.type == pygame.KEYDOWN:
                if (durum == "BITTI" or can <= 0) and event.key == pygame.K_SPACE:
                    await ana_oyun()
                    return
                
                if durum == "BILGI" or durum == "HATA":
                    cevap = 0
                    if event.key == pygame.K_1 or event.key == pygame.K_KP1: cevap = 1
                    elif event.key == pygame.K_2 or event.key == pygame.K_KP2: cevap = 2
                    elif event.key == pygame.K_3 or event.key == pygame.K_KP3: cevap = 3
                    
                    if cevap != 0:
                        if durum == "BILGI":
                            if cevap == soru_bankasi[soru_index]["d"]:
                                skor += 10
                                soru_index += 1
                                if soru_index >= len(soru_bankasi): durum = "BITTI"
                                else:
                                    durum = "OYUN"
                                    npc_rect, npc_img = npc_olustur()
                                    oyuncu.reset()
                            else:
                                durum = "HATA"
                                hata_metni = soru_bankasi[soru_index]["n"]
                                can -= 1
                        elif durum == "HATA":
                            if can > 0: 
                                durum = "OYUN"
                                oyuncu.reset()

        if durum == "OYUN" and can > 0:
            oyuncu.kontrol(platlar)
            for m in meteorlar:
                m.dus(skor//30)
                if oyuncu.rect.colliderect(m.rect):
                    can -= 1; m.reset(); oyuncu.reset()
            if oyuncu.rect.colliderect(npc_rect): durum = "BILGI"

        # Çizimler
        for p in platlar: p.ciz(ekran)
        for m in meteorlar: m.ciz(ekran)
        if durum == "OYUN" or durum == "BILGI": ekran.blit(npc_img, npc_rect)
        ekran.blit(ayi_img, oyuncu.rect)
        
        # Skor Tablosu
        skor_panel = font_skor.render(f"Skor: {skor}  Can: {can}  Soru: {soru_index+1}/10", True, SIYAH)
        ekran.blit(skor_panel, (20, 20))

        if can <= 0:
            msg = font_buyuk.render("CANINIZ BITTI! SPACE: TEKRAR", True, KIRMIZI)
            ekran.blit(msg, (GENISLIK//2 - 250, YUKSEKLIK//2))

        # Paneller
        if durum == "BILGI" or durum == "HATA":
            panel = pygame.Surface((800, 350)); panel.set_alpha(240); panel.fill(SIYAH)
            ekran.blit(panel, (100, 150))
            if durum == "BILGI":
                s_obj = soru_bankasi[soru_index]
                ekran.blit(font_soru.render(s_obj["s"], True, SARI), (120, 180))
                for i, sec in enumerate(s_obj["a"]):
                    ekran.blit(font_secenek.render(sec, True, BEYAZ), (150, 260 + i*40))
            else:
                ekran.blit(font_soru.render("YANLIS CEVAP!", True, KIRMIZI), (120, 180))
                ekran.blit(font_secenek.render(hata_metni, True, BEYAZ), (120, 250))
                ekran.blit(font_secenek.render("Devam etmek icin 1, 2 veya 3'e bas.", True, YESIL), (120, 380))

        if durum == "BITTI":
            panel = pygame.Surface((GENISLIK, YUKSEKLIK)); panel.set_alpha(200); panel.fill(YESIL)
            ekran.blit(panel, (0,0))
            ekran.blit(font_buyuk.render("TEBRIKLER! KUTUP GEZGINI OLDUN!", True, BEYAZ), (200, 250))
            ekran.blit(font_secenek.render("Tekrar oynamak icin SPACE", True, BEYAZ), (380, 350))

        pygame.display.flip()
        saat.tick(60)
        await asyncio.sleep(0)

asyncio.run(ana_oyun())
