import { useEffect, useRef, useState } from "react";
import { categories, discountPercent, fromPrice, products, resolveOffer } from "../data";
import { useStore } from "../store";
import { IconHeart, Stars } from "./Icons";
import Price from "./Price";
import ProductImage from "./ProductImage";
import ProductShareButton from "./ProductShareButton";
import ProductTitle from "./ProductTitle";


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

function ProductCardMedia({ product, soldOut, off, wished, variantId, onOpen, onToggleWish }) {
  const gallery = product.images?.length ? product.images : product.image ? [product.image] : [];
  const hoverImage = product.hoverImage || gallery[1];
  const scrollerRef = useRef(null);
  const swipeRef = useRef({ x: 0, moved: false });
  const [slide, setSlide] = useState(0);

  useEffect(() => {
    const node = scrollerRef.current;
    if (!node) return undefined;
    const onScroll = () => {
      const width = node.clientWidth || 1;
      setSlide(Math.round(node.scrollLeft / width));
    };
    node.addEventListener("scroll", onScroll, { passive: true });
    return () => node.removeEventListener("scroll", onScroll);
  }, []);

  const openUnlessSwiped = () => {
    if (swipeRef.current.moved) return;
    onOpen();
  };

  return (
    <div className="relative aspect-square overflow-hidden bg-ink">
      {/* Mobile / small: swipe between gallery images */}
      <div
        ref={scrollerRef}
        dir="ltr"
        className="flex h-full w-full snap-x snap-mandatory overflow-x-auto overscroll-x-contain md:hidden [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        onTouchStart={(event) => {
          swipeRef.current = { x: event.touches[0]?.clientX ?? 0, moved: false };
        }}
        onTouchMove={(event) => {
          const x = event.touches[0]?.clientX ?? 0;
          if (Math.abs(x - swipeRef.current.x) > 10) swipeRef.current.moved = true;
        }}
      >
        {gallery.map((src, index) => (
          <button
            key={`${src}-${index}`}
            type="button"
            className="h-full w-full shrink-0 snap-center p-3"
            aria-label={`${product.name} — תמונה ${index + 1} מתוך ${gallery.length}`}
            onClick={openUnlessSwiped}
          >
            <ProductImage src={src} alt="" className="h-full w-full object-contain object-center" />
          </button>
        ))}
      </div>

      {/* Desktop: keep existing hover swap */}
      <button
        type="button"
        className="absolute inset-0 hidden p-3 sm:p-4 md:block"
        onClick={onOpen}
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

      {gallery.length > 1 && (
        <div className="pointer-events-none absolute inset-x-0 bottom-2 flex justify-center gap-1.5 md:hidden">
          {gallery.map((src, index) => (
            <span
              key={`dot-${src}-${index}`}
              className={`h-1.5 w-1.5 rounded-full ${index === slide ? "bg-gold" : "bg-white/35"}`}
            />
          ))}
        </div>
      )}

      <div className="pointer-events-none absolute top-3 start-3 z-10 flex max-w-[calc(100%-3.25rem)] flex-col items-start gap-2">
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
      <div className="absolute top-2 end-2 z-10 flex flex-col gap-2">
        <button
          type="button"
          className={`grid h-11 w-11 place-items-center bg-ink/55 ${
            wished ? "text-gold" : "text-ivory"
          }`}
          aria-pressed={wished}
          aria-label={wished ? "הסרה מהמועדפים שלי" : "הוספה למועדפים שלי"}
          onClick={onToggleWish}
        >
          <IconHeart filled={wished} />
        </button>
        <ProductShareButton product={product} variantId={variantId} />
      </div>
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

  return (
    <article className="group flex h-full flex-col border border-white/10 bg-charcoal transition duration-300 hover:border-gold/40">
      <ProductCardMedia
        product={product}
        soldOut={soldOut}
        off={off}
        wished={wished}
        variantId={variantId}
        onOpen={() => openQuickView(product.id)}
        onToggleWish={() => toggleWish(product.id)}
      />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col p-3 sm:p-4">
        <div>
          <p className="line-clamp-2 min-h-8 text-[11px] leading-4 text-gold">{product.category}</p>
          <h3 className="mt-1 h-[4.5rem] overflow-hidden text-sm leading-6 font-medium sm:text-base">
            <button
              type="button"
              className="line-clamp-3 h-full w-full text-start leading-6 hover:text-gold-soft"
              onClick={() => openQuickView(product.id)}
            >
              <ProductTitle product={product} />
            </button>
          </h3>
          <p className="mt-1 h-4 truncate text-start text-xs leading-4 tracking-[0.14em] text-muted">{product.brand}</p>
          <div className="mt-3 h-5">
            {typeof product.rating === "number" && <Stars value={product.rating} reviews={product.reviews} />}
          </div>
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
          <div className="mt-3 flex min-h-12 items-start">
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
