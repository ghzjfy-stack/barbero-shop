import { useEffect, useRef, useState } from "react";
import {
  absoluteAssetUrl,
  discountPercent,
  findProduct,
  productUrl,
  resolveOffer,
  SITE_ORIGIN,
} from "../data";
import { navigate } from "../navigate";
import { useStore } from "../store";
import { IconChevron, IconHeart, IconMinus, IconPlus, Stars } from "./Icons";
import Price from "./Price";
import ProductImage, { imageFrame } from "./ProductImage";
import ProductTitle from "./ProductTitle";

function upsertMeta(attr, key, content) {
  if (!content) return;
  let node = document.head.querySelector(`meta[${attr}="${key}"]`);
  if (!node) {
    node = document.createElement("meta");
    node.setAttribute(attr, key);
    document.head.appendChild(node);
  }
  node.setAttribute("content", content);
}

function upsertLink(rel, href) {
  let node = document.head.querySelector(`link[rel="${rel}"]`);
  if (!node) {
    node = document.createElement("link");
    node.setAttribute("rel", rel);
    document.head.appendChild(node);
  }
  node.setAttribute("href", href);
}

function setProductSeo(product, offer) {
  const title = `${product.name} | BARBERO`;
  const description = product.blurb;
  const image = absoluteAssetUrl(product.image);
  const url = productUrl(product.id);

  document.title = title;
  upsertMeta("name", "description", description);
  upsertMeta("property", "og:type", "product");
  upsertMeta("property", "og:title", title);
  upsertMeta("property", "og:description", description);
  upsertMeta("property", "og:url", url);
  upsertMeta("property", "og:image", image);
  upsertMeta("property", "product:price:amount", String(offer.price));
  upsertMeta("property", "product:price:currency", "ILS");
  upsertLink("canonical", url);

  const schema = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    description: product.blurb,
    sku: product.sku,
    mpn: product.mpn || product.sku,
    gtin13: product.gtin?.padStart(13, "0"),
    brand: { "@type": "Brand", name: product.brand },
    image: (product.images?.length ? product.images : [product.image]).map(absoluteAssetUrl),
    offers: {
      "@type": "Offer",
      url,
      priceCurrency: "ILS",
      price: offer.price,
      availability:
        product.stock > 0 ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
      itemCondition: "https://schema.org/NewCondition",
      seller: { "@type": "Organization", name: "BARBERO", url: SITE_ORIGIN },
    },
  };

  let script = document.getElementById("product-jsonld");
  if (!script) {
    script = document.createElement("script");
    script.id = "product-jsonld";
    script.type = "application/ld+json";
    document.head.appendChild(script);
  }
  script.textContent = JSON.stringify(schema);
}

function clearProductSeo() {
  document.getElementById("product-jsonld")?.remove();
}

export default function ProductPage({ productId }) {
  const product = findProduct(productId);
  const { addToCart, toggleWish, isWished } = useStore();
  const [variantId, setVariantId] = useState(null);
  const [qty, setQty] = useState(1);
  const [photo, setPhoto] = useState(0);
  const touchX = useRef(null);

  useEffect(() => {
    setVariantId(product?.variants?.[0]?.id ?? null);
    setQty(1);
    setPhoto(0);
  }, [product?.id]);

  useEffect(() => {
    if (!product) {
      clearProductSeo();
      document.title = "מוצר לא נמצא | BARBERO";
      return undefined;
    }
    const offer = resolveOffer(product, variantId);
    setProductSeo(product, offer);
    return () => clearProductSeo();
  }, [product, variantId]);

  if (!product) {
    return (
      <section className="mx-auto max-w-3xl px-4 pb-20 pt-28 text-center sm:px-6">
        <h1 className="font-display text-3xl">המוצר לא נמצא</h1>
        <p className="mt-3 text-muted">ייתכן שהקישור ישן או שהפריט הוסר מהקטלוג.</p>
        <button type="button" className="btn-gold mt-8 h-11 px-6" onClick={() => navigate("/#collection")}>
          חזרה לקולקציה
        </button>
      </section>
    );
  }

  const offer = resolveOffer(product, variantId);
  const wished = isWished(product.id);
  const soldOut = product.stock <= 0;
  const off = discountPercent(offer.price, offer.compareAt);
  const maxQty = Math.max(product.stock, 1);
  const frame = imageFrame(product);
  const gallery = product.images?.length ? product.images : [product.image];
  const galleryLength = gallery.length;
  const activePhoto = gallery[photo] ?? gallery[0];
  const specs = [
    ["מותג", product.brand],
    ["קטגוריה", product.category],
    product.voltage ? ["מתח", product.voltage] : null,
    ["מקור", product.origin],
    ["מק״ט", product.sku],
    product.gtin ? ["ברקוד", product.gtin] : null,
  ].filter(Boolean);

  const stepPhoto = (delta) => {
    if (galleryLength < 2) return;
    setPhoto((current) => (current + delta + galleryLength) % galleryLength);
  };

  return (
    <section className="mx-auto max-w-6xl px-4 pb-20 pt-28 sm:px-6">
      <nav className="mb-6 text-sm text-muted">
        <button type="button" className="hover:text-ivory" onClick={() => navigate("/")}>
          ראשי
        </button>
        <span className="mx-2 text-line">/</span>
        <button type="button" className="hover:text-ivory" onClick={() => navigate("/#collection")}>
          קולקציה
        </button>
        <span className="mx-2 text-line">/</span>
        <span className="text-ivory">{product.model}</span>
      </nav>

      <div className="grid gap-8 border border-line bg-slate lg:grid-cols-2 lg:gap-0">
        <div className={`relative flex flex-col ${frame.box}`}>
          <div
            className="relative aspect-square w-full"
            onTouchStart={(event) => {
              touchX.current = event.changedTouches[0]?.clientX ?? null;
            }}
            onTouchEnd={(event) => {
              if (touchX.current == null || gallery.length < 2) return;
              const dx = (event.changedTouches[0]?.clientX ?? touchX.current) - touchX.current;
              if (Math.abs(dx) < 40) return;
              stepPhoto(dx < 0 ? 1 : -1);
            }}
          >
            <ProductImage
              src={activePhoto}
              alt={`${product.name}, תמונה ${photo + 1} מתוך ${gallery.length}`}
              className="h-full w-full object-contain"
            />
            {gallery.length > 1 && (
              <>
                <button
                  type="button"
                  className="absolute top-1/2 start-2 z-10 grid h-11 w-11 -translate-y-1/2 place-items-center bg-ink/80 text-ivory hover:text-gold-soft"
                  aria-label="התמונה הקודמת"
                  onClick={() => stepPhoto(-1)}
                >
                  <IconChevron className="h-5 w-5 rotate-180" />
                </button>
                <button
                  type="button"
                  className="absolute top-1/2 end-2 z-10 grid h-11 w-11 -translate-y-1/2 place-items-center bg-ink/80 text-ivory hover:text-gold-soft"
                  aria-label="התמונה הבאה"
                  onClick={() => stepPhoto(1)}
                >
                  <IconChevron className="h-5 w-5" />
                </button>
              </>
            )}
          </div>
          {gallery.length > 1 && (
            <div className="flex gap-2 overflow-x-auto p-3" role="group" aria-label="גלריית המוצר">
              {gallery.map((src, index) => (
                <button
                  key={src}
                  type="button"
                  aria-label={`תמונה ${index + 1} מתוך ${gallery.length}`}
                  aria-pressed={index === photo}
                  onClick={() => setPhoto(index)}
                  className={`h-16 w-16 shrink-0 overflow-hidden border ${
                    index === photo ? "border-gold" : "border-white/20"
                  }`}
                >
                  <img src={src} alt="" className="h-full w-full object-contain" />
                </button>
              ))}
            </div>
          )}
          {soldOut ? (
            <span className="absolute top-4 start-4 bg-ink/85 px-3 py-1 text-xs">אזל מהמלאי</span>
          ) : product.badge ? (
            <span className="absolute top-4 start-4 max-w-[70%] bg-ink/85 px-3 py-1 text-start text-xs leading-5 text-gold-soft">
              {product.badge}
            </span>
          ) : off > 0 ? (
            <span dir="ltr" className="absolute top-4 start-4 bg-gold px-3 py-1 text-xs font-semibold text-[#16120b]">
              -{off}%
            </span>
          ) : null}
        </div>

        <div className="flex flex-col p-5 sm:p-8">
          <p className="text-xs text-gold">{product.category}</p>
          <h1 className="mt-2 text-start font-display text-[1.7rem] leading-tight sm:text-4xl">
            <ProductTitle product={product} />
          </h1>
          <p className="mt-3 text-xs tracking-[0.16em] text-muted">{product.brand}</p>
          {typeof product.rating === "number" && (
            <div className="mt-4">
              <Stars value={product.rating} reviews={product.reviews} />
            </div>
          )}
          <div className="mt-5">
            <Price price={offer.price} compareAt={offer.compareAt} size="lg" />
          </div>
          <p className="mt-4 text-sm leading-7 text-ivory/75">{product.blurb}</p>
          {product.features?.length > 0 && (
            <ul className="mt-4 list-disc space-y-2 ps-5 text-sm leading-7 text-ivory/75">
              {product.features.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}

          <dl className="mt-6 grid grid-cols-1 gap-px bg-white/10 text-sm min-[480px]:grid-cols-2">
            {specs.map(([label, value]) => (
              <div key={label} className="bg-ink px-3 py-3">
                <dt className="text-xs text-muted">{label}</dt>
                <dd className="mt-1 break-words">{value}</dd>
              </div>
            ))}
          </dl>

          {product.variants && (
            <div className="mt-5" role="group" aria-label="בחירת דגם">
              <p className="mb-2 text-xs text-muted">דגם</p>
              <div className="flex flex-wrap gap-2">
                {product.variants.map((variant) => (
                  <button
                    key={variant.id}
                    type="button"
                    aria-pressed={variantId === variant.id}
                    disabled={soldOut}
                    onClick={() => setVariantId(variant.id)}
                    className={`border px-3 py-2 text-sm ${
                      variantId === variant.id
                        ? "border-gold bg-gold text-[#16120b]"
                        : "border-white/15"
                    }`}
                  >
                    {variant.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {product.stock > 0 && product.stock <= 3 && (
            <p className="mt-4 text-sm text-gold-soft">נותרו {product.stock} יחידות</p>
          )}

          <div className="mt-6 flex items-center gap-3">
            <div className="flex border border-white/15">
              <button
                type="button"
                className="grid h-12 w-12 place-items-center"
                aria-label="הפחתת כמות"
                onClick={() => setQty((value) => Math.max(1, value - 1))}
                disabled={soldOut}
              >
                <IconMinus className="h-4 w-4" />
              </button>
              <span className="grid h-12 w-10 place-items-center tabular-nums" aria-live="polite">
                {qty}
              </span>
              <button
                type="button"
                className="grid h-12 w-12 place-items-center"
                aria-label="הגדלת כמות"
                onClick={() => setQty((value) => Math.min(maxQty, value + 1))}
                disabled={soldOut || qty >= product.stock}
              >
                <IconPlus className="h-4 w-4" />
              </button>
            </div>
            <button
              type="button"
              className={`grid h-12 w-12 place-items-center border border-white/15 ${wished ? "text-gold" : ""}`}
              aria-pressed={wished}
              aria-label={wished ? "הסרה מהמועדפים שלי" : "הוספה למועדפים שלי"}
              onClick={() => toggleWish(product.id)}
            >
              <IconHeart filled={wished} />
            </button>
          </div>

          <button
            type="button"
            className="btn-gold mt-4 h-12 w-full"
            disabled={soldOut}
            onClick={() => addToCart(product.id, qty, offer.variant?.id, { open: true })}
          >
            {soldOut ? "אזל מהמלאי" : "הוסף לעגלה"}
          </button>
        </div>
      </div>
    </section>
  );
}
