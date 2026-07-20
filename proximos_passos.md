# Próximos passos

Última revisão: 20 de julho de 2026.

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
| 2 | CAP-02 | Tendências históricas e incidência crescente | **Planejada** |
| 3 | CAP-03 | Investigação de contatos com dados públicos | **Planejada** |
| 4 | CAP-04 | Vigilância de resistência em camadas | **Planejada** |
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

**Estado atual:** implementação, aceitação técnica, persistência, API,
localização e testes automatizados concluídos. Na reconstrução CE/2023 com 184
municípios, testagem de HIV ficou pronta com 87 valores disponíveis e TRM-TB com
19; cultura permaneceu com comparação insuficiente, com 6 valores disponíveis.
As duas regras prontas geraram cenários marcados como
`pending_domain_review`; cultura não gerou limiar nem cenário. Os gates
`make check`, `make coverage`, `make frontend-check` e `make demo`
passaram. Permanecem pendentes a revisão epidemiológica dos limiares,
severidades e estratégias e o teste de fluxo com usuários de VAL-02. Até essa
aprovação, CAP-01 não atende ao critério de saída.

**Critério de saída:** regras aprovadas e versionadas, casos de aceitação
oficiais, testes de regressão do ranking e explicações/recomendações coerentes na
API e no produto.

### CAP-02: tendências históricas e incidência crescente

**Objetivo:** distinguir um valor anual elevado de uma piora persistente no
tempo.

**Abordagem:** preparar séries anuais comparáveis por município e UF, exigir
anos e denominadores completos e definir uma regra transparente de crescimento
sustentado. A análise deve reduzir instabilidade de percentuais em municípios
com contagens pequenas e manter o ano isolado disponível para auditoria.

**Critério de saída:** janela temporal validada, prontidão por ano explícita,
série histórica acessível por API e cenário de tendência reproduzível por testes.

### CAP-03: investigação de contatos com dados públicos

**Objetivo:** decidir com evidência se os campos públicos do SINAN-TB sustentam
um indicador territorial defensável de contatos examinados.

**Abordagem:** confrontar os campos com o dicionário e o caderno oficial de
indicadores, auditar completude e categorias e reproduzir manualmente uma
amostra municipal. A implementação somente segue se numerador, denominador e
universo forem semanticamente confiáveis.

**Critério de saída:** indicador implementado com sinalização de qualidade ou
decisão documentada de mantê-lo fora do produto público. O alerta sintético de
contato pendente permanece separado em ambos os casos.

### CAP-04: vigilância de resistência em camadas

**Objetivo:** separar lacunas de vigilância observáveis em dados públicos de
casos de resistência confirmada que exigem fonte autorizada.

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

CAP-01 permanece em validação; não há outro recorte de implementação ativo.
O trabalho imediato é de validação e deve ser registrado em avanços atômicos:

1. Submeter a amostra CE/2023, os denominadores e os gates de cobertura à revisão
   epidemiológica.
1. Validar com usuários a leitura das explicações, da prontidão e das respostas
   recomendadas.
1. Registrar decisões sobre limiar, severidade e estratégia; se aprovadas,
   versionar as regras e substituir o estado provisório.
1. Marcar CAP-01 como concluída somente após VAL-01 e a revisão aplicável de
   VAL-02. CAP-02 passa a ser a próxima implementação depois dessa decisão.

Autenticação de produção, dados reais em nível de pessoa, automação clínica e
modelos preditivos permanecem fora do ciclo atual.
