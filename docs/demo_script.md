# Roteiro de Demonstracao

Tempo alvo: 4 a 6 minutos.

## 1. Abertura

"O TB-IA e um MVP para apoiar equipes de APS na organizacao territorial do cuidado em tuberculose. Ele nao diagnostica e nao substitui profissionais. O foco e transformar sinais operacionais simples em uma fila explicavel de trabalho."

## 2. Contexto do problema

Mostrar que sintomas respiratorios, contatos, vulnerabilidades e barreiras de adesao chegam por canais diferentes. A equipe precisa decidir o que acompanhar primeiro.

## 3. Carregar dados sinteticos

Executar:

```bash
python scripts/seed_synthetic.py --api http://127.0.0.1:8000
```

Ou chamar `POST /seed/synthetic` no Swagger.

## 4. Mostrar fila priorizada

Abrir `GET /alerts`. Destacar:

- prioridade;
- territorio e microarea;
- categoria do alerta;
- explicacao em linguagem simples;
- acao operacional sugerida;
- status pendente de validacao humana.

## 5. Validar alerta

Usar `POST /alerts/{alert_id}/validation`:

```json
{
  "decision": "validated",
  "validated_by": "enfermeira_demo",
  "note": "Alerta coerente com visita planejada pela equipe."
}
```

## 6. Registrar acao

Usar `POST /alerts/{alert_id}/actions`:

```json
{
  "action_type": "home_visit_scheduled",
  "performed_by": "acs_demo",
  "note": "Visita domiciliar sintetica agendada para investigacao operacional."
}
```

## 7. Mostrar dashboard

Abrir `GET /dashboard/territories`. Explicar como a equipe e a gestao visualizam carga de alertas por territorio, prioridade e status.

## 8. Fechamento

"A entrega demonstra um caminho tecnicamente simples e eticamente defensavel: dados sinteticos, regras auditaveis, validacao humana obrigatoria e foco em processo de trabalho da APS."

