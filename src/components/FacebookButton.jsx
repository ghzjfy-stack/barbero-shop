import { FACEBOOK_PAGE_URL } from "../data";
import { useStore } from "../store";
import { IconFacebook } from "./Icons";

export default function FacebookButton() {
  const { cartOpen, wishOpen, searchOpen, menuOpen, quickView, info } = useStore();
  const covered = cartOpen || wishOpen || searchOpen || menuOpen || quickView || info;

  return (
    <a
      href={FACEBOOK_PAGE_URL}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="עמוד הפייסבוק של BARBERO"
      aria-hidden={covered}
      tabIndex={covered ? -1 : 0}
      className={`fixed z-30 grid h-14 w-14 place-items-center rounded-full bg-[#1877F2] text-white shadow-[0_12px_28px_rgba(0,0,0,0.35)] transition duration-300 hover:scale-105 hover:bg-[#166fe5] bottom-[max(1.25rem,env(safe-area-inset-bottom,0px))] right-[max(1.25rem,env(safe-area-inset-right,0px))] ${
        covered ? "pointer-events-none opacity-0" : ""
      }`}
    >
      <IconFacebook className="h-6 w-6" />
    </a>
  );
}
