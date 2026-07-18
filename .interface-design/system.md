# Sistema visual TB-IA

## Direção

- **Nome:** Sala de Situação Territorial.
- **Pessoa:** coordenação municipal de vigilância ou atenção primária preparando a rotina de revisão e pactuação com equipes.
- **Tarefa central:** localizar onde há um sinal, compreender por que foi gerado e decidir o que precisa de revisão humana.
- **Sensação:** institucional, calma, precisa e densa como uma ferramenta de trabalho diário; nunca decorativa ou diagnóstica.
- **Assinatura:** Dossiê de vigilância persistente, organizado como uma trilha de evidências entre território/sinal, justificativa e pontos de revisão.

## Mundo visual

- Mosaico territorial, investigação de campo, limiar epidemiológico, rede de unidades, fila de vigilância, evidência pública e trilha de auditoria.
- Petróleo institucional e azul SUS estruturam a navegação.
- Verde cartográfico identifica seleção e continuidade.
- Papel clínico e grafite sustentam leitura prolongada.
- Âmbar e carmim são exclusivamente semânticos: atenção e maior gravidade.

## Tokens

- Canvas: `#edf2f0`.
- Papel: `#ffffff`.
- Superfície suave: `#f5f8f7`.
- Superfície rebaixada: `#e7eeeb`.
- Tinta principal: `#15272b`.
- Tinta secundária: `#536568`.
- Petróleo: `#073c42`.
- Azul SUS: `#096b8c`.
- Verde cartográfico: `#13806f`.
- Âmbar: `#b56f16`.
- Carmim: `#b43a49`.
- Bordas: variações de petróleo com baixa opacidade; sem sombras dramáticas.

## Tipografia e densidade

- Família: IBM Plex Sans empacotada localmente.
- Base: 14 px; escala aproximada de 1,2 para interfaces densas.
- Títulos: 30/36, 20/26 e 16/22 px; peso e cor fazem mais hierarquia que tamanho.
- Números operacionais usam algarismos tabulares.
- Unidade espacial: 4 px; painéis usam 12–16 px e áreas maiores 20–24 px.

## Profundidade e formas

- Estratégia: bordas discretas e variação tonal; sombras apenas quando uma superfície precisa se elevar de fato.
- Raios: 6 px em controles, 10 px em painéis e 12 px em agrupamentos externos.
- Controles: 40 px no desktop e 44 px no mobile.
- Estados selecionados combinam fundo verde muito suave e uma trilha lateral de 3 px.

## Padrões

- **Shell:** 232 px no desktop; cabeçalho horizontal abaixo de 1180 px; menu recolhível abaixo de 760 px.
- **Cabeçalho de situação:** título compacto à esquerda e controles de escopo em superfície rebaixada à direita.
- **Faixa de situação:** quatro métricas em uma única superfície com divisórias, nunca quatro cartões flutuantes idênticos.
- **Bancada:** superfície principal ampla mais dossiê lateral de 360–380 px.
- **Dossiê:** contexto, pontuação/gravidade e trilha de evidências; sticky apenas no desktop.
- **Ranking territorial:** lista compacta de priorização; não usar tabela nem separar seleção e prévia. Cada linha inteira é um botão nativo, com foco visível, `aria-pressed`, nome sem quebra destrutiva e cor reservada ao estado.
- **Fila operacional:** permanece uma tabela semântica, adaptada para cartões apenas no mobile; não herda o padrão de lista do ranking territorial.
- **Mobile:** conteúdo decisório primeiro, controles em largura total, métricas 2x2 e nenhuma rolagem horizontal.

### Ranking territorial prioritário

- Busca, gravidade e situação dos dados permanecem visíveis tanto no estado recolhido quanto no expandido.
- Mostrar seis municípios filtrados por padrão e todos ao expandir; ocultar o controle quando houver seis resultados ou menos.
- Rótulos do controle: `Ver ranking completo` / `Mostrar 6 primeiros`; equivalentes em inglês: `View full ranking` / `Show first 6`.
- A linha apresenta, nesta ordem semântica: posição, município, quantidade de sinais, gravidade localizada e pontuação de prioridade.
- Desktop: altura mínima de 50 px, `padding` de 8 x 10 px, `gap` de 10 px e grade `28px minmax(0, 1fr) minmax(92px, 0.36fr) minmax(118px, auto) 64px`.
- Mobile até 760 px: altura mínima de 62 px, `padding` de 9 x 10 px, `gap` de 5 x 8 px e duas linhas — posição/nome/pontuação acima, posição/sinais/gravidade abaixo.
- Posição em círculo de 24 px; nome 13 px/600; sinais 11 px; pontuação 14 px/700 com algarismos tabulares; badge semântico de 9 px/700.
- Seleção: fundo verde cartográfico suave, borda verde discreta e trilha esquerda de 3 px. A seleção inicial abre automaticamente o município de maior prioridade e permanece sincronizada com mapa e dossiê.
- A lista e seus controles devem caber integralmente no viewport, sem rolagem horizontal em 390 px ou mais.

## Referências de implementação e verificação

- Componente: `frontend/src/components/PriorityRankingList.tsx`.
- Integração e sincronização: `frontend/src/pages/TerritorialPage.tsx`.
- Tokens, medidas e breakpoints: `frontend/src/styles/product.css`.
- Baseline desktop: 1440 px de largura, seis linhas recolhidas de 50 px, seleção visível e expansão completa sem alterar os filtros.
- Baseline mobile: 390 x 844 px, seis linhas de aproximadamente 62–64 px, conteúdo legível, seleção visível e largura do documento igual à largura do viewport.
- A verificação visual deve cobrir os dois estados, troca de município, atualização do dossiê, foco de teclado e ausência de overflow horizontal.

## Restrições do produto

- Não representar diagnóstico, prescrição ou decisão automatizada.
- Distinguir claramente dados públicos agregados de demonstrações sintéticas.
- Preservar semântica de tabelas, teclado, estados de foco e redução de movimento.
- Não alterar regras epidemiológicas, respostas das APIs ou limites de LGPD por razões visuais.
