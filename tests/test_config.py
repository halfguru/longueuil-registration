from longueuil_aweille.config import Participant, Settings


def test_participant_creation():
    participant = Participant(
        name="Test", carte_acces="01234567890123", telephone="5145551234", age=30
    )
    assert participant.name == "Test"
    assert participant.carte_acces == "01234567890123"
    assert participant.telephone == "5145551234"
    assert participant.age == 30


def test_settings_defaults():
    settings = Settings()
    assert settings.headless is False
    assert settings.timeout == 600
    assert settings.refresh_interval == 5.0
    assert settings.participants == []


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("LONGUEUIL_HEADLESS", "true")
    monkeypatch.setenv("LONGUEUIL_TIMEOUT", "300")

    settings = Settings()
    assert settings.headless is True
    assert settings.timeout == 300


def test_settings_custom_values():
    settings = Settings(
        headless=True,
        timeout=120,
        participants=[
            Participant(
                name="Participant 1", carte_acces="11111111111111", telephone="5141111111", age=25
            ),
        ],
    )
    assert settings.headless is True
    assert settings.timeout == 120
    assert len(settings.participants) == 1
    assert settings.participants[0].name == "Participant 1"
