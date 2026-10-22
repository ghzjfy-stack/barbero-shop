import { findProduct, resolveOffer } from "../data";
import { useStore } from "../store";
import Drawer from "./Drawer";
import { IconClose } from "./Icons";
import Price from "./Price";
import ProductImage, { imageFrame } from "./ProductImage";

export default function WishlistDrawer() {
  const { wishOpen, closeWish, wishlist, toggleWish, addToCart, openQuickView } = useStore();
  const items = wishlist.map((id) => findProduct(id)).filter(Boolean);

  return (
    <Drawer open={wishOpen} onClose={closeWish} label="רשימת משאלות">
      <header className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div>
          <p className="text-[11px] text-gold">שמורים אצלכם</p>
          <h2 className="font-display text-3xl leading-none">משאלות</h2>
        </div>
        <button type="button" className="icon-btn" aria-label="סגירה" onClick={closeWish}>
          <IconClose />
        </button>
      </header>
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {items.length === 0 ? (
          <div className="grid min-h-full place-items-center py-16 text-center">
            <div>
              <p className="font-display text-4xl">עדיין ריק</p>
              <p className="mt-3 text-sm leading-7 text-muted">סמנו לב על דגם כדי לשמור אותו לכאן.</p>
              <a href="#collection" className="btn-gold mt-6 h-11 px-6 text-sm" onClick={closeWish}>
                לקולקציה
              </a>
            </div>
          </div>
        ) : (
          <ul className="space-y-4">
            {items.map((product) => {
              const offer = resolveOffer(product);
              const soldOut = product.stock <= 0;
              return (
                <li key={product.id} className="grid grid-cols-[4.5rem_1fr] gap-3 border-b border-white/10 pb-4">
                  <button type="button" className={`h-24 overflow-hidden ${imageFrame(product).box}`} onClick={() => openQuickView(product.id)}>
                    <ProductImage
                      src={product.image}
                      alt={product.name}
                      className={
                        imageFrame(product).studio ? "h-full w-full object-contain p-1.5" : "h-full w-full object-cover"
                      }
                    />
                  </button>
                  <div>
                    <button type="button" className="text-start text-sm leading-5" onClick={() => openQuickView(product.id)}>
                      {product.name}
                    </button>
                    <div className="mt-2">
                      <Price price={offer.price} compareAt={offer.compareAt} />
                    </div>
                    <div className="mt-3 flex gap-2">
                      <button
                        type="button"
                        className="btn-gold h-9 flex-1 text-xs"
                        disabled={soldOut}
                        onClick={() => addToCart(product.id, 1, offer.variant?.id, { open: true })}
                      >
                        {soldOut ? "אזל" : "הוסף לעגלה"}
                      </button>
                      <button type="button" className="btn-ghost h-9 px-3 text-xs" onClick={() => toggleWish(product.id)}>
                        הסרה
                      </button>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </Drawer>
  );
}
