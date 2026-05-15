from backend.schemas import AdherenceInfo, ContactInfo, QuestionnaireCreate, Symptoms


def synthetic_questionnaires() -> list[QuestionnaireCreate]:
    return [
        QuestionnaireCreate(
            synthetic_person_id="SYN-P001",
            territory_id="TERR-01",
            territory_name="Territorio Norte",
            micro_area="MA-01",
            age_range="40-59",
            symptoms=Symptoms(cough_weeks=3, fever=True, night_sweats=True, weight_loss=True),
            contact=ContactInfo(known_tb_contact=True, household_contact=True),
            barriers=["transport"],
            vulnerabilities=["deprivation"],
            submitted_by="acs_demo",
        ),
        QuestionnaireCreate(
            synthetic_person_id="SYN-P002",
            territory_id="TERR-01",
            territory_name="Territorio Norte",
            micro_area="MA-02",
            age_range="20-39",
            symptoms=Symptoms(cough_weeks=0),
            contact=ContactInfo(known_tb_contact=True, household_contact=False),
            vulnerabilities=["previous_tb"],
            submitted_by="acs_demo",
        ),
        QuestionnaireCreate(
            synthetic_person_id="SYN-P003",
            territory_id="TERR-02",
            territory_name="Territorio Leste",
            micro_area="MA-05",
            age_range="60+",
            adherence=AdherenceInfo(
                on_treatment=True,
                missed_recent_appointments=True,
                side_effects_reported=True,
            ),
            barriers=["food_insecurity", "side_effects"],
            vulnerabilities=["diabetes"],
            submitted_by="enfermagem_demo",
        ),
        QuestionnaireCreate(
            synthetic_person_id="SYN-P004",
            territory_id="TERR-02",
            territory_name="Territorio Leste",
            micro_area="MA-06",
            age_range="20-39",
            symptoms=Symptoms(cough_weeks=1, fever=True),
            barriers=["stigma"],
            submitted_by="acs_demo",
        ),
        QuestionnaireCreate(
            synthetic_person_id="SYN-P005",
            territory_id="TERR-03",
            territory_name="Territorio Oeste",
            micro_area="MA-09",
            age_range="40-59",
            adherence=AdherenceInfo(
                on_treatment=True,
                missed_recent_appointments=True,
                treatment_interruption=True,
            ),
            barriers=["transport", "stigma"],
            vulnerabilities=["homelessness", "substance_use"],
            submitted_by="enfermagem_demo",
        ),
        QuestionnaireCreate(
            synthetic_person_id="SYN-P006",
            territory_id="TERR-03",
            territory_name="Territorio Oeste",
            micro_area="MA-10",
            age_range="10-19",
            symptoms=Symptoms(cough_weeks=0),
            submitted_by="acs_demo",
        ),
    ]

