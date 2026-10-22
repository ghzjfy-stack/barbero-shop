import { useStore } from "../store";

export default function Toast() {
  const { toast, dismissToast, openCart, openWish } = useStore();
  if (!toast) return null;

  const action = toast.action === "cart" ? openCart : toast.action === "wish" ? openWish : null;
  const label = toast.action === "cart" ? "לעגלה" : toast.action === "wish" ? "למשאלות" : null;

  return (
    <div className="fixed inset-x-0 bottom-4 z-[80] flex justify-center px-4" role="status" aria-live="polite">
      <div className="flex w-full max-w-lg items-center gap-4 border border-line bg-[#14120e]/95 px-4 py-3 shadow-2xl backdrop-blur">
        <p className="min-w-0 flex-1 text-sm leading-6">{toast.message}</p>
        <div className="flex shrink-0 items-center gap-1">
          {action && (
            <button type="button" className="btn-text h-9 px-2 text-sm" onClick={action}>
              {label}
            </button>
          )}
          <button type="button" className="btn-text h-9 px-2 text-sm text-muted" onClick={dismissToast}>
            סגירה
          </button>
        </div>
      </div>
    </div>
  );
}
