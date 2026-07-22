# Próximos passos

Última revisão: 21 de julho de 2026.

Este documento é o backlog canônico e priorizado do TB-IA. Ele transforma as
entregas ainda abertas do escopo do Biochallenge e da especificação técnica em
uma sequência de trabalho verificável. As definições detalhadas de indicadores,
contratos e arquitetura continuam em `especificacao_tecnica_do_sistema.md`.

O documento de Solução Técnica do Biochallenge não orienta este backlog enquanto
permanecer adiado. Alterações de prioridade devem ser registradas aqui, com a
justificativa correspondente, no mesmo commit que iniciar ou concluir uma
entrega.

## Estados

- **Próxima**: primeira entrega de produto a ser planejada e implementada.
- **Em andamento**: planejamento ou implementação ativa, com uma entrega
  verificável definida.
- **Em validação**: implementação e gates técnicos concluídos, mas ainda depende
  de revisão de domínio, governança ou fluxo com usuários para atender ao
  critério de saída.
- **Em espera**: o trabalho local conhecido está documentado, mas a capacidade
  depende de fonte, reconciliação ou decisão externa antes de ser retomada.
- **Planejada**: possui ordem definida, mas depende das entregas anteriores.
- **Condicional**: depende de fonte autorizada, qualidade mínima ou decisão de
  governança.
- **Pesquisa posterior**: exige evidência e validação antes de se tornar uma
  funcionalidade comprometida.
- **Concluída**: critérios de saída atendidos e verificados por testes e
  documentação.

Somente uma capacidade deve ficar em implementação por vez. Descobertas que
alterem escopo, dados ou segurança devem atualizar este documento antes de gerar
novas funcionalidades.

## Base atual

O produto já possui ingestão de dados públicos, armazenamento canônico,
indicadores municipais, cenários transparentes, ranking territorial,
recomendações auditáveis, alertas operacionais sintéticos, APIs e frontend de
produto. Os refinamentos visuais atuais são suficientes para esta etapa.

As principais lacunas funcionais são indicadores existentes sem cenários de
priorização, ausência de análise temporal, indicadores condicionais ainda não
validados e capacidades que dependem de fontes municipais autorizadas. O mapa e
o ranking atuais são análises territoriais por percentis, não um modelo de
hotspots ou de previsão.

## Regras de entrada no ranking

Uma nova regra somente pode alterar o ranking quando:

1. Numerador, denominador, universo, período e fonte estiverem documentados.
1. A transformação tiver um caso de aceitação reproduzido contra fonte oficial.
1. Completude, supressão e indisponibilidade tiverem comportamento explícito.
1. Limiar, severidade, peso e recomendação tiverem revisão de domínio.
1. Testes cobrirem cálculo, cenário, persistência e resposta da API afetada.
1. A interface continuar distinguindo dado disponível, ausente e suprimido.

Regras marcadas como `pending_domain_review` podem participar exclusivamente da
demonstração local para produzir evidência de validação, desde que permaneçam
visivelmente provisórias. Isso não equivale a aprovação para uso em produção;
o projeto ainda não possui uma implantação de produção selecionada.

Indicadores correlacionados não devem acumular peso indefinidamente. Cada nova
regra deve declarar se representa uma dimensão independente, um detalhamento ou
um componente de cenário composto.

## Ordem das capacidades

| Ordem | ID | Capacidade | Estado |
| --- | --- | --- | --- |
| 1 | CAP-01 | Priorização por testagem de HIV, TRM-TB e cultura | **Em validação** |
| 2 | CAP-02 | Tendências históricas e incidência crescente | **Em validação (método)** |
| 3 | CAP-03 | Investigação de contatos com dados públicos | **Em espera (reconciliação externa e domínio)** |
| 4 | CAP-04 | Vigilância de resistência em camadas | **Em andamento** |
| 5 | CAP-05 | Monitoramento de tratamento preventivo | **Condicional** |
| 6 | CAP-06 | Análise espacial de hotspots | **Pesquisa posterior** |

### CAP-01: testagem de HIV, TRM-TB e cultura

**Objetivo:** transformar os indicadores públicos já calculados em sinais de
priorização transparentes, sem contar a mesma deficiência diagnóstica várias
vezes no escore.

**Abordagem implementada:** três cenários comparativos separados usam p25 e
severidade moderada. HIV compartilha a dimensão de integração TB-HIV, TRM-TB
compartilha acesso diagnóstico e cultura compartilha vigilância de resistência,
limitando a contribuição conjunta de sinais correlacionados. A avaliação exige
pelo menos 10 valores disponíveis e cobertura de 5% dos municípios canônicos do
escopo. Valores ausentes ou suprimidos nunca são classificados como baixo
desempenho.

**Estado atual:** todo o trabalho conhecido que não exige validação de domínio
está concluído: transformação, amostra de aceitação, persistência, localização,
regras provisórias, agrupamento de dimensões, testes por UF e no recorte
nacional e reconstrução da demonstração. Na CE/2023, HIV ficou pronto com 87
valores disponíveis, TRM-TB com 19 e cultura permaneceu com comparação
insuficiente, com 6.

O relatório reproduzível de impacto comparou o ranking sem e com a CAP-01. Os
sinais elevaram o escore de 26 municípios, incluíram 5 municípios no conjunto
ranqueado e mantiveram 8 dos 10 primeiros. O limite por dimensão retirou 2,0775
pontos de peso correlacionado. O relatório continua marcado como
`technical_validation_pending_domain_review`.

O `guia_validacao_de_dominio.md` apresenta fórmulas, amostra, cobertura,
impacto e formulário de decisão sem exigir conhecimento de programação. Restam
exclusivamente a revisão clínica e epidemiológica registrada nesse guia e o
teste de compreensão do fluxo com usuários de VAL-02. Até essas aprovações, as
regras e os cenários permanecem `pending_domain_review` e CAP-01 não atende ao
critério de saída.

**Critério de saída:** regras aprovadas e versionadas, casos de aceitação
oficiais, testes de regressão do ranking e explicações/recomendações coerentes na
API e no produto.

### CAP-02: tendências históricas e incidência crescente

**Objetivo:** distinguir um valor anual elevado de uma piora persistente no
tempo.

**Estado atual:** toda a infraestrutura e a apresentação histórica que não
dependem da escolha de um método estão implementadas. O armazenamento preserva
ano de análise, ano e tipo do denominador e proveniência estruturada. A mesma
série auditável aparece no armazenamento, na API, no relatório municipal e no
dossiê territorial, que distingue valor disponível, suprimido e ausente e
expõe as quebras de comparação sem classificá-las como tendência. A demonstração
inclui um agregado CE/2018-2023 verificável e carregado sem rede.

A auditoria técnica encontrou os 1.104 pontos esperados: 534 disponíveis, 570
suprimidos, nenhum ausente e nenhum com proveniência incompleta. Apenas 56 dos
184 municípios têm os seis anos publicáveis. Mudanças de situação da fonte e do
denominador foram mantidas como quebras explícitas. Nenhum cálculo de tendência,
cenário ou alteração de ranking foi implementado.

**Recorte inicial:** começar apenas pela série anual municipal de incidência de
TB já definida como `tb_incidence_per_100k`. O primeiro recorte não inclui
previsão, hotspot, causalidade, dados pessoais ou combinação opaca de
indicadores.

**Princípios técnicos:**

1. Preservar, para cada ano, numerador, denominador, fonte, ano do denominador,
   supressão, indisponibilidade e ressalvas.
1. Nunca preencher ano ausente com zero nem interpolar silenciosamente.
1. Separar prontidão da série, cálculo candidato e ativação no ranking.
1. Usar a mesma série no domínio, armazenamento, API, relatório e interface.
1. Manter qualquer regra de tendência como provisória até revisão clínica e
   epidemiológica.

**Sequência prevista de commits atômicos:**

1. `feat(storage): preserve annual indicator provenance`

   Preservar ano e tipo da população de referência e a proveniência estruturada
   dos indicadores. A migração mantém metadados legados como desconhecidos, sem
   inferi-los. **Implementado.**

1. `feat(storage): expose territorial indicator history`

   Criar consulta por indicador, território, recorte geográfico e intervalo de
   anos. Cobrir mistura de UFs, anos ausentes, valores suprimidos e fontes
   diferentes sem alterar cenários existentes. **Implementado.**

1. `feat(api): publish auditable incidence series`

   Expor contrato territorial de série histórica com os valores anuais e seus
   estados de qualidade. O endpoint deve validar indicador e intervalo, manter
   a proveniência e não calcular tendência na camada web. **Implementado.**

1. `chore(demo): bundle CE incidence history`

   Empacotar somente agregados municipais anuais de incidência do Ceará,
   acompanhados de manifesto, hashes e referências oficiais. A preparação deve
   funcionar sem baixar novamente os arquivos de origem. **Implementado.**

1. `feat(validation): audit incidence-series comparability`

   Gerar relatório por UF e período com cobertura anual, lacunas, mudanças de
   fonte ou ano do denominador, contagens suprimidas e municípios comparáveis.
   Preparar uma amostra CE reproduzível antes de propor um limiar. **Implementado.**

1. `feat(mvp1): evaluate provisional incidence trends`

   Somente depois da decisão de domínio sobre janela e método, implementar uma
   função transparente e testável. O resultado candidato deve ser auditável e
   permanecer fora do escore oficial enquanto estiver
   `pending_domain_review`. **Aguardando revisão de domínio.**

1. `feat(frontend): show municipal incidence history`

   Mostrar série, unidade, anos ausentes, supressão, fonte e ressalvas no dossiê
   territorial. A interface deve chamar crescimento de sinal histórico, nunca
   de previsão. **Implementado.**

1. `test(validation): measure CAP-02 ranking impact`

   Comparar o ranking sem e com a regra candidata, testar UF e Brasil, verificar
   estabilidade em pequenas contagens e registrar a decisão de ativação. A
   regra só passa a contribuir para o ranking após aprovação registrada.

**Decisões de domínio necessárias:** janela de anos, tratamento do período da
pandemia, definição de crescimento persistente, volume mínimo de casos,
comparabilidade de denominadores, tolerância a lacunas, gravidade e resposta
sugerida. O formulário completo está em `guia_validacao_de_dominio.md`.

**Critérios técnicos de aceitação:**

1. A mesma série anual é retornada pelo armazenamento e pela API.
1. Anos ausentes, suprimidos ou incompatíveis ficam explícitos.
1. Testes cobrem anos e UFs misturados e impedem vazamento entre escopos.
1. Um relatório reproduz a cobertura e a comparabilidade da série CE.
1. O cálculo candidato é determinístico, explica cada componente e não se
   apresenta como previsão.
1. A demonstração continua reproduzível e o impacto no ranking é mensurado.

**Critério de saída:** janela e método validados, prontidão por ano explícita,
série histórica acessível por API e produto, cenário reproduzível por testes,
impacto aceito por revisão de domínio e linguagem de incerteza aprovada.

### CAP-03: investigação de contatos com dados públicos

**Objetivo:** decidir com evidência se os campos públicos do SINAN-TB sustentam
um indicador territorial defensável de contatos examinados.

**Estado atual:** todo o recorte que não depende de decisão de domínio está
implementado sem incorporar o indicador ao produto. O comando isolado audita
CE/2018-2024, verifica hashes, preserva duas leituras para campos incompletos,
lista anomalias municipais, compara referências oficiais e reproduz cinco casos
de aceitação. O guia de validação apresenta a evidência e um formulário próprio
para a CAP-03.

Os sete arquivos conferiram com o manifesto, mas todos os anos têm valores
ausentes e municípios acima de 100%. A base pública atual calculou 80,83% para
CE/2022, contra 72,6% na publicação, e 80,05% para CE/2024, contra 79,4%.
Consequentemente, o relatório permanece
`technical_reconciliation_required` e o comando retorna erro depois de gravar
a evidência.

**Recorte técnico:** auditar os arquivos SINAN-TB de 2018 a 2024 em um comando
independente da ingestão e da demonstração. O relatório deve registrar os
artefatos e seus hashes, os filtros candidatos, a completude dos campos, duas
formas explícitas de somar registros incompletos, anomalias por município e a
comparação com referências oficiais. Divergências geram evidência e código de
erro; nunca são corrigidas silenciosamente.

**Contrato candidato:** contatos examinados divididos por contatos identificados
entre casos novos de TB pulmonar com confirmação laboratorial. A seleção usa
município de residência, tipos de entrada `1`, `4` e `6`, formas `1` e `3`,
exclui mudança de diagnóstico e considera confirmação por baciloscopia inicial
ou de acompanhamento, cultura positiva ou TRM-TB detectável. O contrato é uma
transcrição técnica para auditoria e permanece sujeito à revisão clínica e
epidemiológica.

**Sequência prevista de commits atômicos:**

1. `docs(roadmap): start CAP-03 contact validation`

   Formalizar o recorte, o contrato candidato e os bloqueadores sem alterar o
   produto público.

1. `feat(validation): audit SINAN contact investigation fields`

   Criar manifesto, auditoria CE/2018-2024, comparação com benchmarks oficiais,
   comando isolado e testes de filtros, incompletude, anomalias, hashes e códigos
   de saída.

1. `docs(validation): prepare CAP-03 domain review`

   Apresentar fórmula, evidências, divergências, amostra municipal e formulário
   de decisão em linguagem acessível a profissionais sem formação técnica.

**Fora deste recorte:** não adicionar campos ao agregado canônico de casos,
indicador, cenário, recomendação, persistência, API, ranking ou interface. O
alerta sintético de contato pendente permanece um fluxo operacional separado.

**Próximo bloqueador técnico:** obter a mesma versão congelada usada nas
publicações, ou uma exportação TabWin equivalente, para explicar as diferenças.
Essa tarefa é da equipe técnica. A revisão profissional deve decidir a semântica
e a utilidade do indicador, não reconciliar arquivos ou código.

**Critério de saída:** indicador implementado com sinalização de qualidade ou
decisão documentada de mantê-lo fora do produto público. O alerta sintético de
contato pendente permanece separado em ambos os casos.

**Estado de espera:** a implementação local necessária para produzir a
evidência está concluída, mas a reconciliação depende da versão congelada ou da
exportação TabWin usada nas publicações. A CAP-03 será retomada quando esse
artefato estiver disponível ou quando houver decisão epidemiológica documentada
de manter o indicador fora do produto. Essa espera não equivale a aprovação,
reprovação ou conclusão da capacidade.

### CAP-04: vigilância de resistência em camadas

**Objetivo:** separar lacunas de vigilância observáveis em dados públicos de
casos de resistência confirmada que exigem fonte autorizada.

**Estado atual:** iniciado porque o CAP-03 depende de insumo externo. O recorte
ativo implementará somente contratos e sinais sintéticos, proveniência
estruturada, leitura territorial descritiva e auditoria técnica. Não serão
carregados dados reais, inferida carga de resistência nem criados novos pontos
no ranking.

**Abordagem:** na camada territorial, combinar apenas sinais transparentes como
retratamento elevado e baixa realização de cultura ou TRM-TB, sempre rotulados
como lacuna de vigilância. Na camada operacional, aceitar resistência confirmada
somente quando estiver disponível um registro clínico ou laboratorial autorizado
que declare explicitamente essa condição.

**Critério de saída:** terminologia sem inferência clínica indevida, proveniência
visível, regras públicas testadas e contrato autorizado separado para sinais
confirmados.

### CAP-05: tratamento preventivo

**Objetivo:** monitorar início e, quando a fonte permitir, conclusão do tratamento
preventivo sem fabricar esse indicador a partir de campos incompatíveis.

**Abordagem:** criar um contrato agregado e opcional para relatórios municipais
ou integrações autorizadas com IL-TB, Silt ou Vigilantos. O contrato deve registrar
período, população elegível, iniciações, conclusões, proveniência e autorização.

**Critério de saída:** contrato e validações aprovados pela governança, dados de
demonstração permitidos e estado de indisponibilidade explícito quando nenhuma
fonte estiver configurada. Dados pessoais reais continuam fora do escopo atual.

### CAP-06: hotspots espaciais

**Objetivo:** identificar concentrações territoriais espacialmente consistentes
somente quando os dados sustentarem uma análise além do ranking por percentis.

**Abordagem:** começar por estatística espacial descritiva com biblioteca
estabelecida, vizinhança documentada, tratamento de pequenas contagens e
comparação contra o ranking atual. Um modelo preditivo somente pode ser proposto
com eventos de rastreio, covariáveis, desfecho definido e validação prospectiva.

**Critério de saída:** ganho decisório demonstrado, estabilidade avaliada,
incerteza comunicada e revisão epidemiológica. Sem esses elementos, o produto
deve continuar chamando a funcionalidade de priorização territorial, não de
previsão ou hotspot validado.

## Entregas transversais do Biochallenge

Estas entregas não mudam a ordem das capacidades, mas podem bloquear sua
conclusão ou a apresentação responsável do produto.

| ID | Entrega | Estado | Relação com o escopo |
| --- | --- | --- | --- |
| VAL-01 | Amostra oficial de aceitação CE/2023 | Em validação | Validação dos indicadores e regras |
| VAL-02 | Revisão de domínio e teste de fluxo com usuários | Pendente | Testes funcionais e validação do fluxo |
| DEMO-01 | Demonstração reproduzível sem download ao vivo | Pendente | Dados de demonstração e ensaio |
| GOV-01 | Revisão formal de LGPD, limites clínicos e governança | Pendente | Segurança e governança |
| PRES-01 | Resumo, pitch, apresentação e roteiro de demonstração | Pendente | Entregáveis finais |

VAL-01 e a revisão das regras em VAL-02 são bloqueadores para concluir CAP-01,
CAP-02 e qualquer outra capacidade que altere o ranking. GOV-01 é bloqueador
para qualquer integração municipal real de CAP-04 ou CAP-05.

## Próximo recorte

CAP-01 permanece em validação, com a implementação técnica concluída. O
trabalho para encerrá-la é:

1. Submeter o `guia_validacao_de_dominio.md`, a amostra CE/2023 e os relatórios
   de cobertura e ranking à revisão clínica e epidemiológica.
1. Validar com usuários a leitura das explicações, da prontidão e das respostas
   recomendadas.
1. Implementar e testar eventuais alterações, registrar a decisão e só então
   remover o estado provisório.

A infraestrutura, a auditoria, a documentação para revisão e a apresentação
histórica da CAP-02 estão prontas. O cálculo de tendência e a medição do impacto
no ranking permanecem bloqueados até que as decisões clínicas e epidemiológicas
do `guia_validacao_de_dominio.md` sejam preenchidas. Até essa revisão, o
recorte técnico independente ativo na ordem canônica é a auditoria das fontes
públicas da CAP-03. Ela permanece fora da ingestão, da demonstração e do ranking
até que a reconciliação com as referências oficiais e a revisão de domínio
estejam registradas.

Autenticação de produção, dados reais em nível de pessoa, automação clínica e
modelos preditivos permanecem fora do ciclo atual.
