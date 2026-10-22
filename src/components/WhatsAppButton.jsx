import { useStore } from "../store";
import { IconWhatsApp } from "./Icons";

const WHATSAPP_HREF =
  "https://wa.me/972543554888?text=שלום%20BARBERO,%20אשמח%20לקבל%20מידע%20ייעוץ%20לגבי%20המוצרים";

export default function WhatsAppButton() {
  const { cartOpen, wishOpen, searchOpen, menuOpen, quickView, info } = useStore();
  const covered = cartOpen || wishOpen || searchOpen || menuOpen || quickView || info;

  return (
    <a
      href={WHATSAPP_HREF}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="פנייה בוואטסאפ"
      aria-hidden={covered}
      tabIndex={covered ? -1 : 0}
      className={`fixed z-30 grid h-14 w-14 place-items-center rounded-full bg-[#25D366] text-white shadow-[0_12px_28px_rgba(0,0,0,0.35)] transition duration-300 hover:scale-105 hover:bg-[#1ebe5a] bottom-[max(1.25rem,env(safe-area-inset-bottom,0px))] left-[max(1.25rem,env(safe-area-inset-left,0px))] ${
        covered ? "pointer-events-none opacity-0" : ""
      }`}
    >
      <IconWhatsApp />
    </a>
  );
}
