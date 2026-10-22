import { useState } from "react";
import { fromPrice, products, resolveOffer } from "../data";
import { useStore } from "../store";
import { IconChevron } from "./Icons";
import Price from "./Price";
import ProductImage, { imageFrame } from "./ProductImage";

const HERO_IMAGE =
  "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?auto=format&fit=crop&w=2000&q=80";

export default function Hero() {
  const featured = products.find((product) => product.id === "wahl-senior") ?? products[0];
  const { addToCart, openQuickView } = useStore();
  const [imageOk, setImageOk] = useState(true);
  const offer = resolveOffer(featured);
  const frame = imageFrame(featured);

  return (
    <section id="top" className="relative min-h-[100svh] overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_15%_80%,rgba(198,161,91,0.2),transparent_42%),linear-gradient(160deg,#1a1814,#090909)]" />
      {imageOk && (
        <img
          src={HERO_IMAGE}
          alt=""
          fetchPriority="high"
          className="absolute inset-0 h-full w-full object-cover object-[center_30%] brightness-[.62] saturate-[.75]"
          onError={() => setImageOk(false)}
        />
      )}
      <div className="absolute inset-0 bg-[linear-gradient(to_left,rgba(9,9,9,0.94)_0%,rgba(9,9,9,0.82)_46%,rgba(9,9,9,0.28)_100%)]" />
      <div className="absolute inset-0 bg-gradient-to-t from-ink via-transparent to-ink/50" />

      <div className="relative z-10 mx-auto grid min-h-[100svh] w-full max-w-7xl items-end gap-10 px-4 pt-36 pb-16 sm:px-6 lg:grid-cols-12 lg:px-8">
        <div className="rise lg:col-span-7">
          <p className="mb-5 text-xs tracking-[0.28em] text-gold" dir="ltr">
            BARBERO · DIRECT IMPORT
          </p>
          <h1 className="max-w-3xl font-display text-[2.35rem] leading-[1.18] font-bold text-ivory sm:text-5xl lg:text-[4.4rem]">
            מכונות התספורת והגילוח המובילות בעולם
            <span className="mt-3 block text-[1.45rem] leading-snug font-medium text-gold-soft sm:text-3xl lg:text-[2.35rem]">
              – יבוא ישיר מארה״ב
            </span>
          </h1>
          <p className="mt-6 max-w-xl text-base leading-8 text-ivory/75 sm:text-lg">
            נבחרו למספרות ולשימוש ביתי. 100% מקורי מארה״ב, באיכות ללא פשרות, עם אחריות מלאה ושירות לקוחות בעברית.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <a href="#collection" className="btn-gold h-12 px-7 text-[15px]">
              <span>לצפייה בקולקציה</span>
              <IconChevron className="h-4 w-4" />
            </a>
            <a href="#trust" className="btn-ghost h-12 px-6 text-[15px]">
              למה BARBERO
            </a>
          </div>
        </div>

        <aside className="rise hidden border border-line bg-ink/80 p-4 backdrop-blur-md lg:col-span-5 lg:block">
          <p className="text-xs text-gold">הדגם שפותח את הבית</p>
          <button type="button" className="mt-3 block w-full text-start" onClick={() => openQuickView(featured.id)}>
            <div className={`relative aspect-[16/10] overflow-hidden ${frame.box}`}>
              <ProductImage
                src={featured.image}
                alt={featured.name}
                className={
                  frame.studio
                    ? "h-full w-full object-contain p-3"
                    : "h-full w-full object-cover brightness-90"
                }
              />
            </div>
            <div className="mt-4">
              <p className="text-xs tracking-[0.14em] text-muted">{featured.brand}</p>
              <h2 className="mt-2 font-display text-2xl leading-tight sm:text-3xl">{featured.name}</h2>
              <div className="mt-3">
                <Price price={fromPrice(featured)} compareAt={offer.compareAt} from={Boolean(featured.variants)} />
              </div>
            </div>
          </button>
          <div className="mt-4 grid grid-cols-2 gap-2">
            <button
              type="button"
              className="btn-gold h-11 text-sm"
              onClick={() => addToCart(featured.id, 1, offer.variant?.id)}
            >
              הוסף לעגלה
            </button>
            <button type="button" className="btn-ghost h-11 text-sm" onClick={() => openQuickView(featured.id)}>
              מבט מהיר
            </button>
          </div>
        </aside>
      </div>
    </section>
  );
}
