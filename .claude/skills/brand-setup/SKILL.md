---
name: brand-setup
description: Kanal markasını (ad, handle, niş, dil, ton, haftalık adet, başlık kalıbı, CTA, font, logo) config/brand.yaml'a kurar veya değiştirir. Repo fork'landığında veya klonlandığında, `channel.handle` hâlâ placeholder iken ya da kullanıcı marka/rebrand istediğinde kullan.
argument-hint: "[--local]"
---
1. `config/brand.yaml` ve varsa `config/brand.local.yaml` dosyalarını oku. Eksik veya placeholder alanları kullanıcıya tek seferde sor: kanal adı, handle, niş, dil, ton, haftalık long sayısı, başlık kalıbı, açıklama footer'ı, CTA metni, font dosyası, logo (opsiyonel). Değer uydurma; cevaplanmayan alanı olduğu gibi bırak.
2. Hedef dosya: kalıcı marka (fork) için `config/brand.yaml`. `$ARGUMENTS` içinde `--local` varsa veya değişiklik upstream'e commit edilmeyecekse `config/brand.local.yaml` (yalnızca değişen alanlar; git'e girmez).
3. Dil veya niş değiştiyse `config/use_cases.yaml` içindeki `title_suffix` değerlerini yeni dile/nişe uyarla; o dosyada başka alana dokunma.
4. `short.font` ve `watermark.file` yolları diskte var mı kontrol et; yoksa eksik asset olarak listele, yol uydurma.
5. Mevcut `episodes/*/episode.yaml` dosyalarını yeniden yazma. Eski markayla yazılmış başlık, açıklama veya CTA varsa yalnızca listele.
6. Özet ver: değişen alanlar, eksik asset'ler, elle yapılacaklar (YouTube Studio kanal adı/handle bu repodan yönetilmez).
