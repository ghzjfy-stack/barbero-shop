import { useState } from "react";

export function imageFrame(product) {
  if (product?.frame === "studio") {
    return { studio: true, box: "bg-[#f6f3ec]" };
  }
  return { studio: false, box: "bg-[#1a1814]" };
}

export default function ProductImage({ src, alt, className = "" }) {
  const [failed, setFailed] = useState(false);

  if (failed || !src) {
    return (
      <div
        className={`grid place-items-center bg-[radial-gradient(circle_at_30%_18%,rgba(198,161,91,0.35),transparent_34%),linear-gradient(165deg,#2c281f,#0c0c0e)] ${className}`}
      >
        <div className="flex flex-col items-center gap-3 text-gold-soft/90">
          <span className="grid h-16 w-16 place-items-center border border-gold/50 font-display text-3xl">
            B
          </span>
          <span className="text-[10px] tracking-[0.32em]">BARBERO</span>
        </div>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      onError={() => setFailed(true)}
    />
  );
}
