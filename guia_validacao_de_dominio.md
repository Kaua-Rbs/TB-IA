# Guia de validação clínica e epidemiológica

Última atualização: 21 de julho de 2026.

## Finalidade

Este documento orienta a revisão humana das regras de saúde usadas pelo TB-IA.
Ele foi escrito para profissionais que não trabalham com programação. Não é
necessário abrir o código-fonte para preencher a revisão.

A versão atual detalha a validação da **CAP-01**, que prioriza municípios com
sinais comparativos de baixa testagem para HIV, baixo uso de TRM-TB e baixo uso
de cultura entre casos de retratamento. Ao final há também a lista inicial de
decisões clínicas necessárias para a CAP-02, sobre tendências históricas.

## Quem deve revisar

A aprovação deve ser liderada, idealmente, por médico com experiência em
tuberculose, vigilância em saúde ou epidemiologia. A participação de
profissional da vigilância municipal ou estadual, enfermagem do programa de TB
e análise de dados é recomendada porque cada área observa riscos diferentes.

A equipe de desenvolvimento pode preparar tabelas e demonstrar o produto, mas
não deve aprovar sozinha definições epidemiológicas, gravidade, condutas
sugeridas ou utilidade assistencial.

## O que esta revisão decide

A revisão deve responder a quatro perguntas:

1. Os grupos de pessoas e resultados de exames foram contados corretamente?
1. É útil destacar os municípios dessa forma, sem criar uma falsa meta oficial?
1. O peso no ranking e as ações sugeridas são proporcionais ao sinal observado?
1. As explicações são claras e não parecem diagnóstico, prescrição ou avaliação
   individual de pacientes?

As respostas possíveis para cada item são:

- **Aprovar:** a regra pode deixar de ser provisória.
- **Aprovar com alterações:** a equipe deve implementar e testar as mudanças
  antes de nova assinatura.
- **Reprovar:** a regra não deve participar do ranking.
- **Inconclusivo:** faltam fonte, amostra ou especialista para decidir.

## Limite de segurança

O TB-IA usa dados públicos agregados por município. A CAP-01 não identifica
pessoas, não diagnostica tuberculose ou resistência, não prescreve exames e não
avalia a qualidade de um profissional ou serviço isolado.

Um sinal no ranking significa apenas: "este valor municipal está entre os mais
baixos do grupo comparado e merece revisão do programa". Ele não prova falha
assistencial e não substitui a análise do contexto local.

## CAP-01 em linguagem simples

### O que cada indicador mede

| Sinal | Numerador | Denominador | Leitura pretendida |
| --- | --- | --- | --- |
| Testagem para HIV | Casos novos de TB com resultado de HIV positivo ou negativo | Casos novos de TB | Percentual de casos novos com testagem concluída |
| Uso de TRM-TB | Casos novos de TB pulmonar com resultado registrado de TRM-TB | Casos novos de TB pulmonar | Percentual em que o teste molecular foi realizado |
| Cultura no retratamento | Casos pulmonares de recidiva ou reingresso após abandono com cultura positiva ou negativa | Casos pulmonares de recidiva ou reingresso após abandono | Percentual em que a cultura foi realizada |

Resultado "em andamento", exame não realizado, campo ignorado ou campo vazio não
entra no numerador. Valor ausente ou suprimido não é tratado como desempenho
baixo.

### Como um município é destacado

Para cada indicador, o sistema compara apenas valores disponíveis no mesmo ano
e no mesmo recorte geográfico. O limite atual é o percentil 25, chamado de
`p25`: aproximadamente o quarto inferior dos valores disponíveis.

Estar abaixo desse limite não significa descumprir uma meta do Ministério da
Saúde. É somente uma forma comparativa de organizar a revisão. As três regras
têm gravidade moderada enquanto aguardam aprovação.

### Como o ranking evita contagem repetida

Cada sinal pertence a um tema:

| Sinal novo | Tema do ranking | Ação atualmente sugerida |
| --- | --- | --- |
| Baixa testagem para HIV | Integração TB-HIV | Revisar integração TB-HIV |
| Baixo uso de TRM-TB | Acesso ao diagnóstico | Revisar fluxo diagnóstico |
| Baixo uso de cultura no retratamento | Vigilância de resistência | Revisar vigilância de resistência |

Quando dois sinais do mesmo tema aparecem no mesmo município, todos continuam
visíveis, mas apenas o maior peso do tema entra no total. O revisor deve
confirmar se esses agrupamentos representam problemas suficientemente
correlacionados.

## Interpretações que exigem aprovação de domínio

As decisões abaixo não podem ser encerradas apenas por testes de software.

### Universo e campos do SINAN-TB

1. **Casos novos:** confirmar se os tipos de entrada usados como caso novo são
   "caso novo", "não sabe" e "pós-óbito" para os três indicadores aplicáveis.
1. **Município e período:** confirmar o uso do município de residência e do ano
   de notificação, além do tratamento esperado para registros duplicados ou
   atualizados.
1. **HIV:** confirmar que somente resultados positivo e negativo representam
   testagem concluída; "em andamento" e "não realizado" ficam fora.
1. **Forma pulmonar:** confirmar que formas pulmonar e mista entram nos
   indicadores pulmonares.
1. **TRM-TB realizado:** confirmar que resultados "detectável sensível à
   rifampicina", "detectável resistente à rifampicina", "não detectável" e
   "inconclusivo" representam teste realizado. Confirmar separadamente que
   apenas os dois resultados detectáveis contam como confirmação laboratorial.
1. **Retratamento:** confirmar que recidiva e reingresso após abandono formam o
   universo de retratamento usado aqui.
1. **Cultura realizada:** confirmar que cultura positiva e negativa representam
   realização; "em andamento" não entra.

### Qualidade e representatividade

1. Confirmar que um registro público representa uma notificação utilizável e
   que o método de atualização ou deduplicação do SINAN-TB é adequado.
1. Avaliar se o arquivo preliminar de 2023 é aceitável para demonstração e quais
   ressalvas devem acompanhar uma análise oficial.
1. Avaliar o viés causado pela supressão de valores com numerador menor que
   cinco. Essa proteção remove justamente muitos municípios com poucas
   realizações e pode limitar a interpretação.
1. Confirmar se dez valores disponíveis e cobertura mínima de 5% são suficientes
   para calcular um limite comparativo.
1. Decidir se uma comparação dentro da UF e uma comparação nacional são ambas
   epidemiologicamente interpretáveis.

### Regra e resposta sugerida

1. Confirmar, alterar ou rejeitar o `p25` como limite comparativo.
1. Confirmar, alterar ou rejeitar gravidade moderada para cada um dos três
   sinais.
1. Confirmar se os três temas do ranking evitam dupla contagem sem esconder
   problemas independentes.
1. Confirmar se as ações sugeridas são úteis para gestão municipal e não induzem
   uma conduta clínica automática.
1. Revisar os textos mostrados no produto para garantir que "prioridade" não seja
   lida como diagnóstico, punição, meta ministerial ou prova de baixa qualidade.

## Evidência técnica já disponível

Os itens desta seção mostram o que o software já verificou. Eles não substituem
as decisões anteriores.

### Amostra CE/2023

Uma amostra técnica registra numerador, denominador, resultado esperado e
identificador dos arquivos de origem para cinco municípios:

| Município | HIV testado | TRM-TB realizado | Cultura no retratamento |
| --- | ---: | ---: | ---: |
| Fortaleza | 1.163/1.467 = 79,28% | 480/1.285 = 37,35% | 85/462 = 18,40% |
| Caucaia | 174/215 = 80,93% | 42/184 = 22,83% | 10/61 = 16,39% |
| Sobral | 129/129 = 100,00% | 113/117 = 96,58% | 7/30 = 23,33% |
| Maracanaú | 86/96 = 89,58% | 30/93 = 32,26% | Suprimido: 1/18 |
| Quixadá | 10/11 = 90,91% | Suprimido: 0/10 | Suprimido: 0/4 |

O revisor de domínio deve conferir a interpretação da ficha e, com apoio de um
analista quando necessário, reproduzir ao menos os casos que considerar
críticos diretamente na fonte oficial.

### Cobertura no Ceará

A reconstrução de 2023 contém 184 municípios canônicos:

| Regra | Disponíveis | Suprimidos | Indisponíveis | Cobertura | Resultado |
| --- | ---: | ---: | ---: | ---: | --- |
| HIV | 87 | 86 | 11 | 47,28% | Pronta; limite 87,16%; 23 sinais |
| TRM-TB | 19 | 154 | 11 | 10,33% | Pronta; limite 23,68%; 5 sinais |
| Cultura | 6 | 167 | 11 | 3,26% | Comparação insuficiente; nenhum sinal |

A ausência de cenário de cultura é intencional: a regra não calcula limite com
apenas seis valores disponíveis. O revisor deve decidir se essa proteção é
suficiente ou se a regra deve exigir cobertura maior.

A verificação automática dos 1.716 valores de indicadores encontrou zero
proporções fora dos limites matemáticos. Foram registrados 93 avisos de
denominador zero, mantidos como ausência explícita em vez de valor calculado.

### Efeito no ranking CE/2023

O relatório compara duas versões usando exatamente a mesma fórmula de ranking:

- **Base:** regras atuais, sem os três sinais da CAP-01.
- **Candidata:** mesmas regras, com os sinais provisórios da CAP-01.

Resultado observado:

| Medida | Resultado |
| --- | ---: |
| Cenários antes/depois | 81 / 109 |
| Municípios ranqueados antes/depois | 52 / 57 |
| Municípios com aumento direto de escore | 26 |
| Municípios novos no ranking | 5 |
| Municípios mantidos entre os dez primeiros | 8 de 10 |
| Maior aumento de escore | 4,3448 pontos |
| Peso correlacionado retirado pelo limite por tema | 2,0775 pontos |

Aquiraz e Jijoca de Jericoacoara entraram nos dez primeiros; Frecheirinha e
Pacajus saíram. Itaitinga e Fortaleza permaneceram nas duas primeiras posições.
Essas mudanças são fatos reproduzíveis, não evidência de que o novo ranking seja
clinicamente melhor.

Um teste automatizado separado confirma que as três regras podem ser calculadas
por UF e no recorte nacional quando existe cobertura suficiente. Esse teste usa
dados artificiais; ainda não substitui uma validação nacional com dados oficiais.

## Roteiro sugerido para a reunião

1. Ler as seções "Limite de segurança" e "CAP-01 em linguagem simples".
1. Conferir as sete decisões sobre universo e campos do SINAN-TB.
1. Revisar a tabela de cinco municípios e solicitar a abertura da fonte oficial
   para qualquer valor duvidoso.
1. Avaliar a cobertura e discutir especialmente a grande quantidade de valores
   suprimidos.
1. Comparar as duas listas de dez municípios e discutir se as mudanças parecem
   úteis, enganosas ou excessivas.
1. Abrir o produto e pedir que um usuário da vigilância explique, com suas
   próprias palavras, o motivo de um município estar priorizado.
1. Preencher e assinar o registro de decisão abaixo.

## Registro de decisão da CAP-01

| ID | Decisão | Aprovar | Alterar | Reprovar | Inconclusivo | Observações |
| --- | --- | :---: | :---: | :---: | :---: | --- |
| D01 | Universo de casos novos | [ ] | [ ] | [ ] | [ ] | |
| D02 | Município, período e duplicidades | [ ] | [ ] | [ ] | [ ] | |
| D03 | Resultado de HIV concluído | [ ] | [ ] | [ ] | [ ] | |
| D04 | Formas pulmonar e mista | [ ] | [ ] | [ ] | [ ] | |
| D05 | TRM-TB realizado e confirmação | [ ] | [ ] | [ ] | [ ] | |
| D06 | Universo de retratamento | [ ] | [ ] | [ ] | [ ] | |
| D07 | Cultura realizada | [ ] | [ ] | [ ] | [ ] | |
| D08 | Supressão e representatividade | [ ] | [ ] | [ ] | [ ] | |
| D09 | Mínimo de 10 valores e 5% de cobertura | [ ] | [ ] | [ ] | [ ] | |
| D10 | Limite comparativo p25 | [ ] | [ ] | [ ] | [ ] | |
| D11 | Gravidade moderada | [ ] | [ ] | [ ] | [ ] | |
| D12 | Agrupamento dos temas | [ ] | [ ] | [ ] | [ ] | |
| D13 | Ações sugeridas e linguagem de segurança | [ ] | [ ] | [ ] | [ ] | |
| D14 | Impacto observado no ranking | [ ] | [ ] | [ ] | [ ] | |
| D15 | Compreensão do fluxo por usuários | [ ] | [ ] | [ ] | [ ] | |

**Decisão geral:** [ ] aprovar [ ] aprovar com alterações [ ] reprovar [ ]
inconclusivo

**Alterações obrigatórias antes da aprovação:**

______________________________________________________________________

**Nome do revisor responsável:**

**Formação e função:**

**Instituição:**

**Data:**

**Versão ou identificação das fontes consultadas:**

**Assinatura ou registro equivalente:**

A CAP-01 só pode ser marcada como concluída quando os itens essenciais forem
aprovados, as alterações pedidas forem implementadas e testadas, e o teste de
compreensão com usuários estiver registrado. Até lá, as regras devem continuar
marcadas como provisórias.

## Decisões de domínio antecipadas para a CAP-02

A CAP-02 pretende diferenciar incidência alta em um único ano de crescimento
persistente. Antes de ativar qualquer novo sinal no ranking, a revisão clínica e
epidemiológica deverá decidir:

1. Quantos anos formam uma série suficientemente longa.
1. Como tratar 2020 e 2021 e possíveis mudanças de notificação durante a
   pandemia.
1. O que significa "crescimento": anos consecutivos, variação percentual,
   inclinação de uma série ou outra regra transparente.
1. Qual volume mínimo de casos reduz oscilações enganosas em municípios
   pequenos.
1. Quando mudanças de denominador populacional impedem comparação direta.
1. Quanta ausência de anos ou fontes torna a tendência inconclusiva.
1. Qual gravidade e qual resposta municipal correspondem ao sinal.
1. Como explicar incerteza sem apresentar tendência como previsão.

Essas decisões estão abertas. O planejamento técnico da CAP-02 deve produzir
séries auditáveis e relatórios de qualidade antes de pedir aprovação de uma
regra.

## Onde encontrar a evidência

A equipe técnica pode apresentar os seguintes artefatos sem exigir que o revisor
os edite:

- Amostra municipal:
  `src/tbia/resources/validation/sinan_diagnostic_acceptance_ce_2023.json`.
- Auditoria dos campos SINAN-TB:
  `data/processed/mvp1/validation/sinan_mapping_ce_2023.json`.
- Validação matemática dos indicadores:
  `data/processed/mvp1/validation/indicator_validation_ce_2023.json`.
- Comparação do ranking:
  `data/processed/mvp1/validation/diagnostic_ranking_impact_ce_2023.json`.
- Interface de demonstração: `/territorios`, após executar `make demo` e
  iniciar o servidor.

Os arquivos gerados em `data/processed/` são evidência reproduzível local e
não são versionados no Git. Os identificadores criptográficos dos arquivos DBC
e DBF usados na amostra ficam registrados no próprio arquivo da amostra.
