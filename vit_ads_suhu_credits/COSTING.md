# Ads Suhu — Token / Image Costing

Review + refactor costing agar tidak menjual di bawah biaya vendor.
Tertulis 2026-09-30. Semua harga dicek dari sumber resmi pada tanggal itu.

## Ringkasan masalah lama

| Masalah | Lokasi lama | Dampak |
|---|---|---|
| Harga DeepSeek `$0.27/$0.07/$1.10 per 1M` sudah obsolete | `generate_usage.py:42-43` | Charge di bawah biaya aktual |
| Unit campur: token vs IDR vs integer credit | `TOKENS_PER_CREDIT`, `MIN_CREDIT`, `product.credit_amount` | Ledger menyesatkan |
| Margin hardcode: text 10x, image 4x | `generate_usage.py:66`, `image_generator.py:84` | Tidak bisa disesuaikan tanpa release |
| FX hardcode `17000` dua tempat; kode `res.currency` mati | `generate_usage.py:67`, `image_generator.py:76` | Kurs tidak akurat |
| Precedence bug `description or "" + features or ""` | `generate_usage.py:92` | Tokens output kurang dihitung |
| Cost dihitung dari `self.input` saja, system prompt + template tidak termasuk | semua `action_generate` | Undercount ke sisi vendor |
| `/edit` + reference images (logo/kemasan) tidak dihitung biaya image input | `image_generator.py:82` | Rugi saat pakai brand asset |
| `cache_hit=False` hardcoded | semua pemanggil | Tidak ikut harga turun cache |
| TOCTOU: cek saldo sebelum, charge setelah, tanpa lock | `generate_usage.py:86-101` | Bisa negatif tanpa batas |
| `partner_id` kosong → billing dilewati | `if self.partner_id and ...` | Generate gratis |

## Harga resmi saat penulisan (2026-09)

### DeepSeek (per 1M token) — model baru: `deepseek-flash` & `deepseek-v4-pro`

Model `deepseek-chat` (legacy, dipakai repo) dilayani sebagai `deepseek-flash`,
dibill harga Flash. Kode basis di-set ke harga **v4-pro peak** (paling mahal,
anti-rugi) — bisa diturunkan per config.

| Model | bucket | input cache-hit | input cache-miss | output |
|---|---|---|---|---|
| `deepseek-flash` | off-peak | $0.003 | $0.15 | $0.60 |
| `deepseek-flash` | peak | $0.006 | $0.30 | $1.20 |
| `deepseek-v4-pro` | off-peak | $0.022 | $0.66 | $1.98 |
| `deepseek-v4-pro` | peak | $0.044 | $1.32 | $3.96 |

Peak hours: 01:00–04:00 & 06:00–10:00 UTC, Senin–Jumat, kecuali hari libur CN.

### fal `gpt-image-1.5` (text2image & edit)

- Text input: $0.005 / 1K token = **$5/M** (sama dengan `_count_input_tokens * 0.005`)
- Text output (reasoning): $0.010 / 1K = **$10/M**
- Image per output:

| quality | 1024x1024 | 1024x1536 | 1536x1024 |
|---|---|---|---|
| low | $0.009 | — | — |
| medium | $0.034 | $0.051 | $0.050 |
| high | $0.133 | $0.200 | $0.199 |

- `/edit` : image_urls (reference) di-charge sebagai **image input tokens**.
  Tidak ada angka resmi per image → surcharge konfigurable `image_ref_input_usd`,
  default `0.10` USD per reference image.

## Perubahan

### `vit_ads_suhu_credits/models/generate_usage.py`

- `TOKENS_PER_CREDIT` + `total_credit_used` — dibuang (unit tanpa pemakai).
- Semua harga dari `ir.config_parameter` lewat `_pricing(env)` — default
  `_DEFAULT_*` di modul, konservatif (v4-pro peak).
- `calculate_deepseek_cost()` — harga baru, FX + margin dari config.
- Helper `charge_usage(records, env, name, input, output)` — satu titik billing.
- `StageUsageMixin` — 7 class duplikat pembilongan diganti satu mixin
  (`market_mapper`, `audience_profiler`, `angle_hook`, `hook`, `ads_copy`,
  `video_director`).
- Fix precedence: `(self.description or "") + (self.features or "")`.

### `vit_ads_suhu_inherit/model/image_generator.py`

- FX baca `usd_to_idr` (fallback `image_usd_to_idr`).
- Margin baca `image_margin` dari config.
- `/edit` + reference images → `image_cost_usd += image_ref_input_usd * len(assets)`.
- `brand_assets` dihitung sekali, dipakai untuk cost + payload.

### `vit_ads_suhu_inherit/data/params.xml`

9 key baru, `noupdate="1"`:

| key | default | keterangan |
|---|---|---|
| `usd_to_idr` | 17000 | kurs global text path |
| `text_margin` | 10 | mark up text |
| `deepseek_input_usd_per_1m` | 1.32 | v4-pro peak, cache miss |
| `deepseek_cache_hit_usd_per_1m` | 0.044 | v4-pro peak, cache hit |
| `deepseek_output_usd_per_1m` | 3.96 | v4-pro peak |
| `image_margin` | 4 | mark up image |
| `image_ref_input_usd` | 0.10 | /edit per reference image |
| `image_quality` | high | sudah ada |
| `image_size` | 1024x1024 | sudah ada |

## Test yang ditaruh sekali jalan (assert-based, tanpa framework)

1. Text resale (10x) menutup bill v4-pro peak.
2. Flash dibill lebih rendah → customer dikenai peak, vendor bill lebih murah.
3. Image resale (4x) menutup high 1024x1024.
4. `/edit` + 2 ref: surcharge $0.20 ditambah, tetap tertutup.
5. Edge 1536x1024 + 2 ref tertutup.
6. Default >= harga legacy lama.
7. Precedence bug fix terverifikasi.

## Catatan untuk keputusan bisnis

- **Model DeepSeek aktual**. Default = v4-pro peak (anti-rugi). Kalau akun
  sebenarnya `deepseek-flash` (jauh lebih murah), customer dikenai
  4–9x lipat vendor. Aman dari rugi, margin efektif membengkak.
  Opsional turunkan `deepseek_input_usd_per_1m` ke `0.30` (flash peak) /
  `0.15` (off-peak) untuk charge yang adil.
- **Belum tuntas (di luar scope review ini)**:
  - TOCTOU / `SELECT ... FOR UPDATE` saat cek saldo.
  - `partner_id` falsy → generate gratis masih ada.
  - Cost estimasi masih heuristic `estimate_tokens` — bukan tokenizer asli.
  - Biaya system prompt + template belum dimasukkan ke input (undercount
    sisi vendor; margin menutup).