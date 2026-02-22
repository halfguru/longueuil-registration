from longueuil_registration.config import FamilyMember, Settings


def test_family_member_creation():
    member = FamilyMember(name="Test", dossier="01234567890123", nip="5145551234")
    assert member.name == "Test"
    assert member.dossier == "01234567890123"
    assert member.nip == "5145551234"


def test_settings_defaults():
    settings = Settings()
    assert settings.headless is False
    assert settings.timeout == 600
    assert settings.refresh_interval == 5.0
    assert settings.family_members == []


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("LONGUEUIL_HEADLESS", "true")
    monkeypatch.setenv("LONGUEUIL_TIMEOUT", "300")
    monkeypatch.setenv("MEMBER_NAME", "John")
    monkeypatch.setenv("MEMBER_DOSSIER", "12345678901234")
    monkeypatch.setenv("MEMBER_NIP", "5141112222")

    settings = Settings()
    assert settings.headless is True
    assert settings.timeout == 300


def test_settings_custom_values():
    settings = Settings(
        headless=True,
        timeout=120,
        family_members=[
            FamilyMember(name="Child 1", dossier="11111111111111", nip="5141111111"),
        ],
    )
    assert settings.headless is True
    assert settings.timeout == 120
    assert len(settings.family_members) == 1
    assert settings.family_members[0].name == "Child 1"
