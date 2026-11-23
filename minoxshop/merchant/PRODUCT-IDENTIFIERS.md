# Product identifiers (Minox Shop)

## Verified retail GTINs (manufacturer pack)
| Product id | Brand | GTIN-12 | Notes |
|---|---|---|---|
| `rogaine-single-man` | Rogaine | `312547781350` | Men foam 5% · 3×2.11oz |
| `rogaine-single-woman` | Rogaine | `312547780223` | Women foam 5% · 2×2.11oz |
| `amazon-basic-foam-man` | Amazon Basic Care | `195515027861` | Men foam 5% · 3×2.11oz |
| `kirkland-foam-man` | Kirkland Signature | `096619929221` | Men foam 5% · 6 cans |
| `kirkland-liquid-man` | Kirkland Signature | `096619929214` | Men liquid 5% · 6 bottles |
| `members-mark-foam-man` | Member's Mark | `193968415587` | Men foam 5% · 4 cans |
| `members-mark-liquid-man` | Member's Mark | `078742114163` | Men liquid 5% · 6 bottles |

## Store multipacks (2× / 4× retail boxes sold as one offer)
Do **not** invent a fake GTIN. In the feed:
- use the **base pack GTIN**
- set `multipack` = 2 or 4
- set `is_bundle` = yes when different components (Shapiro kit)

| Product id | Base GTIN | multipack |
|---|---|---|
| `rogaine-double-man` | `312547781350` | 2 |
| `rogaine-year-man` | `312547781350` | 4 |
| `rogaine-double-woman` | `312547780223` | 2 |
| `kirkland-liquid-double-man` | `096619929214` | 2 |
| `kirkland-foam-double-man` | `096619929221` | 2 |
| `members-mark-liquid-double-man` | `078742114163` | 2 |

## Needs barcode scan / label photo (do not guess)
Confirm on the physical box before pushing to Merchant:
- `rogaine-liquid-man`
- `rogaine-liquid-woman`
- `rogaine-shampoo-conditioner-man`
- `rogaine-shampoo-antidandruff-double`
- `kirkland-foam-woman`
- `shapiro-kit-man` → custom kit → `identifier_exists=no` + brand `Shapiro MD` + MPN `SHAPIRO-KIT-MAN`

Until scanned, those rows use `identifier_exists=no` + brand + MPN so they can still submit without GTIN errors.
