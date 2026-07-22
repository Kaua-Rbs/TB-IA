# Guia de validação clínica e epidemiológica

Última atualização: 21 de julho de 2026.

## Finalidade

Este documento orienta a revisão humana das regras de saúde usadas pelo TB-IA.
Ele foi escrito para profissionais que não trabalham com programação. Não é
necessário abrir o código-fonte para preencher a revisão.

A versão atual detalha quatro revisões. A **CAP-01** prioriza municípios com
sinais comparativos de baixa testagem para HIV, baixo uso de TRM-TB e baixo uso
de cultura entre casos de retratamento. A **CAP-02** apresenta a série histórica
de incidência, suas quebras de comparabilidade e as decisões necessárias antes
de criar qualquer regra de crescimento. A **CAP-03** avalia se os campos
públicos de investigação de contatos permitem construir um indicador municipal
confiável; esse indicador ainda não faz parte do produto. A **CAP-04** separa
lacunas territoriais observáveis em dados públicos de evidências operacionais
sintéticas e registra o que deve ser validado antes de interpretar os sinais ou
usar uma fonte municipal real.

## Quem deve revisar

A aprovação deve ser liderada, idealmente, por médico com experiência em
tuberculose, vigilância em saúde ou epidemiologia. A participação de
profissional da vigilância municipal ou estadual, enfermagem do programa de TB
e análise de dados é recomendada porque cada área observa riscos diferentes.

A equipe de desenvolvimento pode preparar tabelas e demonstrar o produto, mas
não deve aprovar sozinha definições epidemiológicas, gravidade, condutas
sugeridas ou utilidade assistencial.

Para a CAP-04, a revisão de domínio deve incluir experiência no programa de TB
e em vigilância laboratorial. Uma futura integração municipal real também exige
responsáveis por LGPD, segurança da informação e governança institucional; o
parecer clínico ou epidemiológico não substitui essas autorizações.

## O que esta revisão decide

A revisão deve responder a cinco perguntas:

1. Os grupos de pessoas e resultados de exames foram contados corretamente?
1. É útil destacar os municípios dessa forma, sem criar uma falsa meta oficial?
1. O peso no ranking e as ações sugeridas são proporcionais ao sinal observado?
1. As explicações são claras e não parecem diagnóstico, prescrição ou avaliação
   individual de pacientes?
1. A origem, a autorização e os controles de acesso são adequados para o uso
   pretendido?

### Respostas possíveis

- **Aprovar:** a regra pode deixar de ser provisória.
- **Aprovar com alterações:** a equipe deve implementar e testar as mudanças
  antes de nova assinatura.
- **Reprovar:** a regra ou o fluxo não deve ser ativado no uso avaliado.
- **Inconclusivo:** faltam fonte, amostra ou especialista para decidir.

## Limite de segurança

O TB-IA usa dados públicos agregados por município na análise territorial e
somente dados sintéticos, identificados por pseudônimos, na demonstração
operacional atual. Nenhuma capacidade descrita neste guia diagnostica
tuberculose ou resistência, prescreve exames ou avalia isoladamente a qualidade
de um profissional ou serviço.

Um sinal no ranking significa apenas: "este valor municipal está entre os mais
baixos do grupo comparado e merece revisão do programa". Ele não prova falha
assistencial e não substitui a análise do contexto local. Um alerta operacional
significa que existe evidência ou pendência registrada para revisão humana; ele
também não confirma diagnóstico por conta própria.

Dados reais em nível de pessoa continuam proibidos até que fonte, finalidade,
autorização, acesso, retenção, auditoria e resposta a incidentes sejam aprovados
em GOV-01.

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

## CAP-02 em linguagem simples

### O que a série mede

A série disponível mostra a incidência anual de tuberculose por município entre
2018 e 2023. Para cada ano, o cálculo usado na demonstração é:

```text
casos novos de TB notificados / população de referência x 100.000
```

O numerador atual considera notificações classificadas pelos códigos 1, 4 e 6 do
campo `TRATAMENTO` do SINAN-TB. A revisão de domínio deve confirmar se esse
universo e o tratamento de duplicidades ou atualizações representam corretamente
"casos novos" para a finalidade proposta.

A taxa permite comparar populações de tamanhos diferentes, mas não mostra risco
individual, não explica por que houve mudança e não prevê o ano seguinte. Um
aumento também não prova, sozinho, piora da assistência: pode refletir
transmissão, busca ativa, acesso ao diagnóstico, atualização da base ou mudança
do denominador.

### O que a verificação técnica encontrou

O pacote CE/2018-2023 contém exatamente 184 municípios e seis observações por
município, totalizando 1.104 registros agregados. Nenhum registro esperado está
ausente e todos têm fonte, período e denominador identificados.

Valores com menos de cinco casos são ocultados para evitar exposição indevida de
contagens pequenas. Eles permanecem marcados como **suprimidos** e nunca são
substituídos por zero. Por isso, existência do registro não significa que a taxa
possa ser mostrada ou comparada.

| Ano | Taxas disponíveis | Suprimidas | Situação do SINAN-TB | População usada | Atenção |
| --- | ---: | ---: | --- | --- | --- |
| 2018 | 95 | 89 | Final | Estimativa de 2018 | Início da série |
| 2019 | 83 | 101 | Final | Estimativa de 2019 | Mesma família de denominador |
| 2020 | 83 | 101 | Preliminar | Estimativa de 2020 | Mudança da situação da fonte e pandemia |
| 2021 | 89 | 95 | Preliminar | Estimativa de 2021 | Período da pandemia |
| 2022 | 90 | 94 | Preliminar | Censo de 2022 | Mudança de estimativa para Censo |
| 2023 | 94 | 90 | Preliminar | Censo de 2022 | Eventos de 2023 sobre população de 2022 |

No total, 534 taxas podem ser mostradas e 570 estão suprimidas. Somente 56 dos
184 municípios têm os seis anos disponíveis. Os outros 128 têm ao menos um ano
suprimido. O rótulo técnico "candidato à comparação" significa apenas série
completa e proveniência preenchida; não significa que a comparação tenha sido
aprovada por médico ou epidemiologista.

### Exemplos para conferência

Os cinco municípios abaixo foram escolhidos para uma conferência reproduzível,
não porque representem todo o Ceará. Todos têm os seis anos disponíveis. Os
valores são taxas por 100 mil habitantes, arredondadas para duas casas.

| Município | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Fortaleza | 60,27 | 59,60 | 48,87 | 47,38 | 59,58 | 60,40 |
| Caucaia | 54,12 | 42,06 | 44,08 | 44,18 | 53,14 | 60,45 |
| Sobral | 74,52 | 74,19 | 57,42 | 57,43 | 71,91 | 63,54 |
| Maracanaú | 49,53 | 48,27 | 38,35 | 41,99 | 39,23 | 40,94 |
| Quixadá | 25,25 | 26,22 | 18,12 | 34,87 | 19,01 | 13,07 |

Fortaleza ilustra por que a inspeção humana é necessária. Entre 2021 e 2022, os
casos novos passam de 1.281 para 1.447, enquanto o denominador muda de uma
estimativa de 2.703.391 habitantes para 2.428.708 habitantes no Censo. A taxa
resultante sobe de 47,38 para 59,58. O software registra os dois movimentos, mas
não decide quanto da diferença representa mudança epidemiológica.

### Quebras que exigem decisão de domínio

1. **Situação da fonte:** 2018 e 2019 usam arquivos finais; 2020 a 2023 usam
   arquivos preliminares. O revisor deve decidir se podem participar da mesma
   análise e qual ressalva é obrigatória.
1. **Pandemia:** notificações e acesso ao diagnóstico em 2020 e 2021 podem ter
   sido afetados. O revisor deve decidir se esses anos entram, ficam destacados
   ou impedem determinada interpretação.
1. **Método populacional:** a série troca estimativas anuais pelo Censo em 2022.
   O revisor deve decidir se a quebra permite comparação direta ou exige outro
   denominador.
1. **Ano do denominador:** a taxa de 2023 usa casos de 2023 e população do Censo
   de 2022, em alinhamento com a demonstração atual. Essa escolha precisa ser
   aceita ou substituída.
1. **Supressão:** municípios pequenos frequentemente não têm uma sequência
   publicável. O revisor deve decidir quantos anos disponíveis bastam e se uma
   lacuna torna o resultado inconclusivo.

### O que o software ainda não decidiu

Nenhuma regra de tendência foi implementada. O sistema ainda não:

- escolhe uma janela de três, quatro, cinco ou seis anos;
- classifica crescimento por anos consecutivos, diferença percentual ou
  inclinação;
- corrige ou exclui automaticamente os anos da pandemia;
- define volume mínimo de casos ou população;
- preenche anos suprimidos, calcula previsão ou atribui causalidade;
- atribui gravidade, recomendação ou pontos no ranking pela série histórica.

Essas ausências são intencionais. Implementar uma fórmula antes das decisões
abaixo criaria uma regra de saúde sem aprovação adequada.

## Roteiro sugerido para a revisão da CAP-02

1. Confirmar a definição de caso novo e o período de notificação usado.
1. Ler a tabela de cobertura e distinguir dado suprimido de dado ausente.
1. Conferir os cinco exemplos diretamente na fonte ou em uma extração oficial
   aceita pelo revisor.
1. Discutir separadamente as quatro quebras: arquivos preliminares, pandemia,
   troca para o Censo e uso da população de 2022 em 2023.
1. Escolher uma regra simples e explicável somente se a série for considerada
   comparável.
1. Definir quando a regra deve responder "inconclusivo" em vez de classificar o
   município.
1. Revisar a linguagem, a possível resposta municipal e qualquer peso no
   ranking.
1. Registrar a decisão e as fontes consultadas no formulário abaixo.

## Registro de decisão da CAP-02

| ID | Decisão | Aprovar | Alterar | Reprovar | Inconclusivo | Observações |
| --- | --- | :---: | :---: | :---: | :---: | --- |
| D02-01 | Universo de casos novos, período e duplicidades | [ ] | [ ] | [ ] | [ ] | |
| D02-02 | Uso conjunto de arquivos finais e preliminares | [ ] | [ ] | [ ] | [ ] | |
| D02-03 | Tratamento de 2020 e 2021 | [ ] | [ ] | [ ] | [ ] | |
| D02-04 | Troca de estimativa populacional para Censo | [ ] | [ ] | [ ] | [ ] | |
| D02-05 | Casos de 2023 sobre população de 2022 | [ ] | [ ] | [ ] | [ ] | |
| D02-06 | Quantidade de anos da janela | [ ] | [ ] | [ ] | [ ] | |
| D02-07 | Tolerância a anos suprimidos ou ausentes | [ ] | [ ] | [ ] | [ ] | |
| D02-08 | Definição matemática de crescimento persistente | [ ] | [ ] | [ ] | [ ] | |
| D02-09 | Volume mínimo de casos ou população | [ ] | [ ] | [ ] | [ ] | |
| D02-10 | Critério para resultado inconclusivo | [ ] | [ ] | [ ] | [ ] | |
| D02-11 | Gravidade e resposta municipal sugerida | [ ] | [ ] | [ ] | [ ] | |
| D02-12 | Linguagem de incerteza e segurança | [ ] | [ ] | [ ] | [ ] | |
| D02-13 | Peso e ativação futura no ranking | [ ] | [ ] | [ ] | [ ] | |
| D02-14 | Compreensão do fluxo por usuários | [ ] | [ ] | [ ] | [ ] | |

**Janela escolhida:**

**Regra de crescimento escolhida, em linguagem simples:**

**Anos ou situações que impedem o cálculo:**

**Volume mínimo escolhido e justificativa:**

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

A equipe técnica só deve implementar a regra candidata depois que janela,
método, exceções e volume mínimo estiverem preenchidos. A CAP-02 só pode alterar
o ranking depois que o impacto da regra implementada também for apresentado e
aceito em nova revisão.

## CAP-03 em linguagem simples

### Qual pergunta está sendo investigada

A investigação de contatos procura saber quantas pessoas que tiveram contato
com um caso de tuberculose foram identificadas e quantas foram efetivamente
examinadas. A fórmula candidata é:

```text
contatos examinados / contatos identificados x 100
```

Ela seria calculada somente para casos novos de tuberculose pulmonar confirmados
por exame laboratorial. Uma proporção municipal baixa poderia apontar uma
oportunidade para revisar o processo de investigação, mas não provaria falha de
uma equipe ou serviço.

O alerta de contato pendente já presente na demonstração municipal é diferente.
Ele usa dados sintéticos de acompanhamento individual e uma regra de prazo. A
CAP-03 avalia contagens públicas agregadas do SINAN-TB e não pode substituir
esse fluxo operacional.

### Universo candidato usado na auditoria

| Parte da seleção | Interpretação técnica usada |
| --- | --- |
| Período | Ano registrado em `NU_ANO` |
| Município | Município de residência em `ID_MN_RESI` |
| Tipo de entrada | Caso novo, não sabe e pós-óbito, códigos `1`, `4` e `6` |
| Forma clínica | Pulmonar ou pulmonar e extrapulmonar, códigos `1` e `3` |
| Encerramento | Todas as situações, exceto mudança de diagnóstico, código `6` |
| Confirmação laboratorial | Baciloscopia inicial positiva, segunda baciloscopia positiva, cultura positiva ou TRM-TB detectável |
| Contatos identificados | Soma de `NU_CONTATO` |
| Contatos examinados | Soma de `NU_COMU_EX` |

Essa tabela transcreve o método candidato para permitir auditoria. Ela não
significa que a equipe clínica e epidemiológica já aprovou a interpretação dos
campos ou o uso municipal do resultado.

### Duas somas que não devem ser confundidas

Existem registros em que somente uma das duas contagens está preenchida. Por
isso, a auditoria apresenta duas leituras:

- **Valores registrados:** soma cada campo quando ele está preenchido. Um campo
  vazio não é somado, mas também não é chamado de zero.
- **Pares completos:** usa somente registros em que as duas contagens estão
  preenchidas.

As duas leituras produzem resultados diferentes. O software não escolheu uma
delas como correta e não preencheu valores ausentes.

### Resultado técnico de 2018 a 2024

Todos os arquivos e seus identificadores criptográficos conferiram com o
manifesto técnico. Mesmo assim, todos os anos apresentaram contagens ausentes e
registros ou municípios com examinados acima de identificados.

| Ano | Casos elegíveis | Valores registrados | Identificados ausentes | Examinados ausentes | Municípios acima de 100% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2018 | 2.331 | 7.698/9.627 = 79,96% | 9 | 200 | 5 |
| 2019 | 2.306 | 7.156/10.383 = 68,92% | 28 | 315 | 4 |
| 2020 | 1.885 | 6.000/7.483 = 80,18% | 34 | 228 | 2 |
| 2021 | 1.970 | 5.691/6.878 = 82,74% | 26 | 261 | 1 |
| 2022 | 2.208 | 5.948/7.359 = 80,83% | 17 | 318 | 1 |
| 2023 | 2.223 | 5.648/7.023 = 80,42% | 29 | 376 | 4 |
| 2024 | 2.146 | 5.821/7.272 = 80,05% | 30 | 363 | 2 |

“Acima de 100%” significa que a soma de examinados ficou maior que a de
identificados. A auditoria apenas sinaliza essa inconsistência. Ela não limita o
resultado a 100%, não troca valores e não descarta silenciosamente o município.

### Comparação com publicações oficiais

| Coorte | Publicação oficial | Base pública atual | Diferença identificados/examinados |
| --- | ---: | ---: | ---: |
| CE/2022 | 4.684/6.449 = 72,6% | 5.948/7.359 = 80,83% | +910 / +1.264 |
| CE/2024 | 5.921/7.454 = 79,4% | 5.821/7.272 = 80,05% | -182 / -100 |

As publicações usaram bancos extraídos e qualificados em momentos específicos.
Os arquivos públicos atuais podem ter sido revisados depois dessas extrações.
Enquanto a equipe técnica não reproduzir os totais com a mesma versão da fonte
ou explicar formalmente a diferença, a CAP-03 permanece em reconciliação
técnica e nenhum resultado deve ser apresentado como indicador validado.

### Cinco municípios para conferência

Os valores abaixo usam a coorte CE/2024. “Registrados” e “pares completos” são
as duas leituras descritas anteriormente.

| Município | Registrados | Pares completos | Ausentes identificados/examinados | Registros acima |
| --- | ---: | ---: | ---: | ---: |
| Fortaleza | 991/2.026 = 48,91% | 988/1.545 = 63,95% | 17 / 251 | 5 |
| Caucaia | 305/399 = 76,44% | 305/357 = 85,43% | 0 / 16 | 0 |
| Sobral | 334/311 = 107,40% | 332/311 = 106,75% | 1 / 0 | 4 |
| Maracanaú | 82/108 = 75,93% | 82/89 = 92,13% | 1 / 7 | 0 |
| Quixadá | 6/7 = 85,71% | 6/7 = 85,71% | 1 / 3 | 0 |

Esses casos foram reproduzidos automaticamente contra o arquivo cujo hash está
no manifesto. A conferência profissional deve se concentrar no significado e
na utilidade dos resultados, especialmente na grande diferença causada pelos
campos ausentes e no resultado impossível de Sobral.

### Responsabilidade técnica antes da aprovação

A reconciliação abaixo é responsabilidade da equipe de dados e não deve ser
transferida ao profissional de saúde. Quando possível, ela deve contar com um
operador do SINAN ou do TabWin que conheça a extração oficial.

A equipe técnica ainda deve:

1. Obter a versão congelada ou uma exportação TabWin equivalente usada no
   Boletim Epidemiológico de Tuberculose de março de 2024, extraída em fevereiro
   de 2024 para a coorte CE/2022.
1. Obter a versão congelada ou uma exportação TabWin equivalente usada no
   Boletim Epidemiológico de Tuberculose de março de 2026, extraída em fevereiro
   de 2026 para a coorte CE/2024.
1. Confirmar os filtros, categorias, exclusões e a operação do TabWin usados na
   Tabela 7 das duas publicações.
1. Reproduzir os totais oficiais de 4.684 examinados entre 6.449 identificados
   para CE/2022 e 5.921 entre 7.454 para CE/2024, ou explicar formalmente uma
   diferença causada por versão ou qualificação posterior do SINAN-TB.
1. Registrar a origem, data, versão e identificador criptográfico dos arquivos,
   além dos filtros e resultados da nova tabulação.
1. Reexecutar a auditoria e conferir Fortaleza, Caucaia, Sobral, Maracanaú e
   Quixadá contra a fonte aceita para a revisão.
1. Repetir a auditoria se a ficha migrar para uma nova estrutura do e-SUS SINAN.

A reconciliação técnica estará resolvida somente quando os totais oficiais forem
reproduzidos ou quando a diferença residual estiver explicada, versionada e
aceita como evidência suficiente. Se isso não for possível, existem duas opções:
registrar a decisão geral como **inconclusiva**, mantendo a CAP-03 aberta, ou
**reprovar** o uso dos campos públicos e concluir a CAP-03 com o indicador fora
do produto. O revisor não precisa resolver problemas de banco ou programação.

### Quem precisa participar da decisão

| Responsabilidade | Participação esperada |
| --- | --- |
| Reconciliação dos arquivos e do TabWin | Equipe de dados, preferencialmente com operador do SINAN ou TabWin |
| Semântica dos campos e validade epidemiológica | Profissional do programa de TB, vigilância ou epidemiologia com experiência no SINAN |
| Utilidade municipal e compreensão do fluxo | Usuários da vigilância municipal ou estadual |
| Inclusão, alteração ou exclusão do produto | Responsáveis de produto e governança, apoiados pelo parecer epidemiológico |

Um médico pode participar, mas a revisão da CAP-03 não deve depender apenas de
formação clínica. Conhecimento de vigilância da tuberculose, preenchimento do
SINAN e tabulação dos indicadores é essencial para avaliar os campos e a coorte.

## Decisões de domínio necessárias para a CAP-03

1. **D03-01 - Universo, município e período:** confirmar o uso de `NU_ANO`, do
   município de residência `ID_MN_RESI`, dos tipos de entrada `1`, `4` e `6` e
   da exclusão de mudança de diagnóstico no encerramento.
1. **D03-02 - Formas clínicas:** confirmar a inclusão das formas pulmonar e
   pulmonar mais extrapulmonar, códigos `1` e `3`.
1. **D03-03 - Confirmação laboratorial:** confirmar a inclusão de baciloscopia
   inicial positiva, segunda baciloscopia positiva, cultura positiva e TRM-TB
   detectável, especialmente a interpretação da segunda baciloscopia.
1. **D03-04 - Campos de contatos:** confirmar se `NU_CONTATO` representa
   contatos identificados e `NU_COMU_EX` representa contatos examinados em todo
   o período analisado.
1. **D03-05 - Campos vazios:** decidir se vazio significa zero, informação
   desconhecida, ausência de preenchimento ou outra situação. Também escolher
   entre valores registrados, pares completos ou indisponibilidade do resultado.
1. **D03-06 - Duplicidades, atualizações e transferências:** definir se esses
   eventos alteram as contagens e como devem ser identificados ou tratados.
1. **D03-07 - Maturidade da coorte:** definir quanto tempo deve transcorrer para
   considerar um ano completo e qual atraso deve ser comunicado no produto.
1. **D03-08 - Examinados acima de identificados:** escolher entre resultado
   inconclusivo, exclusão, correção na fonte ou outra conduta explícita. O
   sistema não corrigirá nem limitará automaticamente a proporção a 100%.
1. **D03-09 - Pequenos denominadores:** definir denominador mínimo, supressão,
   agregação de anos ou outra proteção para pequenas contagens.
1. **D03-10 - Nível geográfico:** decidir se a proporção é interpretável por
   município ou somente em regiões, estados ou outros agregados.
1. **D03-11 - Referência ou limiar:** confirmar se existe referência oficial
   adequada e como ela pode ser usada. O sistema não deve transformar uma meta
   em regra comparativa por conta própria.
1. **D03-12 - Priorização e resposta:** somente se o indicador for aceito,
   definir gravidade, dimensão do ranking, peso e resposta municipal sugerida.
1. **D03-13 - Linguagem de segurança:** revisar o texto para que o sinal não
   pareça diagnóstico, punição, avaliação individual de serviço ou prova de
   baixa qualidade.
1. **D03-14 - Divergências oficiais:** decidir se uma diferença tecnicamente
   explicada em relação às publicações ainda impede o uso do indicador.
1. **D03-15 - Compreensão pelos usuários:** pedir que usuários da vigilância
   expliquem o resultado e suas limitações com as próprias palavras antes de
   aprovar a apresentação.

D03-01 a D03-10 e D03-14 são essenciais para qualquer cálculo público. D03-11 e
D03-12 são necessárias se o resultado produzir limiar, alerta, pontos ou
recomendação. D03-13 e D03-15 devem ser concluídas antes de apresentar o
indicador aos usuários.

## Roteiro sugerido para a revisão da CAP-03

1. Ler “Qual pergunta está sendo investigada” e confirmar a separação do alerta
   municipal sintético.
1. Conferir o universo candidato e as quatro formas de confirmação
   laboratorial.
1. Comparar “valores registrados” com “pares completos” e decidir como tratar
   campos vazios.
1. Analisar as duas divergências com publicações oficiais e registrar se a
   evidência técnica é suficiente.
1. Conferir Fortaleza, Caucaia, Sobral, Maracanaú e Quixadá diretamente em uma
   fonte aceita pelo revisor.
1. Definir maturidade da coorte, denominador mínimo e comportamento de
   resultados impossíveis.
1. Discutir eventual utilidade municipal antes de considerar limiar ou ranking.
1. Preencher e assinar o registro abaixo.

## Registro de decisão da CAP-03

| ID | Decisão | Aprovar | Alterar | Reprovar | Inconclusivo | Observações |
| --- | --- | :---: | :---: | :---: | :---: | --- |
| D03-01 | Universo, município e período | [ ] | [ ] | [ ] | [ ] | |
| D03-02 | Formas pulmonar e mista | [ ] | [ ] | [ ] | [ ] | |
| D03-03 | Confirmação laboratorial e segunda baciloscopia | [ ] | [ ] | [ ] | [ ] | |
| D03-04 | Significado dos dois campos de contatos | [ ] | [ ] | [ ] | [ ] | |
| D03-05 | Tratamento de campo vazio | [ ] | [ ] | [ ] | [ ] | |
| D03-06 | Duplicidades, atualizações e transferências | [ ] | [ ] | [ ] | [ ] | |
| D03-07 | Maturidade e atraso da coorte | [ ] | [ ] | [ ] | [ ] | |
| D03-08 | Examinados acima de identificados | [ ] | [ ] | [ ] | [ ] | |
| D03-09 | Denominador mínimo, supressão e agregação | [ ] | [ ] | [ ] | [ ] | |
| D03-10 | Interpretação no nível municipal | [ ] | [ ] | [ ] | [ ] | |
| D03-11 | Referência ou limiar oficial | [ ] | [ ] | [ ] | [ ] | |
| D03-12 | Gravidade, ranking e resposta sugerida | [ ] | [ ] | [ ] | [ ] | |
| D03-13 | Linguagem de segurança | [ ] | [ ] | [ ] | [ ] | |
| D03-14 | Divergências com as publicações | [ ] | [ ] | [ ] | [ ] | |
| D03-15 | Compreensão do fluxo por usuários | [ ] | [ ] | [ ] | [ ] | |

**Situação da reconciliação técnica:** [ ] totais oficiais reproduzidos [ ]
diferença residual explicada e aceita [ ] não reconciliada

**Fonte congelada ou exportação TabWin utilizada:**

**Responsável pela reconciliação e data:**

**Leitura escolhida para campos incompletos:**

**Situações que tornam o resultado inconclusivo:**

**Coorte mínima considerada madura:**

**Denominador mínimo e justificativa:**

**Nível geográfico aprovado:**

**Uso aprovado:** [ ] somente indicador descritivo [ ] limiar, alerta ou ranking
[ ] fora do produto público

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

### Efeito da decisão geral

- **Aprovar:** permite implementar o cálculo somente após a reconciliação
  técnica e a aprovação de D03-01 a D03-10 e D03-14. Limiar, alerta, ranking ou
  recomendação também exigem D03-11 a D03-13. A apresentação aos usuários exige
  D03-13 e D03-15.
- **Aprovar com alterações:** mantém a CAP-03 aberta até que as alterações sejam
  implementadas, testadas, auditadas e submetidas a nova revisão.
- **Reprovar:** conclui a CAP-03 com decisão documentada de manter o indicador
  fora do produto público. O alerta municipal sintético de contato pendente
  continua sendo um fluxo operacional separado.
- **Inconclusivo:** mantém a CAP-03 aberta e impede indicador, cenário, pontos no
  ranking ou apresentação no produto até que a evidência ausente seja obtida.

A CAP-03 não pode gerar indicador, cenário ou pontos no ranking enquanto a
reconciliação técnica estiver aberta. Uma aprovação profissional não substitui
a reconciliação dos arquivos, e a equipe técnica não pode aprovar sozinha a
semântica ou a utilidade epidemiológica.

## CAP-04 em linguagem simples

### Duas camadas que não devem ser confundidas

A CAP-04 responde a duas perguntas diferentes. A primeira é territorial:
"os dados públicos mostram uma possível lacuna de vigilância que merece revisão
do programa?". A segunda é operacional: "há uma evidência ou pendência registrada
para este caso sintético que uma equipe deveria revisar?". Nenhuma das duas
perguntas equivale a diagnosticar resistência.

| Camada | Unidade observada | Fonte atual | O que apresenta | O que não apresenta |
| --- | --- | --- | --- | --- |
| Territorial pública | Município e ano | SINAN-TB público agregado | Retratamento elevado, baixo uso de cultura no retratamento e baixo uso de TRM-TB | Casos confirmados ou carga municipal de resistência |
| Operacional | Caso sintético pseudonimizado | Arquivos municipais de demonstração | Evidência explícita registrada, histórico de risco e lacuna de cultura ou teste de sensibilidade | Diagnóstico produzido pelo sistema ou autorização para usar dados reais |

O perfil territorial é apenas descritivo e não cria nem recalcula pontos. Ele
reutiliza três regras transparentes já existentes; exibi-las na CAP-04 não
acrescenta uma nova contribuição ao ranking. Eventual pontuação das regras
originais continua regida pela configuração e validação próprias de cada
cenário. Resultado ausente, suprimido ou sem grupo suficiente para comparação
não é tratado como alerta.

A fila operacional atual usa somente dados sintéticos. Ela não mostra o
pseudônimo da pessoa e não cria mapa de casos. Uma eventual integração real
precisa de fonte autorizada e dos controles de GOV-01 antes de qualquer teste
com dados pessoais.

### Como os sinais operacionais foram separados

Um alerta de vigilância de resistência pode reunir três classes de informação:

1. **Evidência explícita registrada:** um registro separado informa
   "resistance_status=confirmed" e "record_status=final". Na implementação
   atual, a origem permitida é somente "synthetic_demo". O sistema apenas
   reproduz a classificação declarada pelo registro; ele não interpreta um
   laudo para produzir um diagnóstico.
1. **Histórico de risco não verificado:** retratamento, falha prévia de tratamento
   ou o antigo campo de resistência à rifampicina. Esses elementos pedem revisão,
   mas nunca são apresentados como confirmação.
1. **Lacuna de vigilância:** caso de retratamento pulmonar sem evento concluído
   de cultura ou teste de sensibilidade registrado. A regra técnica atual exige
   data de resultado, situação concluída e um tipo de exame reconhecido como
   cultura, DST, sensibilidade ou suscetibilidade.

Se o mesmo caso tiver mais de um desses elementos, o sistema gera um único
alerta e mostra todas as evidências separadamente. Todos os alertas dessa classe
recebem gravidade alta e ficam marcados como pendentes de revisão de domínio.
A adequação dessa gravidade, da definição de exame concluído e da ação esperada
ainda não foi aprovada por especialista.

### Evidência técnica já disponível para a CAP-04

A auditoria do Ceará em 2023 cobriu os 184 municípios:

| Sinal público | Disponíveis | Suprimidos | Ausentes | Comparação | Municípios destacados |
| --- | ---: | ---: | ---: | --- | ---: |
| Retratamento elevado | 18 | 155 | 11 | Pronta | 5 |
| Baixo uso de cultura no retratamento | 6 | 167 | 11 | Insuficiente | 0 |
| Baixo uso de TRM-TB | 19 | 154 | 11 | Pronta | 5 |

Foram nove municípios distintos com pelo menos um sinal e um município com dois
sinais simultâneos. As 43 ocorrências com valor disponível tinham proveniência
SINAN-TB; nenhuma estava sem fonte. A auditoria encontrou zero violação
estrutural, zero perfil declarando efeito próprio no ranking e zero perfil
alegando resistência confirmada em fonte pública.

O relatório fica marcado como
"technical_validation_pending_domain_review". Isso significa que o software
reproduziu os dados e respeitou as salvaguardas programadas. Não significa que
a interpretação, o limiar, a gravidade ou a conduta foram aprovados.

Na demonstração operacional, as validações técnicas também garantem que:

- o caso citado existe no mesmo ano e o pseudônimo coincide com o cadastro
  sintético;
- valores fora das listas permitidas são rejeitados;
- registro preliminar, cancelado, indeterminado ou não confirmado não produz
  sozinho um sinal de confirmação;
- a fila e a API informam a classe e a proveniência da evidência sem devolver o
  pseudônimo;
- vários sinais do mesmo caso permanecem em um único alerta auditável.

Essas verificações demonstram consistência do contrato, não validade clínica.

### Quem precisa participar da decisão

| Responsabilidade | Participação esperada |
| --- | --- |
| Significado epidemiológico dos sinais públicos | Profissional do programa de TB, vigilância ou epidemiologia |
| Interpretação de cultura, teste de sensibilidade e evidência explícita | Médico ou profissional de referência em TB resistente e laboratório |
| Utilidade e ação na fila municipal | Profissionais da vigilância municipal, APS e coordenação do programa |
| Fonte real, finalidade, acesso, retenção e auditoria | Governança institucional, LGPD e segurança da informação |
| Linguagem e compreensão do produto | Usuários representativos das camadas territorial e operacional |

A equipe técnica deve demonstrar as regras e registrar as respostas, mas não
pode decidir sozinha nenhum desses itens.

## Decisões de domínio e governança necessárias para a CAP-04

1. **D04-01 - Evidência explícita:** confirmar se um registro final marcado como
   confirmado é suficiente para ser exibido como evidência explícita e quais
   tipos de documento, exames e sistemas de origem podem declarar essa condição.
1. **D04-02 - Histórico de risco:** decidir se retratamento, falha prévia e o
   campo legado de resistência à rifampicina pertencem à mesma classe de
   vigilância. Confirmar que nenhum deles deve ser chamado de resistência
   confirmada sem outra evidência.
1. **D04-03 - Cultura ou teste de sensibilidade concluído:** definir quais exames,
   resultados, situações e prazos contam como evidência concluída e se a lacuna
   deve se aplicar a todo retratamento pulmonar.
1. **D04-04 - Agrupamento por caso:** confirmar se um único alerta deve reunir
   todas as classes de sinal ou se alguma situação exige alertas, responsáveis
   ou prioridades separados.
1. **D04-05 - Gravidade e resposta:** revisar a gravidade alta, definir quem
   revisa o alerta, em qual prazo e qual ação é esperada para cada combinação de
   sinais. A resposta não pode ser uma prescrição automática.
1. **D04-06 - Perfil territorial público:** confirmar se retratamento elevado,
   baixo uso de cultura e baixo uso de TRM-TB são úteis como lacunas ou sinais
   indiretos de vigilância, sem apresentá-los como carga de resistência.
1. **D04-07 - Comparação e ranking:** revisar os grupos de comparação,
   cobertura e percentis, distinguindo a contribuição de cenários já existentes
   da apresentação criada pela CAP-04. Decidir se o perfil deve continuar
   descritivo e se as regras subjacentes permanecem adequadas. A configuração
   atual do perfil não acrescenta uma nova contribuição ao ranking.
1. **D04-08 - Linguagem de segurança:** revisar rótulos, explicações,
   recomendações e a distinção visual entre evidência explícita, histórico de
   risco, lacuna de vigilância e dado público agregado.
1. **D04-09 - Governança de dados reais:** antes de qualquer integração real,
   registrar fonte, finalidade, fundamento jurídico, autorização institucional,
   minimização, pseudonimização, perfis de acesso, retenção, trilha de auditoria,
   resposta a incidentes e responsabilidade pelo tratamento.
1. **D04-10 - Compreensão pelos usuários:** pedir que usuários das duas camadas
   expliquem com as próprias palavras o significado de cada sinal, o que devem
   fazer e o que o sistema não permite concluir.

D04-01 a D04-08 e D04-10 são essenciais para retirar o estado provisório dos
fluxos demonstrados. D04-09 e a entrega GOV-01 são obrigatórias antes de usar
qualquer dado municipal real. Uma decisão de manter os sinais públicos fora do
ranking também é válida, desde que seja registrada.

## Roteiro sugerido para a revisão da CAP-04

1. Ler "Duas camadas que não devem ser confundidas" e pedir aos revisores que
   expliquem a diferença entre lacuna pública e evidência operacional.
1. Abrir o perfil de um município com sinal, outro sem sinal e um resultado
   suprimido ou ausente.
1. Confirmar que nenhum elemento territorial parece estimar casos confirmados de
   resistência ou alterar o ranking.
1. Conferir a tabela CE/2023 e discutir a baixa disponibilidade dos três sinais,
   especialmente cultura no retratamento.
1. Abrir na fila sintética um exemplo de cada classe e um caso com classes
   combinadas.
1. Revisar quais registros podem ser chamados de evidência explícita e o que
   caracteriza cultura ou teste de sensibilidade concluído.
1. Definir gravidade, responsável, prazo e ação esperada sem automatizar
   diagnóstico ou prescrição.
1. Realizar o teste de compreensão com usuários e registrar dúvidas ou
   interpretações indevidas.
1. Se houver proposta de fonte real, submeter também a lista de GOV-01 aos
   responsáveis institucionais.
1. Preencher e assinar o registro abaixo.

## Registro de decisão da CAP-04

| ID | Decisão | Aprovar | Alterar | Reprovar | Inconclusivo | Observações |
| --- | --- | :---: | :---: | :---: | :---: | --- |
| D04-01 | Evidência explícita e fontes aceitas | [ ] | [ ] | [ ] | [ ] | |
| D04-02 | Histórico de risco não confirmado | [ ] | [ ] | [ ] | [ ] | |
| D04-03 | Cultura ou teste de sensibilidade concluído | [ ] | [ ] | [ ] | [ ] | |
| D04-04 | Um alerta por caso e agrupamento dos sinais | [ ] | [ ] | [ ] | [ ] | |
| D04-05 | Gravidade, responsável, prazo e ação | [ ] | [ ] | [ ] | [ ] | |
| D04-06 | Utilidade dos três sinais públicos | [ ] | [ ] | [ ] | [ ] | |
| D04-07 | Comparação e ausência de contribuição adicional do perfil | [ ] | [ ] | [ ] | [ ] | |
| D04-08 | Linguagem e distinção entre as classes | [ ] | [ ] | [ ] | [ ] | |
| D04-09 | Governança para dados municipais reais | [ ] | [ ] | [ ] | [ ] | |
| D04-10 | Compreensão do fluxo por usuários | [ ] | [ ] | [ ] | [ ] | |

**Uso territorial aprovado:** [ ] descritivo e sem ranking [ ] com alteração
documentada [ ] fora do produto

**Uso operacional aprovado:** [ ] demonstração sintética [ ] piloto autorizado
após GOV-01 [ ] fora do produto

**Fontes e tipos de evidência explícita aceitos:**

**Definição aprovada de cultura ou teste de sensibilidade concluído:**

**Responsável, prazo e ação esperada para o alerta:**

**Fonte municipal real avaliada, se houver:**

**Finalidade, autorização institucional e fundamento jurídico:**

**Perfis de acesso, retenção e trilha de auditoria:**

**Decisão geral:** [ ] aprovar [ ] aprovar com alterações [ ] reprovar [ ]
inconclusivo

**Alterações obrigatórias antes da aprovação:**

______________________________________________________________________

**Nome do revisor de domínio responsável:**

**Formação e função:**

**Instituição:**

**Nome do responsável por governança, quando aplicável:**

**Data:**

**Versão ou identificação das fontes consultadas:**

**Assinatura ou registro equivalente:**

### Efeito da decisão geral da CAP-04

- **Aprovar:** permite retirar o estado provisório somente dentro do uso e das
  fontes registrados. Dados municipais reais continuam proibidos sem D04-09 e
  GOV-01 aprovados.
- **Aprovar com alterações:** mantém a CAP-04 em validação até que as mudanças
  sejam implementadas, testadas e submetidas a nova revisão.
- **Reprovar:** retira do produto o sinal ou fluxo reprovado. Isso não autoriza
  substituí-lo por uma inferência ou fonte não avaliada.
- **Inconclusivo:** mantém os sinais provisórios, sem nova contribuição ao
  ranking e limitados à demonstração sintética até obter a evidência ausente.

A CAP-04 só pode ser marcada como concluída quando as decisões essenciais
estiverem registradas, as alterações solicitadas passarem pelos gates técnicos
e o teste de compreensão estiver documentado. Uma auditoria com zero violações
não substitui revisão epidemiológica, validação de fluxo ou autorização de
governança.

## Onde encontrar a evidência

A equipe técnica pode apresentar os seguintes artefatos sem exigir que o revisor
os edite.

### Evidência da CAP-01

- Amostra municipal:
  `src/tbia/resources/validation/sinan_diagnostic_acceptance_ce_2023.json`.
- Auditoria dos campos SINAN-TB:
  `data/processed/mvp1/validation/sinan_mapping_ce_2023.json`.
- Validação matemática dos indicadores:
  `data/processed/mvp1/validation/indicator_validation_ce_2023.json`.
- Comparação do ranking:
  `data/processed/mvp1/validation/diagnostic_ranking_impact_ce_2023.json`.

### Evidência da CAP-02

- Agregado municipal anual:
  `src/tbia/resources/demo/incidence_history_ce_2018_2023.json`.
- Manifesto com fontes, datas e identificadores criptográficos:
  `src/tbia/resources/demo/incidence_history_ce_2018_2023.manifest.json`.
- Auditoria de comparabilidade:
  `data/processed/mvp1/validation/incidence_history_comparability_ce_2018_2023.json`,
  gerada por `python -m tbia validate-incidence-history`.
- Série de um município, disponível na API
  `/api/territorial/history` com município, indicador e intervalo informados.

### Evidência da CAP-03

- Manifesto, hashes, benchmarks e cinco municípios:
  `src/tbia/resources/validation/sinan_contact_audit_ce_2018_2024.json`.
- Auditoria técnica gerada localmente:
  `data/processed/mvp1/validation/sinan_contact_investigation_ce_2018_2024.json`.
- Comando reproduzível:
  `python -m tbia validate-sinan-contacts --uf CE --year-from 2018 --year-to 2024`.

Enquanto houver divergência, o comando grava o relatório e retorna código `1`.
Esse código documenta um bloqueio esperado e não significa que o relatório foi
perdido.

### Evidência da CAP-04

- Auditoria territorial gerada localmente:
  `data/processed/mvp1/validation/resistance_surveillance_audit_ce_2023.json`.
- Comando reproduzível:
  `python -m tbia validate-resistance-surveillance --uf CE --year 2023`.
- Contrato e limites da demonstração operacional:
  `mvp2_municipal_contracts.md`.
- Perfil territorial para revisão em `/territorios` e fila sintética em
  `/acompanhamento`, após executar `make demo` e iniciar o servidor.

O comando retorna sucesso quando as salvaguardas estruturais passam, mas mantém
o estado `technical_validation_pending_domain_review`. O arquivo registra
disponibilidade, comparação, sobreposição, proveniência e as proteções contra
efeito no ranking ou alegação pública de resistência confirmada.

A interface de demonstração fica em `/territorios`, após executar `make demo`
e iniciar o servidor. Os arquivos gerados em `data/processed/` são evidência
reproduzível local e não são versionados no Git. Os identificadores
criptográficos dos arquivos de origem ficam registrados nos artefatos
versionados de cada capacidade.
