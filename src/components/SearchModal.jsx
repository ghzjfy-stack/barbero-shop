import { useEffect, useMemo, useRef, useState } from "react";
import { products, resolveOffer } from "../data";
import { useStore } from "../store";
import { IconClose, IconSearch } from "./Icons";
import Price from "./Price";
import ProductImage, { imageFrame } from "./ProductImage";
import ProductTitle from "./ProductTitle";

export default function SearchModal() {
  const { searchOpen, closeSearch, openQuickView } = useStore();
  const [query, setQuery] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    if (!searchOpen) return undefined;
    const timer = setTimeout(() => inputRef.current?.focus(), 40);
    return () => clearTimeout(timer);
  }, [searchOpen]);

  const results = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const source = needle
      ? products.filter((product) =>
          [product.name, product.kind, product.model, product.brand, product.category, product.sku]
            .join(" ")
            .toLowerCase()
            .includes(needle),
        )
      : products.slice(0, 4);
    return source;
  }, [query]);

  if (!searchOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center px-4 pt-24 sm:pt-28">
      <button type="button" className="absolute inset-0 bg-black/75 backdrop-blur-sm" aria-label="סגירת חיפוש" onClick={closeSearch} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="חיפוש בקולקציה"
        className="relative z-10 w-full max-w-2xl border border-line bg-[#0e0e10] shadow-2xl"
      >
        <div className="flex items-center gap-2 border-b border-white/10 px-4">
          <IconSearch className="h-5 w-5 text-gold" />
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="חיפוש מכונה, מותג או מק״ט"
            className="h-14 w-full bg-transparent text-base outline-none placeholder:text-muted"
            aria-label="חיפוש"
          />
          <button type="button" className="icon-btn" aria-label="סגירה" onClick={closeSearch}>
            <IconClose />
          </button>
        </div>
        <div className="max-h-[60svh] overflow-y-auto p-2">
          <p className="px-3 py-2 text-xs text-muted">{query.trim() ? "תוצאות" : "דגמים מובילים"}</p>
          {results.length === 0 ? (
            <p className="px-3 py-8 text-center text-sm text-muted">לא מצאנו דגם תואם. נסו שם מותג או קטגוריה.</p>
          ) : (
            <ul>
              {results.map((product) => {
                const offer = resolveOffer(product);
                return (
                  <li key={product.id}>
                    <button
                      type="button"
                      className="grid w-full grid-cols-[3.5rem_1fr_auto] items-center gap-3 px-3 py-2 text-start hover:bg-white/5"
                      onClick={() => openQuickView(product.id)}
                    >
                      <span className={`h-14 overflow-hidden ${imageFrame(product).box}`}>
                        <ProductImage
                          src={product.image}
                          alt=""
                          className={
                            imageFrame(product).studio
                              ? "h-full w-full object-contain p-1"
                              : "h-full w-full object-cover"
                          }
                        />
                      </span>
                      <span>
                        <span className="block text-start text-sm">
                          <ProductTitle product={product} />
                        </span>
                        <span className="mt-1 block text-xs text-muted">
                          {product.brand} · {product.category}
                        </span>
                      </span>
                      <Price price={offer.price} compareAt={offer.compareAt} />
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
