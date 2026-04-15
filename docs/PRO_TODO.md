# SCAN Professional TODO

Bu liste, mevcut tasarimi koruyarak projeyi profesyonel surume tasimak icin hazirlandi.

## Sabit Kurallar

- Pencere boyutu sabit kalacak.
- Mevcut ana yerlesim bozulmayacak.
- Yeni ozellikler varsa sadece bos alan mantigiyla yerlestirilecek.
- Gereksiz "kutu icinde kutu" tasarimindan kacilacak.
- Islem Merkezi ekraninin mevcut gorsel dili korunacak.

## Faz 1 - Guvenli Profesyonellesme

- [x] Ayarlari sabit `C:\scanapp` yerine kullaniciya uygun uygulama klasorune tasima
- [x] Eski ayar dosyasi varsa geriye donuk uyumlulukla tasima
- [x] Islem gecmisini kalici hale getirme
- [ ] JSON okuma hatalarinda daha iyi kurtarma ve kullanici bilgilendirmesi
- [x] README tarafindaki ayar yolu bilgisini guncelleme
- [x] UTF-8 icerik dogrulamasini yapma

## Faz 2 - Kod Kalitesi

- [x] uygulama katalogu ve alias tanimlarini ayri module tasima
- [x] ayar, gecmis ve dil yardimcilarini ayri modullere ayirma
- [x] eslesme mantigini ayri modula tasima
- [x] `winget` sorgularini servis katmanina ayirma
- [x] registry tarama ve detay okumayi servis katmanina ayirma
- [x] saf islem komutu ve sonuc yardimcilarini ayri module tasima
- [x] islem akis karar mantigini controller katmanina ayirma
- [x] UI bagli dil ve placeholder metin yardimcilarini ayirma
- [x] UI bagli islem sunum katmanini ayirma
- [x] moduler katmanlara tip ipuclari ekleme
- [ ] ana uygulama dosyasinda secili bolgelere tip ipuclari ekleme
- [ ] temel loglama sistemi ekleme

## Faz 3 - Urun Kalitesi

- [ ] `winget search` ile katalog disi uygulama arama
- [ ] favori uygulamalar
- [ ] guncelleme mevcut rozeti
- [ ] islem gecmisi disa aktarma
- [ ] daha anlasilir hata mesajlari
- [ ] sessiz kurulum secenekleri
- [ ] kaynak secimi destegi

## Faz 4 - Test ve Dagitim

- [x] katalog ve saf islem yardimcilari icin test
- [x] alias eslesme mantigi icin test
- [x] `winget` cikti ayrisma testleri
- [x] ayar ve gecmis yukleme testleri
- [x] controller karar mantigi icin test
- [x] presentation yardimcilari icin test
- [x] UI presenter yardimcilari icin test
- [ ] paketleme surecini netlestirme
- [ ] surum notu ve changelog sistemi

## UI Notlari

- Ust bosluklar ve sag panel gibi alanlar ileride dikkatli kullanilabilir.
- Liste panellerinin yuksekligini arttiracak veya ekran kaydiracak eklemeler yapilmayacak.
- Yeni kontrol eklenirse once mevcut bos alana sigma kontrolu yapilacak.
