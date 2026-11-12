---
name: new-episode
description: Yeni bir episode klasörü ve episode.yaml oluşturur. Kullanıcı yeni video/tema eklemek istediğinde kullan.
argument-hint: "[slug] [tema açıklaması]"
---
1. `episodes/_template/episode.yaml` dosyasını `episodes/$0/episode.yaml` olarak kopyala.
2. Tema: $ARGUMENTS. Alanları doldurmak için concept-planner alt ajanına delege et.
3. Son 20 episode ile tema/preset/başlık çakışması varsa uyar.
4. Gerekli ses katmanları veya Unity preset'i eksikse listele; uydurma dosya yolu yazma.
