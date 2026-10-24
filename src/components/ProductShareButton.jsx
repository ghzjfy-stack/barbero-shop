import { productWhatsAppShareHref } from "../share";
import { IconBeardBrush } from "./Icons";

export default function ProductShareButton({
  product,
  variantId,
  className = "btn-text h-9 text-sm",
  iconOnly = false,
}) {
  const href = productWhatsAppShareHref(product, variantId);

  if (iconOnly) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className={className}
        aria-label={`שיתוף ${product.name} בוואטסאפ`}
        title="שתף בוואטסאפ"
      >
        <IconBeardBrush className="h-5 w-5" />
      </a>
    );
  }

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={className}
      aria-label={`שיתוף ${product.name} בוואטסאפ`}
    >
      <IconBeardBrush className="h-4 w-4" />
      שתף בוואטסאפ
    </a>
  );
}
