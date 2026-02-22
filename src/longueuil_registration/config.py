from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FamilyMember(BaseSettings):
    name: str = Field(..., description="Family member name for logging")
    dossier: str = Field(..., description="Dossier number")
    nip: str = Field(..., description="NIP (phone number)")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LONGUEUIL_")

    registration_url: str = Field(
        default="https://loisir.longueuil.quebec/inscription/Pages/Anonyme/Resultat/Page.fr.aspx?m=1",
        description="Registration website URL",
    )
    headless: bool = Field(default=False, description="Run browser in headless mode")
    timeout: int = Field(default=600, description="Timeout in seconds")
    refresh_interval: float = Field(default=5.0, description="Refresh interval in seconds")
    domain: str = Field(
        default="Activités aquatiques (Vieux-Longueuil)",
        description="Domain/category to select (e.g., 'Activités aquatiques (Vieux-Longueuil)')",
    )
    activity_name: str = Field(
        default="",
        description="Activity name to search for (e.g., 'Parent-bébé', 'Niveau 1')",
    )
    family_members: list[FamilyMember] = Field(default_factory=list)

    @classmethod
    def from_toml(cls, path: Path) -> "Settings":
        import tomllib

        with open(path, "rb") as f:
            data = tomllib.load(f)

        members_data = data.pop("family_members", [])
        family_members = [FamilyMember(**m) for m in members_data]
        return cls(**data, family_members=family_members)
