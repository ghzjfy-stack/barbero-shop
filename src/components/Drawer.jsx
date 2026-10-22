export default function Drawer({ open, onClose, label, children }) {
  return (
    <div
      className={`fixed inset-0 z-50 ${open ? "" : "pointer-events-none"}`}
      aria-hidden={!open}
    >
      <button
        type="button"
        className={`absolute inset-0 bg-black/75 backdrop-blur-[2px] transition-opacity duration-500 ${
          open ? "opacity-100" : "opacity-0"
        }`}
        aria-label="סגירה"
        tabIndex={open ? 0 : -1}
        onClick={onClose}
      />
      <aside
        role="dialog"
        aria-modal={open}
        aria-label={label}
        inert={open ? undefined : true}
        className={`absolute top-0 bottom-0 left-0 flex w-full max-w-[28rem] flex-col border-e border-white/10 bg-[#0c0c0e] shadow-[0_0_80px_rgba(0,0,0,0.45)] transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {children}
      </aside>
    </div>
  );
}
