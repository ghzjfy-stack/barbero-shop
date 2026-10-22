function Svg({ children, className = "h-5 w-5" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {children}
    </svg>
  );
}

export function IconSearch({ className }) {
  return (
    <Svg className={className}>
      <circle cx="11" cy="11" r="6.25" />
      <path d="M16 16.5 20.5 21" />
    </Svg>
  );
}

export function IconHeart({ className, filled = false }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={className || "h-5 w-5"}
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.5"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 20s-7-4.4-7-9.1C5 8 6.8 6.2 9.1 6.2c1.3 0 2.4.6 2.9 1.6.5-1 1.6-1.6 2.9-1.6 2.3 0 4.1 1.8 4.1 4.7C19 15.6 12 20 12 20Z"
      />
    </svg>
  );
}

export function IconBag({ className }) {
  return (
    <Svg className={className}>
      <path d="M6.5 8.5h11l-.7 11.2a1 1 0 0 1-1 .8H8.2a1 1 0 0 1-1-.8L6.5 8.5Z" />
      <path d="M9 8.5V7a3 3 0 0 1 6 0v1.5" />
    </Svg>
  );
}

export function IconMenu({ className }) {
  return (
    <Svg className={className}>
      <path d="M4 7.5h16M4 12h16M4 16.5h12" />
    </Svg>
  );
}

export function IconClose({ className }) {
  return (
    <Svg className={className}>
      <path d="M6 6 18 18M18 6 6 18" />
    </Svg>
  );
}

export function IconPlus({ className }) {
  return (
    <Svg className={className}>
      <path d="M12 5.5v13M5.5 12h13" />
    </Svg>
  );
}

export function IconMinus({ className }) {
  return (
    <Svg className={className}>
      <path d="M5.5 12h13" />
    </Svg>
  );
}

export function IconTrash({ className }) {
  return (
    <Svg className={className}>
      <path d="M5 7.5h14" />
      <path d="M9.5 7.4V5.8h5V7.4" />
      <path d="M8 7.5 8.7 19h6.6l.7-11.5" />
    </Svg>
  );
}

export function IconChevron({ className }) {
  return (
    <Svg className={className}>
      <path d="M14.5 5.5 8 12l6.5 6.5" />
    </Svg>
  );
}

export function IconStar({ className }) {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true" className={className || "h-3.5 w-3.5"}>
      <path
        fill="currentColor"
        d="M10 1.7 12.35 6.9l5.7.5-4.35 3.7 1.35 5.5L10 14.1 4.95 16.6l1.35-5.5L1.95 7.4l5.7-.5L10 1.7Z"
      />
    </svg>
  );
}

export function IconTruck({ className }) {
  return (
    <Svg className={className}>
      <path d="M3 7.5h11v8H3z" />
      <path d="M14 10.5h4.2L20 13.5V15.5h-6" />
      <circle cx="7" cy="17.2" r="1.4" />
      <circle cx="16.5" cy="17.2" r="1.4" />
    </Svg>
  );
}

export function IconBolt({ className }) {
  return (
    <Svg className={className}>
      <path d="M13 3 5.5 13.5H11L10 21l8-11.5H13L13 3Z" />
    </Svg>
  );
}

export function IconGlobe({ className }) {
  return (
    <Svg className={className}>
      <circle cx="12" cy="12" r="8.25" />
      <path d="M3.75 12h16.5M12 3.75c2.2 2.3 3.3 5.1 3.3 8.25S14.2 17.95 12 20.25C9.8 17.95 8.7 15.15 8.7 12S9.8 6.05 12 3.75Z" />
    </Svg>
  );
}

export function IconShield({ className }) {
  return (
    <Svg className={className}>
      <path d="M12 3.5 19 6.2v5.4c0 4.2-2.8 6.9-7 8.9-4.2-2-7-4.7-7-8.9V6.2L12 3.5Z" />
      <path d="m8.8 12 2.1 2.1 4.3-4.4" />
    </Svg>
  );
}

export function Stars({ value, reviews }) {
  const rounded = Math.round(value);
  return (
    <div className="flex items-center gap-2" aria-label={`דירוג ${value} מתוך 5`}>
      <span className="text-xs text-muted tabular-nums">{value.toFixed(1)}</span>
      <span className="flex" dir="ltr">
        {Array.from({ length: 5 }, (_, index) => (
          <IconStar
            key={index}
            className={`h-3.5 w-3.5 ${index < rounded ? "text-gold" : "text-white/15"}`}
          />
        ))}
      </span>
      {typeof reviews === "number" && (
        <span className="text-xs text-muted tabular-nums">({reviews.toLocaleString("he-IL")})</span>
      )}
    </div>
  );
}

const trustIcons = {
  truck: IconTruck,
  bolt: IconBolt,
  globe: IconGlobe,
  shield: IconShield,
};

export function TrustIcon({ name, className = "h-6 w-6" }) {
  const Icon = trustIcons[name] || IconShield;
  return <Icon className={className} />;
}
