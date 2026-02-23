from longueuil_aweille.config import Participant, Settings


def test_participant_creation():
    participant = Participant(name="Test", dossier="01234567890123", nip="5145551234")
    assert participant.name == "Test"
    assert participant.dossier == "01234567890123"
    assert participant.nip == "5145551234"


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
            Participant(name="Participant 1", dossier="11111111111111", nip="5141111111"),
        ],
    )
    assert settings.headless is True
    assert settings.timeout == 120
    assert len(settings.participants) == 1
    assert settings.participants[0].name == "Participant 1"
