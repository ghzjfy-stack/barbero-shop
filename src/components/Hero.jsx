import { useState } from "react";
import { fromPrice, products, resolveOffer } from "../data";
import { useStore } from "../store";
import { IconChevron } from "./Icons";
import Price from "./Price";
import ProductImage from "./ProductImage";

const HERO_IMAGE =
  "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?auto=format&fit=crop&w=2000&q=80";
const HERO_PRODUCT = "/products/wahl-senior-cut.png";

export default function Hero() {
  const featured = products.find((product) => product.id === "wahl-senior") ?? products[0];
  const { addToCart, openQuickView } = useStore();
  const [imageOk, setImageOk] = useState(true);
  const offer = resolveOffer(featured);

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
      <div className="absolute inset-0 bg-[linear-gradient(to_top,rgba(9,9,9,0.9)_0%,rgba(9,9,9,0.72)_48%,rgba(9,9,9,0.5)_100%)] md:bg-[linear-gradient(to_left,rgba(9,9,9,0.94)_0%,rgba(9,9,9,0.88)_60%,rgba(9,9,9,0.32)_100%)]" />
      <div className="absolute inset-0 bg-gradient-to-t from-ink/80 via-transparent to-ink/45" />

      <div className="relative z-10 mx-auto grid min-h-[100svh] w-full max-w-7xl items-end gap-8 px-4 pt-[calc(8.5rem+env(safe-area-inset-top,0px))] pb-12 sm:px-6 md:grid-cols-12 md:gap-10 md:pb-16 lg:px-8">
        <div className="rise md:col-span-7">
          <p className="mb-4 text-[11px] tracking-[0.16em] text-gold sm:mb-5 sm:text-xs sm:tracking-[0.28em]" dir="ltr">
            BARBERO · DIRECT IMPORT
          </p>
          <h1 className="max-w-3xl font-display text-[2.05rem] leading-[1.2] font-bold text-ivory sm:text-4xl md:text-[2.6rem] lg:text-5xl xl:text-[4.4rem]">
            מכונות התספורת והגילוח המובילות בעולם
            <span className="mt-3 block text-[1.3rem] leading-snug font-medium text-gold-soft sm:text-2xl lg:text-3xl xl:text-[2.35rem]">
              – יבוא ישיר מארה״ב
            </span>
          </h1>
          <p className="mt-6 max-w-xl text-base leading-8 text-ivory/75 sm:text-lg">
            נבחרו למספרות ולשימוש ביתי. 100% מקורי מארה״ב, באיכות ללא פשרות, עם אחריות יבואן ושירות ישירות מולנו.
          </p>
          <div className="mt-8 flex flex-col gap-3 min-[420px]:flex-row min-[420px]:flex-wrap min-[420px]:items-center">
            <a href="#collection" className="btn-gold h-12 w-full px-7 text-[15px] min-[420px]:w-auto">
              <span>לצפייה בקולקציה</span>
              <IconChevron className="h-4 w-4" />
            </a>
            <a href="#trust" className="btn-ghost h-12 w-full px-6 text-[15px] min-[420px]:w-auto">
              למה BARBERO
            </a>
          </div>
        </div>

        <aside className="rise border border-line bg-ink/80 p-4 backdrop-blur-md md:col-span-5">
          <p className="inline-block border border-gold/50 bg-gradient-to-l from-gold/20 via-gold/10 to-transparent px-3 py-1.5 text-[11px] font-medium tracking-[0.18em] text-gold shadow-[0_0_24px_rgba(198,161,91,0.25)]">
            הדגם הנמכר ביותר
          </p>
          <button type="button" className="mt-3 block w-full text-start" onClick={() => openQuickView(featured.id)}>
            <div className="relative mx-auto h-72 w-full overflow-hidden sm:h-80 md:aspect-[3/4] md:h-auto md:max-h-[min(34rem,calc(100svh-26rem))]">
              <div
                aria-hidden="true"
                className="absolute inset-0 bg-[radial-gradient(ellipse_78%_64%_at_50%_42%,#d7b56a_0%,#a07a42_24%,#5c4328_52%,#2a2118_78%,#16120e_100%)]"
              />
              <div
                aria-hidden="true"
                className="absolute inset-x-[10%] top-[8%] h-[52%] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(255,246,220,0.9),rgba(228,196,120,0.35)_40%,transparent_72%)] blur-2xl"
              />
              <div
                aria-hidden="true"
                className="absolute inset-x-[18%] bottom-[8%] h-16 rounded-full bg-[rgba(255,214,140,0.55)] blur-2xl"
              />
              <ProductImage
                src={HERO_PRODUCT}
                alt={featured.name}
                className="absolute inset-0 h-full w-full object-contain object-center p-5 [filter:brightness(1.08)_contrast(1.06)_drop-shadow(0_22px_18px_rgba(0,0,0,0.5))_drop-shadow(0_0_26px_rgba(236,214,164,0.34))] sm:p-7"
              />
            </div>
            <div className="mt-4">
              <p className="text-xs tracking-[0.14em] text-muted">{featured.brand}</p>
              <h2 className="mt-2 font-display text-xl leading-tight sm:text-2xl lg:text-3xl">{featured.name}</h2>
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
