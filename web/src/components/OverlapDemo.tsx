import type React from "react";
const FONT = { fontFamily: "Rethink Sans, sans-serif" };

const EDGES = [
  [168, 249, 163, 236], [168, 249, 134, 242], [134, 242, 163, 221], [156, 208, 163, 221], [221, 219, 204, 214],
  [204, 214, 186, 188], [186, 188, 167, 179], [127, 181, 154, 170], [127, 181, 114, 209], [167, 179, 191, 191],
  [152, 203, 156, 208], [382, 154, 374, 183], [352, 227, 339, 216], [339, 216, 360, 199], [406, 192, 432, 194],
  [374, 183, 360, 199], [345, 176, 370, 157], [370, 157, 385, 185], [411, 215, 406, 192], [339, 293, 322, 299],
  [295, 311, 297, 339], [295, 311, 322, 299], [297, 339, 283, 339], [337, 310, 346, 353], [221, 219, 339, 216],
  [370, 157, 337, 291],
];

const DOTS = [
  [[168, 249], [134, 242], [156, 208], [221, 219], [163, 236], [204, 214], [186, 188], [152, 203], [127, 181], [114, 209], [167, 179], [191, 191], [154, 170], [163, 221]],
  [[382, 154], [352, 227], [339, 216], [406, 192], [411, 215], [432, 194], [374, 183], [360, 199], [368, 229], [345, 176], [370, 157], [433, 161], [385, 185]],
  [[339, 293], [337, 310], [295, 311], [322, 299], [297, 339], [337, 291], [346, 353], [283, 339]],
];

const GROUPS = [
  { cx: 165, cy: 212, r: 78 },
  { cx: 386, cy: 192, r: 70 },
  { cx: 314, cy: 318, r: 52 },
];

function Pill({ x, y, label }: { x: number; y: number; label: string }) {
  return (
    <>
      <rect x={x} y={y} width="50" height="32" rx="16" fill="var(--bg)" />
      <text x={x + 25} y={y + 21}>
        {label}
      </text>
    </>
  );
}

/** Passos 1–2: as coleções de Ana e Bruno, separadas e depois sobrepostas. */
export function PairDemo({ overlap }: { overlap: boolean }) {
  const shift = { transform: `translateX(${overlap ? 155 : 0}px)` };
  const label = overlap
    ? "Os círculos de Ana e Bruno sobrepostos, com T1 e T2 na interseção"
    : "Os círculos de Ana e Bruno separados, cada um com seus tweets";
  return (
    <svg viewBox="0 0 560 400" role="img" aria-label={label} className="block h-auto w-full">
      <g className="slide" style={shift}>
        <circle cx="170" cy="200" r="105" fill="var(--line)" stroke="var(--faint)" strokeWidth="2.5" />
        <text x="110" y="92" style={FONT} fontWeight="800" fontSize="20" fill="var(--ink)">Ana</text>
      </g>
      <circle cx="390" cy="200" r="125" fill="var(--line-strong)" fillOpacity="0.6" stroke="var(--faint)" strokeWidth="2.5" />
      <text x="430" y="72" style={FONT} fontWeight="800" fontSize="20" fill="var(--ink)">Bruno</text>
      <g style={FONT} fontSize="15" fontWeight="700" textAnchor="middle" fill="var(--ink)">
        <g className="slide" style={shift}>
          <Pill x={145} y={152} label="T1" />
          <Pill x={145} y={214} label="T2" />
        </g>
        <Pill x={300} y={152} label="T1" />
        <Pill x={300} y={214} label="T2" />
        <Pill x={440} y={183} label="T3" />
      </g>
      {overlap && (
        <text className="grow" x="280" y="372" textAnchor="middle" style={FONT} fontSize="18" fontWeight="800" fill="var(--ink)">
          2 em comum ÷ 3 no total = ligação de 0,67
        </text>
      )}
    </svg>
  );
}

type Person = { name: string; x: number; y: number; labelDy: number };

/** Ana e Bruno chegam do passo 2; os demais entram depois, já como pontos. */
const PEOPLE: Person[] = [
  { name: "Ana", x: 160, y: 230, labelDy: 40 },
  { name: "Bruno", x: 260, y: 230, labelDy: 40 },
  { name: "Fê", x: 205, y: 115, labelDy: -26 },
  { name: "Edu", x: 365, y: 255, labelDy: 40 },
  { name: "Carla", x: 425, y: 120, labelDy: -26 },
  { name: "Davi", x: 470, y: 275, labelDy: 40 },
];

/**
 * Pares com sobreposição (índices em PEOPLE) e o peso ilustrativo da ligação. Ana–Bruno é o 0,67 do passo 2.
 * Dois trios bem ligados por dentro e uma ponte fina (Bruno–Edu) prenunciam as bolhas do passo 5.
 */
const LINKS: [number, number, number][] = [
  [0, 2, 0.5],
  [1, 2, 0.6],
  [4, 5, 0.75],
  [3, 4, 0.6],
  [3, 5, 0.5],
  [1, 3, 0.12],
];

/** Onde os círculos de Ana e Bruno estavam no fim do passo 2 (centro e raio). */
const BUBBLES = [
  { cx: 325, cy: 200, r: 105, fill: "var(--line)", alpha: 1 },
  { cx: 390, cy: 200, r: 125, fill: "var(--line-strong)", alpha: 0.6 },
];

const NODE_R = 15;
const MORPH_MS = 900;
const OTHERS_MS = 1500;
const width = (w: number) => 1.5 + w * 9;
const delay = (ms: number) => ({ animationDelay: `${ms}ms` });

/** Passo 3: as coleções de Ana e Bruno encolhem até virar pontos, a sobreposição vira linha e mais gente entra na rede. */
export function LinkDemo() {
  const [ana, bruno] = PEOPLE;
  return (
    <svg
      viewBox="0 0 560 400"
      role="img"
      aria-label="Os círculos de Ana e Bruno viram dois pontos ligados por uma linha de 0,67; outras quatro pessoas entram, formando dois trios ligados por uma linha fina"
      className="block h-auto w-full"
    >
      <g className="vanish" style={FONT} fontSize="15" fontWeight="700" textAnchor="middle" fill="var(--ink)">
        <Pill x={300} y={152} label="T1" />
        <Pill x={300} y={214} label="T2" />
        <Pill x={440} y={183} label="T3" />
        <text x="265" y="92" textAnchor="start" fontWeight="800" fontSize="20">Ana</text>
        <text x="430" y="72" textAnchor="start" fontWeight="800" fontSize="20">Bruno</text>
      </g>

      <g stroke="var(--rule)" strokeLinecap="round">
        {LINKS.map(([a, b, w], i) => (
          <line
            key={i}
            className="draw"
            style={delay(OTHERS_MS + 400 + i * 140)}
            pathLength={1}
            x1={PEOPLE[a].x}
            y1={PEOPLE[a].y}
            x2={PEOPLE[b].x}
            y2={PEOPLE[b].y}
            strokeWidth={width(w)}
          />
        ))}
        <line
          className="draw"
          style={delay(MORPH_MS - 200)}
          pathLength={1}
          x1={ana.x}
          y1={ana.y}
          x2={bruno.x}
          y2={bruno.y}
          strokeWidth={width(0.67)}
          stroke="var(--ink)"
        />
      </g>

      {[ana, bruno].map((p, i) => {
        const b = BUBBLES[i];
        const from = `translate(${b.cx - p.x}px, ${b.cy - p.y}px) scale(${b.r / NODE_R})`;
        return (
          <circle
            key={p.name}
            className="morph"
            style={{ "--from": from, "--from-fill": b.fill, "--from-alpha": b.alpha } as React.CSSProperties}
            cx={p.x}
            cy={p.y}
            r={NODE_R}
            fill="var(--faint)"
          />
        );
      })}
      {PEOPLE.slice(2).map((p, i) => (
        <circle key={p.name} className="grow" style={delay(OTHERS_MS + i * 150)} cx={p.x} cy={p.y} r={NODE_R} fill="var(--faint)" />
      ))}

      <g style={FONT} fontSize="17" fontWeight="800" textAnchor="middle" fill="var(--ink)">
        {PEOPLE.map((p, i) => (
          <text key={p.name} className="appear" style={delay(i < 2 ? MORPH_MS - 300 : OTHERS_MS + (i - 2) * 150)} x={p.x} y={p.y + p.labelDy}>
            {p.name}
          </text>
        ))}
        <text className="appear" style={delay(MORPH_MS + 200)} x={(ana.x + bruno.x) / 2} y={ana.y - 18} fontSize="16">
          0,67
        </text>
      </g>
    </svg>
  );
}

/** Passos 4–5: a rede de pessoas e as bolhas que o Leiden encontra nela. */
export function CrowdDemo({ grouped }: { grouped: boolean }) {
  const label = grouped ? "Pontos coloridos em três grupos" : "Uma rede de pontos ligados por linhas";
  return (
    <svg viewBox="0 0 560 400" role="img" aria-label={label} className="block h-auto w-full">
      {grouped &&
        GROUPS.map((g, i) => (
          <circle key={i} className="grow" cx={g.cx} cy={g.cy} r={g.r} fill={`var(--group-${i + 1})`} fillOpacity="0.16" />
        ))}
      <g className="zoom-out">
        <g stroke="var(--rule)" strokeWidth="1.2">
          {EDGES.map(([x1, y1, x2, y2], i) => (
            <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} />
          ))}
        </g>
        {DOTS.map((group, g) => (
          <g key={g} fill={grouped ? `var(--group-${g + 1})` : "var(--faint)"}>
            {group.map(([cx, cy], i) => (
              <circle key={i} className="appear" style={delay(200 + ((i * 3 + g * 7) % 20) * 30)} cx={cx} cy={cy} r="7" />
            ))}
          </g>
        ))}
      </g>
    </svg>
  );
}
