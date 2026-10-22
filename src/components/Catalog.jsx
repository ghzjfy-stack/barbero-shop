import { useState } from "react";
import { categories, discountPercent, fromPrice, products, resolveOffer } from "../data";
import { useStore } from "../store";
import { IconHeart, Stars } from "./Icons";
import Price from "./Price";
import ProductImage, { imageFrame } from "./ProductImage";

function ProductCard({ product }) {
  const { addToCart, openQuickView, toggleWish, isWished } = useStore();
  const [variantId, setVariantId] = useState(product.variants?.[0]?.id);
  const offer = resolveOffer(product, variantId);
  const wished = isWished(product.id);
  const soldOut = product.stock <= 0;
  const off = discountPercent(offer.price, offer.compareAt);
  const lowStock = product.stock > 0 && product.stock <= 3;
  const frame = imageFrame(product);
  const gallery = product.images?.length ? product.images : [product.image];
  const hoverImage = gallery[1];
  const photoClass = frame.studio
    ? "h-full w-full object-contain p-5 transition duration-500"
    : "h-full w-full object-cover brightness-[.78] saturate-[.8] transition duration-500";

  return (
    <article className="group flex flex-col border border-white/10 bg-charcoal transition duration-300 hover:border-gold/40">
      <div className={`relative aspect-[3/4] overflow-hidden ${frame.box}`}>
        <button
          type="button"
          className="absolute inset-0"
          onClick={() => openQuickView(product.id)}
          aria-label={`מבט מהיר: ${product.name}`}
        >
          <ProductImage
            src={gallery[0]}
            alt={product.name}
            className={
              hoverImage
                ? `${photoClass} group-hover:opacity-0`
                : `${photoClass} ${frame.studio ? "group-hover:scale-[1.03]" : "group-hover:scale-[1.04] group-hover:brightness-90"}`
            }
          />
          {hoverImage && (
            <ProductImage
              src={hoverImage}
              alt=""
              className={`${photoClass} absolute inset-0 opacity-0 group-hover:opacity-100`}
            />
          )}
        </button>
        <div className="pointer-events-none absolute top-3 start-3 flex max-w-[calc(100%-3.25rem)] flex-col items-start gap-2">
          {soldOut ? (
            <span className="bg-ink/85 px-2.5 py-1 text-[11px] text-ivory">אזל</span>
          ) : product.badge ? (
            <span className="bg-ink/85 px-2.5 py-1 text-start text-[11px] leading-4 text-gold-soft">
              {product.badge}
            </span>
          ) : off > 0 ? (
            <span dir="ltr" className="bg-gold px-2.5 py-1 text-[11px] font-semibold text-[#16120b]">
              -{off}%
            </span>
          ) : null}
        </div>
        <button
          type="button"
          className={`absolute top-2 end-2 grid h-11 w-11 place-items-center bg-ink/55 ${
            wished ? "text-gold" : "text-ivory"
          }`}
          aria-pressed={wished}
          aria-label={wished ? "הסרה מרשימת המשאלות" : "שמירה לרשימת המשאלות"}
          onClick={() => toggleWish(product.id)}
        >
          <IconHeart filled={wished} />
        </button>
      </div>

      <div className="flex flex-1 flex-col p-4">
        <p className="text-[11px] text-gold">{product.category}</p>
        <h3 className="mt-1 text-base leading-6 font-medium">
          <button type="button" className="text-start hover:text-gold-soft" onClick={() => openQuickView(product.id)}>
            {product.name}
          </button>
        </h3>
        <p className="mt-1 text-start text-xs tracking-[0.14em] text-muted">{product.brand}</p>
        {typeof product.rating === "number" && (
          <div className="mt-3">
            <Stars value={product.rating} reviews={product.reviews} />
          </div>
        )}
        {product.variants && (
          <div className="mt-3 flex flex-wrap gap-1.5" role="group" aria-label="בחירת דגם">
            {product.variants.map((variant) => (
              <button
                key={variant.id}
                type="button"
                aria-pressed={variantId === variant.id}
                disabled={soldOut}
                onClick={() => setVariantId(variant.id)}
                className={`border px-2.5 py-1.5 text-xs ${
                  variantId === variant.id
                    ? "border-gold bg-gold text-[#16120b]"
                    : "border-white/15 text-ivory/80"
                }`}
              >
                {variant.label}
              </button>
            ))}
          </div>
        )}
        <div className="mt-3">
          <Price price={offer.price} compareAt={offer.compareAt} />
        </div>
        {lowStock && <p className="mt-2 text-xs text-gold-soft">נותרו {product.stock} יחידות</p>}

        <div className="mt-4 grid gap-1">
          <button
            type="button"
            className="btn-gold h-11 text-sm"
            disabled={soldOut}
            onClick={() => addToCart(product.id, 1, offer.variant?.id)}
          >
            {soldOut ? "אזל מהמלאי" : "הוסף לעגלה"}
          </button>
          <button type="button" className="btn-text h-9 text-sm" onClick={() => openQuickView(product.id)}>
            מבט מהיר
          </button>
        </div>
      </div>
    </article>
  );
}

export default function Catalog() {
  const { category, setCategory } = useStore();
  const [sort, setSort] = useState("featured");

  const visible = products
    .filter((product) => category === "הכל" || product.category === category)
    .slice()
    .sort((a, b) => {
      if (sort === "priceAsc") return fromPrice(a) - fromPrice(b);
      if (sort === "priceDesc") return fromPrice(b) - fromPrice(a);
      if (sort === "rating") return (b.rating ?? 0) - (a.rating ?? 0);
      return 0;
    });

  return (
    <section id="collection" className="bg-ink">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-5">
          <div>
            <p className="mb-3 text-xs text-gold">הקולקציה</p>
            <h2 className="font-display text-4xl leading-tight sm:text-5xl">קולקציית פרימיום לתספורת וגילוח</h2>
          </div>
          <label className="text-sm text-muted">
            <span className="sr-only">מיון</span>
            <select
              value={sort}
              onChange={(event) => setSort(event.target.value)}
              className="field sort-select h-11 bg-charcoal"
            >
              <option value="featured">מיון: מומלצים</option>
              <option value="priceAsc">מחיר: מהנמוך</option>
              <option value="priceDesc">מחיר: מהגבוה</option>
              <option value="rating">דירוג</option>
            </select>
          </label>
        </div>

        <div className="mb-8 flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {categories.map((item) => (
            <button
              key={item}
              type="button"
              className="chip"
              aria-pressed={category === item}
              onClick={() => setCategory(item)}
            >
              {item}
            </button>
          ))}
        </div>

        {visible.length === 0 ? (
          <p className="border border-dashed border-white/15 px-6 py-16 text-center text-muted">
            אין דגמים בקטגוריה הזו כרגע.
          </p>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
            {visible.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
