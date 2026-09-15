import { useState } from "react";

interface Props {
  src: string | null;
  name: string | null;
  color: string;
  size?: number;
}

/** Avatar redondo com fallback de iniciais sobre a cor do grupo (X remove imagens de contas suspensas). */
export function Avatar({ src, name, color, size = 40 }: Props) {
  const [failed, setFailed] = useState(false);
  const style = { width: size, height: size };
  if (!src || failed) {
    return (
      <div
        aria-hidden
        style={{ ...style, backgroundColor: color }}
        className="flex shrink-0 select-none items-center justify-center rounded-full text-[14px] font-bold text-white"
      >
        {initials(name)}
      </div>
    );
  }
  return (
    <img
      src={src}
      alt=""
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
      style={style}
      className="shrink-0 rounded-full bg-gray-100 object-cover"
    />
  );
}

function initials(name: string | null): string {
  const words = (name ?? "").trim().split(/\s+/).filter(Boolean).slice(0, 2);
  const out = words.map((w) => Array.from(w)[0]?.toUpperCase() ?? "").join("");
  return out || "?";
}
