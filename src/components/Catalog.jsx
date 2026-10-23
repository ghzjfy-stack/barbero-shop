import { useEffect, useRef, useState } from "react";
import { categories, discountPercent, fromPrice, products, resolveOffer } from "../data";
import { useStore } from "../store";
import { IconHeart, Stars } from "./Icons";
import Price from "./Price";
import ProductImage from "./ProductImage";

const sortOptions = [
  { value: "featured", label: "מיון: מומלצים" },
  { value: "priceAsc", label: "מחיר: מהנמוך" },
  { value: "priceDesc", label: "מחיר: מהגבוה" },
  { value: "rating", label: "דירוג" },
];

function SortSelect({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const current = sortOptions.find((option) => option.value === value) ?? sortOptions[0];

  useEffect(() => {
    if (!open) return undefined;
    const onPointer = (event) => {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    };
    const onKey = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const choose = (next) => {
    onChange(next);
    setOpen(false);
  };

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        className="sort-select field h-11 bg-black text-ivory"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls="catalog-sort-list"
        onClick={() => setOpen((isOpen) => !isOpen)}
        onKeyDown={(event) => {
          if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
          event.preventDefault();
          const index = sortOptions.findIndex((option) => option.value === value);
          const step = event.key === "ArrowDown" ? 1 : -1;
          const next = sortOptions[(index + step + sortOptions.length) % sortOptions.length];
          onChange(next.value);
          setOpen(true);
        }}
      >
        {current.label}
      </button>
      {open && (
        <ul
          id="catalog-sort-list"
          role="listbox"
          aria-label="מיון"
          className="absolute z-30 mt-2 w-full min-w-full border border-white/15 bg-black py-1 shadow-2xl"
        >
          {sortOptions.map((option) => {
            const selected = option.value === value;
            return (
              <li key={option.value} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={selected}
                  className={`block min-h-11 w-full px-4 py-3 text-start text-sm text-ivory transition-colors hover:bg-[#27272a] hover:text-gold-soft ${
                    selected ? "bg-[#18181b] text-gold-soft" : ""
                  }`}
                  onClick={() => choose(option.value)}
                >
                  {option.label}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

function ProductCard({ product }) {
  const { addToCart, openQuickView, toggleWish, isWished } = useStore();
  const [variantId, setVariantId] = useState(product.variants?.[0]?.id);
  const offer = resolveOffer(product, variantId);
  const wished = isWished(product.id);
  const soldOut = product.stock <= 0;
  const off = discountPercent(offer.price, offer.compareAt);
  const lowStock = product.stock > 0 && product.stock <= 3;
  const hoverImage = product.hoverImage || product.images?.[1];

  return (
    <article className="group flex h-full flex-col border border-white/10 bg-charcoal transition duration-300 hover:border-gold/40">
      <div className="relative aspect-square overflow-hidden bg-ink">
        <button
          type="button"
          className="absolute inset-0 p-3 sm:p-4"
          onClick={() => openQuickView(product.id)}
          aria-label={`מבט מהיר: ${product.name}`}
        >
          <ProductImage
            src={product.image}
            alt={product.name}
            className={
              hoverImage
                ? "h-full w-full object-contain object-center transition duration-500 group-hover:opacity-0"
                : "h-full w-full object-contain object-center transition duration-500"
            }
          />
          {hoverImage && (
            <ProductImage
              src={hoverImage}
              alt=""
              className="pointer-events-none absolute inset-3 sm:inset-4 h-[calc(100%-1.5rem)] w-[calc(100%-1.5rem)] sm:h-[calc(100%-2rem)] sm:w-[calc(100%-2rem)] object-contain object-center opacity-0 transition duration-500 group-hover:opacity-100"
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
          aria-label={wished ? "הסרה מהמועדפים שלי" : "הוספה למועדפים שלי"}
          onClick={() => toggleWish(product.id)}
        >
          <IconHeart filled={wished} />
        </button>
      </div>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col justify-between p-3 sm:p-4">
        <div>
          <p className="text-[11px] leading-4 text-gold">{product.category}</p>
          <h3 className="mt-1 text-sm leading-5 font-medium sm:text-base sm:leading-6">
            <button
              type="button"
              className="text-start hover:text-gold-soft"
              onClick={() => openQuickView(product.id)}
            >
              {product.name}
            </button>
          </h3>
          <p className="mt-1 text-start text-xs tracking-[0.14em] text-muted">{product.brand}</p>
          {typeof product.rating === "number" && (
            <div className="mt-3 h-5">
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
          <div className="mt-3 min-h-7">
            <Price price={offer.price} compareAt={offer.compareAt} />
          </div>
          {lowStock && <p className="mt-2 text-xs text-gold-soft">נותרו {product.stock} יחידות</p>}
        </div>

        <div className="mt-auto grid gap-1 pt-4">
          <button
            type="button"
            className="btn-gold h-11 text-sm"
            disabled={soldOut}
            onClick={() => addToCart(product.id, 1, offer.variant?.id)}
          >
            {soldOut ? "אזל מהמלאי" : "הוסף לעגלה"}
          </button>
          <button
            type="button"
            className="btn-text h-9 text-sm"
            onClick={() => openQuickView(product.id)}
          >
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
            <h2 className="font-display text-4xl leading-tight sm:text-5xl">
              קולקציית פרימיום לתספורת וגילוח
            </h2>
          </div>
          <div className="text-sm text-muted">
            <span className="sr-only">מיון</span>
            <SortSelect value={sort} onChange={setSort} />
          </div>
        </div>

        <div className="mb-8 flex flex-wrap gap-2">
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
          <div className="grid grid-cols-2 items-stretch gap-3 sm:gap-4 lg:grid-cols-4">
            {visible.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
