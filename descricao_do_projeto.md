# Descrição do projeto

## Visão geral

O projeto propõe uma plataforma inteligente de apoio à gestão da tuberculose na atenção primária e na vigilância municipal. O objetivo é ajudar equipes de saúde a identificar áreas prioritárias, evitar oportunidades perdidas de rastreamento, acompanhar pacientes de maior risco e selecionar estratégias de controle mais adequadas à realidade local.

A solução busca transformar dados já existentes nos serviços de saúde em decisões operacionais mais rápidas, territoriais e baseadas em evidências. Ela deve apoiar gestores e equipes da atenção primária na escolha das estratégias mais efetivas, viáveis e custo-efetivas para avançar no controle e na eliminação da tuberculose como problema de saúde pública.

## Objetivo principal

A plataforma tem como objetivo apoiar a tomada de decisão em saúde pública, sem substituir a avaliação profissional. Ela deve funcionar como uma camada de inteligência operacional para:

- Identificar territórios prioritários.
- Detectar zonas quentes de transmissão.
- Apontar falhas assistenciais ou operacionais.
- Sinalizar oportunidades perdidas de rastreamento.
- Priorizar pacientes, contatos e áreas com maior risco.
- Apoiar estratégias de adesão ao tratamento.
- Monitorar sinais relacionados à tuberculose resistente.

## Usuários previstos

A solução é voltada principalmente para equipes da atenção primária e da vigilância municipal, incluindo:

- Agentes comunitários de saúde.
- Enfermeiros.
- Médicos.
- Equipes de vigilância epidemiológica.
- Gestores municipais.
- Coordenações de atenção primária.
- Coordenações de programas de tuberculose.

O sistema deve reduzir trabalho manual sempre que possível, funcionando como suporte à rotina existente e não como uma obrigação adicional pesada para os profissionais.

## Classificação territorial e cenários

A plataforma utiliza inteligência artificial combinada com regras epidemiológicas e diretrizes públicas para classificar territórios em cenários e subcenários adaptativos. Essa lógica é inspirada no Plano Nacional pelo Fim da Tuberculose como Problema de Saúde Pública.

Os subcenários podem ser atualizados conforme novos dados surgem. Exemplos de situações que a plataforma deve identificar:

- Alta incidência de tuberculose.
- Baixa confirmação laboratorial.
- Baixa investigação de contatos.
- Maior abandono ou interrupção do tratamento.
- Baixa testagem para HIV.
- Baixa cobertura de tratamento preventivo.
- Sinais de alerta para tuberculose resistente.
- Concentração territorial de casos.
- Indícios de falhas assistenciais.

## Ações orientadas pelo sistema

A partir da identificação de áreas ou grupos prioritários, a plataforma pode orientar ações ativas, como:

- Busca de sintomáticos respiratórios.
- Investigação de contatos de casos pulmonares.
- Fortalecimento da coleta de escarro.
- Encaminhamento para teste rápido molecular.
- Acompanhamento de populações vulneráveis.
- Estratégias de adesão ao tratamento.
- Visitas domiciliares.
- Tratamento diretamente observado.
- Avaliação de barreiras sociais.
- Encaminhamento para assistência social.
- Monitoramento mais frequente pela equipe de saúde.

Essas recomendações devem ser apresentadas como apoio operacional e não como prescrição automática.

## Triagem assistida por IA

Um componente central do projeto é o fluxo de triagem assistida por IA voltado para a atenção primária. A partir de dados clínicos, territoriais e operacionais, o sistema ajuda as equipes a identificar pessoas ou grupos com maior risco de tuberculose ativa.

O fluxo pode priorizar:

- Pacientes com sintomas respiratórios persistentes.
- Contatos de casos pulmonares.
- Pessoas vivendo com HIV.
- Pessoas em situação de vulnerabilidade social.
- Pacientes com histórico prévio de tuberculose.
- Pessoas em territórios com alta transmissão.
- Pacientes com registros incompletos ou sem confirmação laboratorial.

O objetivo é reduzir casos não diagnosticados e evitar oportunidades perdidas de rastreamento.

## Acompanhamento de pacientes diagnosticados

Para pacientes já diagnosticados, a plataforma estima o risco de interrupção do tratamento. Isso permite que a equipe acompanhe mais de perto aqueles com maior probabilidade de abandono.

O sistema pode sugerir estratégias de cuidado conforme o risco identificado, como:

- Visitas domiciliares.
- Lembretes e busca ativa.
- Tratamento diretamente observado.
- Avaliação de barreiras sociais.
- Encaminhamento à assistência social.
- Monitoramento mais frequente.
- Priorização em reuniões de equipe.

## Vigilância para tuberculose resistente

A solução também inclui uma camada de vigilância para tuberculose resistente. Essa frente deve monitorar sinais operacionais e clínicos que indiquem necessidade de maior atenção ou encaminhamento para fluxos especializados.

Indicadores e sinais relevantes:

- Retratamento.
- Falha terapêutica.
- Ausência de cultura quando indicada.
- Ausência de teste de sensibilidade quando indicado.
- Resistência à rifampicina.
- Histórico de tratamento prévio.
- Necessidade de encaminhamento para serviço de referência.

## Indicadores operacionais

A plataforma deve apresentar indicadores alinhados ao Plano Nacional pelo Fim da Tuberculose e à Estratégia Global pelo Fim da Tuberculose.

Indicadores previstos:

- Incidência.
- Mortalidade.
- Cura.
- Interrupção do tratamento.
- Confirmação laboratorial.
- Testagem para HIV.
- Investigação de contatos.
- Cobertura de tratamento preventivo.
- Uso de testes diagnósticos.
- Acompanhamento de casos de tuberculose resistente.
- Distribuição territorial dos casos.
- Populações vulneráveis acompanhadas.

## Fontes de dados

A proposta inicial considera o uso de bases já existentes, evitando ao máximo que os profissionais precisem alimentar manualmente o sistema.

Fontes possíveis:

- DATASUS.
- SINAN.
- Dados oficiais de vigilância municipal.
- Dados públicos agregados.
- Prontuários eletrônicos locais da atenção primária.
- Registros da farmácia municipal.
- Cadastro territorial da UBS.
- Dados simulados para prototipagem e demonstração.

## Limitação prática sobre prontuários e e-SUS APS

O diálogo com o mentor destacou uma limitação importante: o acesso direto a dados de prontuário do e-SUS APS não é simples. Mesmo em instalações locais, parte dos dados clínicos pode estar criptografada ou indisponível fora do próprio sistema.

Isso significa que a proposta não deve depender, no MVP, de acesso completo e automático aos prontuários clínicos do e-SUS APS. O uso de dados microassistenciais deve ser tratado como uma camada futura ou condicional, possível apenas quando houver integração local, autorização institucional, acesso técnico adequado e governança compatível com a LGPD.

## Premissa realista para o MVP

A forma mais realista de estruturar o projeto inicialmente é considerar que o sistema funciona com bases públicas, dados oficiais de vigilância e dados agregados disponíveis. A camada microassistencial pode ser adicionada quando a solução for instalada ou integrada ao ambiente local da gestão municipal.

Assim, o MVP deve priorizar:

- Análise territorial com dados públicos e oficiais.
- Painéis de indicadores operacionais.
- Classificação de territórios em cenários e subcenários.
- Regras epidemiológicas transparentes.
- Simulação de dados microassistenciais quando necessário.
- Entrada manual mínima apenas para campos indispensáveis.
- Demonstração de valor sem depender de integração complexa com prontuário.

## Integração local futura

Em uma etapa posterior, a plataforma pode ganhar uma camada microassistencial integrada ao ambiente municipal. Essa etapa pode incluir:

- Instalação local no servidor da gestão municipal.
- Integração com prontuário eletrônico local, quando tecnicamente possível.
- Uso de registros da farmácia municipal.
- Uso de cadastros territoriais da UBS.
- Integração com fluxos internos da vigilância.
- Importação autorizada de dados identificáveis ou pseudonimizados.

Essa fase exige parceria institucional, segurança da informação, definição de responsabilidades e conformidade com a LGPD.

## LGPD, segurança e governança

Por se tratar de um projeto de saúde, a plataforma deve operar com limites claros:

- Não diagnosticar automaticamente.
- Não prescrever condutas.
- Não substituir a decisão profissional.
- Não expor dados sensíveis sem necessidade.
- Usar dados agregados ou pseudonimizados sempre que possível.
- Registrar ações e decisões relevantes.
- Manter validação humana nos alertas e recomendações.
- Definir perfis de acesso por função.
- Garantir rastreabilidade e governança sobre os dados.

O sistema deve ser apresentado como apoio à decisão e à gestão, não como ferramenta autônoma de diagnóstico ou tratamento.

## Valor esperado

O valor central do projeto está em organizar dados dispersos e transformá-los em priorização prática para o serviço de saúde. A plataforma deve ajudar o município a responder perguntas como:

- Onde a tuberculose está mais concentrada?
- Onde há possível subdiagnóstico?
- Onde a confirmação laboratorial está baixa?
- Quais territórios precisam de busca ativa?
- Quais pacientes têm maior risco de abandono?
- Quais contatos precisam ser investigados?
- Onde há alerta para tuberculose resistente?
- Quais estratégias são mais adequadas para cada cenário local?

## Síntese da proposta

O projeto é uma plataforma de inteligência territorial e assistencial para tuberculose. Ele combina dados públicos, dados de vigilância, regras epidemiológicas e inteligência artificial para apoiar decisões na atenção primária e na gestão municipal.

Inicialmente, o sistema deve funcionar com bases públicas e oficiais, evitando dependência de integrações difíceis com prontuários. Futuramente, pode incorporar dados microassistenciais quando houver instalação local ou integração autorizada com sistemas municipais.

A proposta é aplicável porque não exige, em sua versão inicial, grande carga extra de trabalho dos profissionais. Seu papel é apoiar a tomada de decisão, priorizar ações e orientar estratégias mais efetivas para o controle da tuberculose.
