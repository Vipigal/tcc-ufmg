import { HelpCircle } from "lucide-react";

/** "Saiba mais" (E4: explicação acessível do método). Linguagem para quem não vem da computação. */
export function MethodExplainer({ open = false }: { open?: boolean }) {
  return (
    <details open={open} className="rounded-xl border border-line bg-surface px-4 py-3 text-[13.5px] leading-6">
      <summary className="flex cursor-pointer items-center gap-1.5 font-semibold">
        <HelpCircle size={15} /> Como ler esta tela
      </summary>
      <div className="mt-2 space-y-2 text-ink/90">
        <p>
          <b>Cada ponto do mapa é um usuário</b> que retuitou durante o evento. Usuários ficam perto quando retuitaram as
          mesmas coisas. Os <b>grupos</b> foram encontrados por um algoritmo (Leiden) a partir só desses retweets: ninguém
          disse a ele quem é de qual lado.
        </p>
        <p>
          O <b>trecho entre aspas</b> é um recorte literal de uma síntese escrita por um modelo de linguagem (Claude) a
          partir dos tweets mais retuitados do grupo. O recorte foi escolhido pelos pesquisadores; o texto é do modelo. A
          síntese completa, com links para os tweets que sustentam cada afirmação, está em "ler o grupo".
        </p>
        <p>
          A <b>tag colorida</b> (<span className="font-semibold text-axis-left">esquerda</span>,{" "}
          <span className="font-semibold text-axis-right">direita</span>,{" "}
          <span className="font-semibold text-axis-other">outro</span>) resume a inclinação que o modelo descreveu, numa
          das três categorias, escolhida pelos pesquisadores. É um palpite sobre o <i>conteúdo amplificado</i>, não sobre
          as pessoas — e esquerda/direita descreve mal alguns grupos.
        </p>
        <p>
          A <b>barra</b> mostra quanto do que o grupo retuíta também circula em outros grupos. Perto de zero: o grupo vive
          num ambiente próprio. Alta: divide boa parte do conteúdo com um grupo "irmão". É assimétrica — um grupo pequeno
          tende a compartilhar mais com um grande do que o contrário.
        </p>
        <p className="text-muted">
          Limites: só os tweets mais retuitados de cada grupo foram recuperados, e parte deles já tinha sido apagada ou
          vinha de contas suspensas.
        </p>
      </div>
    </details>
  );
}
