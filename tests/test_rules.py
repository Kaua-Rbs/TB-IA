from backend.rules_engine import evaluate_questionnaire
from backend.schemas import ContactInfo, Priority, Questionnaire, QuestionnaireCreate, Symptoms


def test_rule_engine_explains_high_priority_contact_and_symptoms() -> None:
    questionnaire = Questionnaire(
        **QuestionnaireCreate(
            synthetic_person_id="SYN-TEST-1",
            territory_id="T1",
            territory_name="Territorio Teste",
            micro_area="MA-1",
            symptoms=Symptoms(cough_weeks=3, fever=True),
            contact=ContactInfo(known_tb_contact=True, household_contact=True),
        ).model_dump()
    )

    evaluation = evaluate_questionnaire(questionnaire)

    assert evaluation.priority in {Priority.high, Priority.critical}
    assert evaluation.score >= 60
    assert any("Tosse" in reason for reason in evaluation.rationale)
    assert any("Contato" in reason for reason in evaluation.rationale)


def test_rule_engine_keeps_low_priority_for_routine_monitoring() -> None:
    questionnaire = Questionnaire(
        **QuestionnaireCreate(
            synthetic_person_id="SYN-TEST-2",
            territory_id="T1",
            territory_name="Territorio Teste",
            micro_area="MA-1",
        ).model_dump()
    )

    evaluation = evaluate_questionnaire(questionnaire)

    assert evaluation.priority == Priority.low
    assert evaluation.score == 0
    assert evaluation.rationale

