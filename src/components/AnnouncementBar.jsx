import { announcements } from "../data";

export default function AnnouncementBar() {
  const loop = [0, 1];

  return (
    <div className="border-b border-gold/30 bg-ink text-[13px] text-gold-soft">
      <p className="sr-only">{announcements.join(". ")}</p>
      <div className="marquee h-9 overflow-hidden" dir="ltr">
        <div className="marquee-track h-full">
          {loop.map((copy) => (
            <ul key={copy} className="flex h-full shrink-0 items-center">
              {announcements.map((item) => (
                <li key={`${copy}-${item}`} className="flex items-center gap-8 px-8" dir="rtl">
                  <span className="text-gold" aria-hidden="true">
                    ◆
                  </span>
                  <span className="whitespace-nowrap font-medium">{item}</span>
                </li>
              ))}
            </ul>
          ))}
        </div>
      </div>
    </div>
  );
}
