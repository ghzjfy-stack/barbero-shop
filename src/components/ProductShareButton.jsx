import { productWhatsAppShareHref } from "../share";
import { IconShare } from "./Icons";

const mediaClass =
  "grid h-11 w-11 place-items-center bg-ink/55 text-ivory transition hover:text-gold-soft";

export default function ProductShareButton({
  product,
  variantId,
  className = mediaClass,
}) {
  return (
    <a
      href={productWhatsAppShareHref(product, variantId)}
      target="_blank"
      rel="noopener noreferrer"
      className={className}
      aria-label={`שיתוף ${product.name} בוואטסאפ`}
      title="שתף בוואטסאפ"
      onClick={(event) => event.stopPropagation()}
    >
      <IconShare className="h-5 w-5" />
    </a>
  );
}
