# CLAUDE.md
# Contexto do Projeto — TCC

Esta pasta contém o contexto consolidado do projeto, destinado a ser usado como base para qualquer agente (humano ou de IA) que vá trabalhar no desenvolvimento.

## Como usar

Os três arquivos têm propósitos distintos. Leia na ordem se você está chegando agora:

1. **`docs/visao-projeto.md`** — *O que não muda.*
   Pergunta central, postura intelectual, entregáveis, escopo e stack. Esse arquivo é a referência mais alta. Se algo aqui mudar, todo o resto provavelmente precisa ser revisitado.

2. **`docs/especificacao-tecnica.md`** — *Como implementar.*
   Especificação da pipeline, do dataset, da hidratação, da rotulagem, da análise narrativa e da visualização. Parâmetros são deliberadamente deixados como "valor inicial a ajustar" onde dependem de validação empírica.

3. **`docs/decisoes-metodologicas.md`** — *Por que decidimos cada coisa.*
   Registro de cada decisão importante, com alternativas rejeitadas. Consultar antes de propor mudanças metodológicas.

## Postura analítica (vale para humanos e agentes)

Trabalhamos como cientistas de dados: **descrever, não prescrever**, e enviesar ao mínimo. A pergunta é o que a estrutura dos dados revela — não confirmar uma tese. Em concreto:

- **Não force estrutura.** Não assuma que os clusters são "esquerda × direita", que devem ser exatamente N, nem que comunidades pequenas são ruído descartável. O que o algoritmo encontra significa algo até prova em contrário — **caracterize antes de descartar**.
- **Separe correção de escolha analítica.** Corrigir um cálculo errado (ex.: uma matriz que deveria ser simétrica num grafo não-direcionado) é obrigatório. Já decidir "remover/agregar X para o resultado ficar limpo" é uma escolha que embute viés — evite, ou explicite o trade-off em vez de apresentá-la como recomendação/verdade.
- **Interprete pela ótica certa.** O objetivo é mapear o *comportamento* dos clusters e lê-lo sob computação social e ciência política — não rotular nem ranquear.
- **Nos docs de análise/sensibilidade** (`docs/analises-sensibilidade.md`, `docs/relatorio-diagnostico-*.md`): registre **observações brutas** (números, tabelas, como foram medidas) e, separadamente, uma **interpretação como apontamento** — datada e amarrada ao contexto daquele momento do projeto, **não como verdade absoluta**. Prefira "o que se observa" + "o que isso sugere, por ora" a recomendações prescritivas.

## Para agentes de codificação

Se você é um agente de IA encarregado de implementar partes do pipeline:

- Antes de fazer qualquer escolha não trivial, consulte `docs/decisoes-metodologicas.md` para ver se a questão já foi decidida.
- Se você precisar tomar uma decisão metodológica nova, registre-a no `docs/decisoes-metodologicas.md` no mesmo formato dos demais itens.
- Não invente parâmetros novos sem necessidade. Os parâmetros propositalmente em aberto (N de filtragem de usuários, X% de filtragem de tweets virais, τ do backbone) devem ser calibrados pela validação preliminar antes de aplicar a pipeline aos quatro eventos.
