# Visão do Projeto — TCC

Este arquivo registra a visão fixa do projeto. O que está aqui **não deve mudar** sem discussão explícita. Outros arquivos podem evoluir conforme o desenvolvimento avança; este não.

## Identificação

- **Autor:** Vinicius
- **Orientadora:** Eliane
- **Curso:** Bacharelado em Sistemas de Informação
- **Entrega da proposta:** fim de maio de 2026
- **Defesa final:** novembro de 2026 (aprox. 24 semanas de desenvolvimento)

## Pergunta central

> Como apoiadores de esquerda e de direita no Twitter brasileiro construíram e amplificaram narrativas distintas sobre o mesmo evento — os ataques de 8 de janeiro de 2023 — e como essa divergência pode ser tornada visível e navegável para um leitor?

Esta pergunta orienta todas as decisões do projeto. Qualquer escolha técnica ou metodológica deve poder ser justificada como contribuição para respondê-la.

## Postura intelectual

O trabalho assume três posturas que não devem ser revertidas:

1. **Bolha de eco como ferramenta de leitura, não como objeto de prova.** O projeto não tenta provar que bolhas existem — a literatura já discute isso extensamente. O projeto usa o conceito de bolha como instrumento para tornar legível a divergência informacional entre comunidades políticas em torno de um evento específico.

2. **O grafo é meio, não fim.** A construção e análise do grafo de co-retweet são ferramentas para chegar ao produto final (a visualização). Métricas estruturais são reportadas, mas não são o ponto central da contribuição.

3. **TCC, não artigo científico.** O critério de sucesso não é originalidade absoluta nem rigor de paper de pesquisa. O critério é demonstrar competência técnica em aplicar conceitos computacionais a um problema do mundo real, com entregáveis concretos e bem documentados.

## Contribuição esperada

Três entregáveis concretos:

1. **Pipeline computacional reutilizável** em Python que recebe um arquivo do dataset Silva et al. (2024) e produz um grafo de co-retweet com comunidades detectadas e métricas estruturais.

2. **Análise comparativa de quatro eventos políticos** que compõem um arco narrativo de tensionamento progressivo até o 8 de janeiro:
   - Mobilização do 7 de setembro de 2022
   - Caso Roberto Jefferson (outubro de 2022)
   - Debate sobre democracia no dia do 2º turno (30 de outubro de 2022)
   - Ataques de 8 de janeiro de 2023

3. **Aplicação web interativa pública** em React que permita a um leitor não-técnico explorar os grafos, comparar lado a lado o conteúdo amplificado por cada comunidade, e visualizar a evolução temporal do 8 de janeiro.

## O que está fora do escopo

Para evitar escopo difuso:

- **Não se analisa WhatsApp ou Telegram**, mesmo sabendo que parte da organização do 8 de janeiro ocorreu nessas plataformas.
- **Não se faz análise de sentimento textual em larga escala.** O texto dos tweets só é recuperado para uma amostra reduzida (top-N por evento), e a análise de conteúdo é qualitativa.
- **Não se faz detecção de bots ou de desinformação** como objeto de estudo.
- **Não se reconstrói o grafo de retweet direto (A retuita B)** — o dataset não permite isso a custo razoável.
- **Não se compara o caso brasileiro com outros países.** O foco é o contexto nacional.

## Limitações assumidas desde o início

Estas limitações são reconhecidas e documentadas — não são problemas a serem resolvidos no escopo do TCC:

1. Co-retweet network mede similaridade de consumo informacional, não fluxo direto de influência.
2. O dataset Silva et al. cobre apenas tweets capturados por palavras-chave em eventos específicos; não representa o Twitter político brasileiro como um todo.
3. Retweet não é endosso absoluto — pode haver retweet antagônico (citação irônica, exposição ao ridículo).
4. Hidratação parcial: contas suspensas ou tweets removidos após janeiro de 2023 não são recuperáveis.
5. Twitter é apenas uma janela do ecossistema digital político brasileiro.

## Stack técnica (fixada)

- **Processamento de dados:** Python + pandas
- **Análise de grafos:** igraph
- **Detecção de comunidades:** algoritmo de Leiden
- **Cache de hidratação:** SQLite
- **Classificação assistida:** API de LLM
- **Frontend:** React + Sigma.js + Tailwind
- **Hospedagem:** Vercel ou equivalente gratuito

## Princípios de execução

- **Eficiência de custos de API.** Hidratação é cara e deve ser feita uma única vez por tweet/autor, com cache persistente. Orçamento total previsto: ~US$ 25-50 para todo o projeto.
- **Reaproveitamento entre eventos.** Sempre que um autor já tiver sido classificado em um evento, sua classificação é reutilizada nos demais.
- **Documentação à medida que se constrói.** Cada decisão metodológica importante é registrada em commit/markdown, não deixada para o fim.
- **LLM como assistente, não como oráculo.** Toda classificação ou sumarização feita por LLM é revisada manualmente e documentada como tal.