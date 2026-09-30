# Estimasi Penggunaan Credit — Rp 100.000

Config yang dipakai (2026-09): DeepSeek v4-pro peak, `text_margin=10`,
`image_margin=4`, `usd_to_idr=18000`, `image_ref_input_usd=0.10`,
`actor_image_cost_usd=0.25`.

Angka = estimasi, memakai representative prompt dari pipeline.
Token text dihitung dengan heuristic `estimate_tokens()` di
`vit_ads_suhu_credits/models/generate_usage.py`.

## Harga per item

| Item | charge Rp | Rp 100k dapat |
|---|---|---|
| Text stage — 1 generate (`action_generate`) | 60 – 270 | — |
| Image — tanpa logo (text2image) | 9.864 | **10 image** |
| Image + logo (1 ref) | 17.064 | **6 image** |
| Image + logo + kemasan (2 ref) | 24.264 | **4 image** |
| Actor image (video, flux-pro v1.1-ultra) | 18.000 | **6 image** |
| Pipeline text-only (7 stage) | ~741 | **135 campaign teks** |

Rumus charge:
- Text: `(input_tk/1M × $1.32 + output_tk/1M × $3.96) × 18000 × 10`
- Image: `((prompt_tk/1000) × $0.005 + harga_image + 0.10×n_ref) × 18000 × 4`
- Actor: `0.25 × 18000 × 4`

## Campaign lengkap (1 market / 1 audience / 1 angle / 1 hook → 4 image + 1 actor)

### Tanpa logo, 4 image — Rp 58.197 / campaign → **1,7 campaign per Rp 100k**

```
text 7 stage   = Rp    741   (1%)
image × 4      = Rp 39.456   (68%)
actor image    = Rp 18.000   (31%)
─────────────────────────────
                  Rp 58.197
```

### Dengan logo + kemasan (2 ref), 4 image — Rp 115.797 / campaign → **0,9 campaign per Rp 100k**

```
text 7 stage   = Rp    741
image × 4      = Rp 97.056
actor image    = Rp 18.000
─────────────────────────────
                  Rp 115.797
```

## Pembaca

- **Image & actor dominan** — text hampir gratis (Rp 741 seluruh pipeline
  vs Rp 39k–97k untuk 4 image).
- **Satu campaign ≈ Rp 58k–116k**, tergantung logo/kemasan.
- **Rp 100k** ≈ **1–2 campaign** penuh, atau ~10 image standalone.
- Komposisi satu campaign: **image 68%, actor image 31%, text 1%**.

## Caveat

- Jumlah image per ads copy ditentukan fan-out `action_split_images` —
  kalau > 4, budget habis lebih cepat.
- `action_generate_actor` dipanggil per video_director; tidak otomatis di
  semua ads copy.
- Estimasi text sensitif terhadap panjang prompt aktual; memakai representasi
  konservatif. Prompt 3× lebih panjang tetap < 5% total biaya campaign.
- **Harga per image adalah unit ekonomi utama** — kendali di `image_margin`
  dan `image_ref_input_usd`, bukan di text.