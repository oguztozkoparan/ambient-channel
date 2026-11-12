---
name: weekly-batch
description: Haftalık episode batch'ini (adet config/brand.yaml'dan) planlar, build eder ve upload checklist'i üretir.
disable-model-invocation: true
---
1. `config/brand.yaml` `channel.handle` placeholder ise önce `/brand-setup`. concept-planner ile `cadence.longs_per_week` kadar farklı tema öner (çoğu `general`, en fazla `cadence.max_variants_per_week` `sleep`/`focus` varyantı); kullanıcıya tek liste olarak göster ve onay al (tek onay noktası bu).
2. Onaylanan her tema için `/new-episode` adımlarını uygula.
3. Her episode için `/build-episode` adımlarını sırayla uygula; onay bekleme.
4. `output/week-<ISO hafta>/upload-checklist.md` yaz: önerilen yayın günü/saati (haftaya yayılmış), başlık, açıklama, tag, chapter, thumbnail yolu, short yolu ve "Altered or synthetic content" sorusunun cevabı (Unity render → hayır; istisna varsa gerekçesi).
