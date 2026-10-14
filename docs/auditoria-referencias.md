# Auditoria das referências (TCC1 → proposta do TCC2)

> **Data:** 2026-10-05.
> **Escopo:** as 17 referências de `reports/final-report-msi-1.tex`, as 5 que só aparecem em
> `docs/proposta.md` e as 5 referências metodológicas novas, propostas para a revisão estrutural do
> TCC2.
> **Como foi feito:** um workflow com 9 agentes (3 referências cada) checou os metadados, o acesso
> ao texto integral e cada passagem citante. Os problemas graves foram depois conferidos à mão
> (Crossref, API do Zenodo e PDFs do arXiv/periódico). O resultado bruto, por passagem, está em
> `refs.json` no scratchpad da sessão e não foi versionado.
> **O relatório do TCC1 está congelado e não será editado.** As correções valem para a proposta e
> para o texto do TCC2.

## 1. Erros confirmados manualmente (corrigir antes de reusar)

| Ref | Problema | Conferido em | Correção |
|---|---|---|---|
| `b_silva2024` | **Autoria errada.** A primeira autora é Livia Alabarse dos Santos; L. J. da Silva é o 3º autor. O total também diverge: o agente contou 9.388.978 linhas (≈9,39 M), não 9,47 M. | API do Zenodo (`records/11206577`) | "L. Alabarse dos Santos, R. Mendes de Araujo, L. J. da Silva, A. G. D. Correa, O. B. Coelho, I. C. A. de Oliveira, *Tweet_Eleições_2022…* [Dataset], Zenodo, v1, 2024, doi:10.5281/zenodo.11206577". No texto: "Alabarse dos Santos et al. (2024)". O total de linhas pode ser recontado localmente. |
| `b_singh2020` | **A referência não existe.** Mistura o título de Pathak et al. com autores inventados e páginas que não correspondem a nenhum artigo. | Crossref | Para "sem benefício" (RCTs): Pathak S. K. et al., *DMSR* 14(6):1673–1680, 2020, doi:10.1016/j.dsx.2020.08.033. "Aumento de mortalidade" já é sustentado por Axfors et al. 2021. Singh A. K. et al. 2020 (14(4):589–596) é majoritariamente observacional e não serve para a frase sobre RCTs. |
| `b_becatti2019` | **Veículo, volume e autora errados**, e o termo **"comunidade discursiva" não aparece no artigo** (busca no PDF do arXiv 1901.07933: zero ocorrências de "discurs"). | Crossref + PDF | Metadados: C. Becatti et al., *Palgrave Communications* 5, art. 91, 2019, doi:10.1057/s41599-019-0300-3. O artigo continua útil, porque **projeta uma rede bipartida de retweets sobre a camada de usuários** (um precedente direto da nossa projeção). O termo "comunidade discursiva" precisa de outra fonte. O grupo Caldarelli/Saracco o usa em trabalhos posteriores, como Guarino, Mounim, Caldarelli e Saracco, *Leveraging content producer networks and user perception to detect online discursive communities* (Sci. Rep., 2026); falta conferir os metadados. |
| `b_recuero2021` | **O artigo não fala de vacinação.** Analisa apenas links pró e anti-hidroxicloroquina, numa rede de usuários × links, com **dois** clusters. Por isso não sustenta: (a) "resistência à vacinação" (relatório, l. 51); (b) "comunidades de um mesmo campo se distinguem pelo registro" (l. 74 e 270), já que não há análise de subcomunidades; (c) "esquerda e direita" (proposta, l. 42), porque os clusters são pró e anti-HCQ. | Resumo no periódico + texto integral (agente) | Manter só o que ela sustenta: assimetria da dieta informativa, cluster pró-HCQ mais ativo e hiperpartidário, mídia tradicional quase ausente nele. A vacinação precisa de outra fonte, ou sai do texto. A hipótese de "registro" passa a ser nossa, sem atribuição. |
| `proposta-pena2025` | **Não é rede de co-retweet.** As comunidades vêm de uma rede de **menções** com homofilia de sentimento, e o objeto é um **referendo**, não uma eleição. O título publicado também está incompleto. | Resumo no arXiv 2311.09196 | Citar como exemplo de detecção de polos e de difusão (cascatas de retweet) entre eles, não como co-retweet. Metadados: *R. Soc. Open Sci.* 12(1):240454, 2025, doi:10.1098/rsos.240454. |
| `b_conover2011` | **Possível troca entre os dois artigos.** As afirmações descritivas (rede dirigida, duas comunidades segregadas) são do ICWSM 2011 *Political Polarization on Twitter*. O PASSAT 2011 (*Predicting…*) sustenta a parte de **predição** (95% de acurácia pela estrutura de comunidades). | Agente (ICWSM lido na íntegra) | Citar os dois, cada um na afirmação que lhe cabe. |

## 2. Correções menores

- `b_rj2022` (Agência Brasil): a notícia sustenta a data, o mandado, as ofensas a Cármen Lúcia, as granadas, os ~60 tiros e os policiais feridos. **Não sustenta** "prisão domiciliar", "milícias digitais", "fuzil" (a notícia diz "armas de grosso calibre") nem "ex-deputado". Esses fatos precisam de uma segunda fonte jornalística.
- `b_interian2023`: os números (44,1% e 13,4%, >15 M tweets) conferem. "Mais **coesa**" é inferência nossa. Os autores falam em isolamento e em facilidade de "dominação" ou coordenação. "Converge… reforça a validade de ambos" é forte demais (períodos, grafo e medida diferentes); "é consistente com" é mais seguro.
- `b_rocha2024`: sustenta a topologia bipolar, mas **não usa a mesma base de dados** (é um dataset próprio de ~2 M tweets).
- `b_pariser2011`: o subtítulo citado é o da edição de 2012. O original (Penguin Press, 2011) é *What the Internet Is Hiding from You*.
- `b_sunstein2001`: *Echo Chambers* é um livreto complementar. A formulação teórica completa está em **Republic.com** (Princeton UP, 2001); vale citar este ou os dois.
- `b_kessler1963`: o conceito confere. A formulação matricial (A·Aᵀ) é posterior, então a frase não deve ser atribuída a Kessler.
- `b_watson2022`: "da ordem de 14 milhões, 185 países" confere com o resumo (14,4 M; 19,8 M com excesso de mortalidade). Existe uma errata ainda não lida.
- DOIs a acrescentar: Recuero 2021 (10.22409/contracampo.v40i1.45611), Conover PASSAT (10.1109/PASSAT/SocialCom.2011.34), Kessler (10.1002/asi.5090140103), Cicchini (10.1140/epjds/s13688-022-00360-8), Soares 2019 (10.1145/3328529.3328546).
- `b_traag2019`, `b_newman2003`, `b_axfors2021`, `b_cicchini2022`, Flamino 2023, Recuero/Soares/Gruzd 2020 e Soares/Recuero 2021: corretas (estas três últimas só estão na proposta). Ressalva: Recuero 2020 e Soares 2021 usam redes de interação (RT + menção + resposta), não só retweet.

## 3. Referências novas (metodologia do TCC2)

Good et al. 2010 (degenerescência), Fortunato e Barthélemy 2007 (limite de resolução), Traag, Van
Dooren e Nesterov 2011 (CPM) e Peixoto 2014 (SBM aninhado/MDL): existem e sustentam a afirmação
pretendida. Lancichinetti e Fortunato 2012: sustenta, mas o volume e o DOI (Sci. Rep. 2:336,
10.1038/srep00336) foram recuperados de memória pelo agente e precisam ser conferidos.

## 4. Documentos que o autor precisa obter (sem acesso ao texto integral)

| Ref | Por quê |
|---|---|
| Soares, Recuero e Zago 2019 (SMSociety) | Só o resumo foi acessado. Falta verificar se a assimetria é de **fechamento** (como usamos) ou de outra natureza. |
| Conover et al. 2011 (PASSAT, *Predicting…*) | Só o resumo. Confirmar a definição da rede e o número de 95%. |
| Kessler 1963 | Só o resumo. Confirmar a definição de acoplamento. |
| Pariser 2011 | Livro. Confirmar a definição de *filter bubble* e a edição usada. |
| Sunstein 2001 (*Echo Chambers* e/ou *Republic.com*) | Livro. Confirmar o mecanismo social atribuído. |
