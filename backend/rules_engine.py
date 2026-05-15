from backend.schemas import AlertCategory, Priority, Questionnaire, RuleEvaluation


KNOWN_BARRIERS = {
    "transport": ("Barreira de transporte relatada", 10),
    "food_insecurity": ("Inseguranca alimentar relatada", 10),
    "stigma": ("Estigma ou medo de exposicao relatado", 10),
    "side_effects": ("Efeitos adversos relatados como barreira", 15),
}

KNOWN_VULNERABILITIES = {
    "hiv",
    "diabetes",
    "homelessness",
    "deprivation",
    "substance_use",
    "previous_tb",
}


def priority_from_score(score: int) -> Priority:
    if score >= 90:
        return Priority.critical
    if score >= 60:
        return Priority.high
    if score >= 30:
        return Priority.moderate
    return Priority.low


def evaluate_questionnaire(questionnaire: Questionnaire) -> RuleEvaluation:
    score = 0
    rationale: list[str] = []
    categories: set[AlertCategory] = set()

    symptoms = questionnaire.symptoms
    if symptoms.cough_weeks >= 2:
        score += 30
        rationale.append("Tosse por 2 semanas ou mais")
        categories.add(AlertCategory.respiratory_symptom_screening)
    if symptoms.fever:
        score += 15
        rationale.append("Febre relatada")
        categories.add(AlertCategory.respiratory_symptom_screening)
    if symptoms.night_sweats:
        score += 15
        rationale.append("Sudorese noturna relatada")
        categories.add(AlertCategory.respiratory_symptom_screening)
    if symptoms.weight_loss:
        score += 15
        rationale.append("Perda de peso relatada")
        categories.add(AlertCategory.respiratory_symptom_screening)

    contact = questionnaire.contact
    if contact.known_tb_contact:
        score += 30
        rationale.append("Contato conhecido com caso de tuberculose")
        categories.add(AlertCategory.contact_investigation)
    if contact.household_contact:
        score += 20
        rationale.append("Contato domiciliar informado")
        categories.add(AlertCategory.contact_investigation)
    if contact.known_tb_contact and not contact.contact_investigated:
        rationale.append("Contato ainda sem investigacao registrada no MVP")
        categories.add(AlertCategory.contact_investigation)

    adherence = questionnaire.adherence
    if adherence.on_treatment:
        categories.add(AlertCategory.adherence_support)
    if adherence.missed_recent_appointments:
        score += 25
        rationale.append("Faltas recentes em acompanhamento/tratamento")
        categories.add(AlertCategory.adherence_support)
    if adherence.treatment_interruption:
        score += 30
        rationale.append("Interrupcao de tratamento relatada")
        categories.add(AlertCategory.adherence_support)
    if adherence.side_effects_reported:
        score += 15
        rationale.append("Efeitos adversos relatados")
        categories.add(AlertCategory.adherence_support)

    normalized_barriers = {item.strip().lower() for item in questionnaire.barriers}
    for barrier, (reason, points) in KNOWN_BARRIERS.items():
        if barrier in normalized_barriers:
            score += points
            rationale.append(reason)
            categories.add(AlertCategory.adherence_support)

    normalized_vulnerabilities = {
        item.strip().lower() for item in questionnaire.vulnerabilities
    }
    vulnerability_hits = sorted(normalized_vulnerabilities & KNOWN_VULNERABILITIES)
    if vulnerability_hits:
        added = min(len(vulnerability_hits) * 15, 45)
        score += added
        rationale.append(
            "Vulnerabilidades sinteticas relevantes: " + ", ".join(vulnerability_hits)
        )
        categories.add(AlertCategory.territorial_vulnerability)

    if not categories:
        categories.add(AlertCategory.respiratory_symptom_screening)
        rationale.append("Sem criterios de maior prioridade; manter monitoramento de rotina")

    return RuleEvaluation(
        score=score,
        priority=priority_from_score(score),
        categories=sorted(categories, key=lambda item: item.value),
        rationale=rationale,
        recommended_actions=recommended_actions_for(categories),
    )


def recommended_actions_for(
    categories: set[AlertCategory],
) -> dict[AlertCategory, str]:
    actions = {
        AlertCategory.respiratory_symptom_screening: (
            "Revisar registro com profissional da APS e seguir protocolo local para "
            "avaliacao de sintomatico respiratorio."
        ),
        AlertCategory.contact_investigation: (
            "Organizar investigacao operacional de contatos conforme fluxo municipal."
        ),
        AlertCategory.adherence_support: (
            "Avaliar barreiras de adesao e planejar apoio pela equipe de referencia."
        ),
        AlertCategory.territorial_vulnerability: (
            "Considerar visita ou discussao em equipe pela vulnerabilidade territorial."
        ),
    }
    return {category: actions[category] for category in categories}


def title_for_category(category: AlertCategory) -> str:
    titles = {
        AlertCategory.respiratory_symptom_screening: "Rastreio respiratorio prioritario",
        AlertCategory.contact_investigation: "Investigacao de contato prioritario",
        AlertCategory.adherence_support: "Apoio de adesao prioritario",
        AlertCategory.territorial_vulnerability: "Atencao por vulnerabilidade territorial",
    }
    return titles[category]

