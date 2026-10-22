import { useStore } from "../store";
import { IconClose } from "./Icons";

export default function Toast() {
  const { toast, dismissToast, openCart, openWish } = useStore();
  if (!toast) return null;

  const action = toast.action === "cart" ? openCart : toast.action === "wish" ? openWish : null;
  const label = toast.action === "cart" ? "לעגלה" : toast.action === "wish" ? "לצפייה במועדפים" : null;

  return (
    <div className="fixed inset-x-0 bottom-4 z-[80] flex justify-center px-4" role="status" aria-live="polite">
      <div className="flex w-full max-w-lg flex-wrap items-center gap-3 border border-line bg-[#14120e]/95 px-4 py-3 shadow-2xl backdrop-blur">
        <p className="min-w-0 flex-1 text-sm leading-6">{toast.message}</p>
        <div className="flex shrink-0 items-center gap-2">
          {action && (
            <button
              type="button"
              className="btn-ghost h-9 px-3 text-sm whitespace-nowrap"
              onClick={() => {
                dismissToast();
                action();
              }}
            >
              {label}
            </button>
          )}
          <button
            type="button"
            className="grid h-9 w-9 shrink-0 place-items-center text-ivory/70 hover:text-ivory"
            aria-label="סגירה"
            onClick={dismissToast}
          >
            <IconClose className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
