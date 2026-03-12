from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from longueuil_aweille.__main__ import app
from longueuil_aweille.status import RegistrationStatus
from longueuil_aweille.verify import VerificationStatus

runner = CliRunner()


class TestVersion:
    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "longueuil-aweille version" in result.stdout


class TestRegister:
    def test_register_missing_config(self, tmp_path: Path):
        result = runner.invoke(app, ["register", "--config", str(tmp_path / "missing.toml")])
        assert result.exit_code != 0

    def test_register_no_participants(self, tmp_path: Path):
        config = tmp_path / "config.toml"
        config.write_text("headless = true\n")
        result = runner.invoke(app, ["register", "--config", str(config)])
        assert result.exit_code == 1
        assert "No participants configured" in result.stdout

    @patch("longueuil_aweille.__main__.RegistrationBot")
    def test_register_success(self, mock_reg_bot, tmp_path: Path):
        config = tmp_path / "config.toml"
        config.write_text("""
headless = true
activity_name = "Test Activity"

[[participants]]
name = "Test User"
carte_acces = "01234567890123"
telephone = "5145551234"
age = 30
""")

        mock_reg_instance = MagicMock()
        mock_reg_instance.run = AsyncMock(return_value=RegistrationStatus.SUCCESS)
        mock_reg_bot.return_value = mock_reg_instance

        result = runner.invoke(app, ["register", "--config", str(config), "--no-verify"])

        assert result.exit_code == 0
        assert "Registration completed" in result.stdout

    @patch("longueuil_aweille.__main__.RegistrationBot")
    def test_register_timeout(self, mock_reg_bot, tmp_path: Path):
        config = tmp_path / "config.toml"
        config.write_text("""
headless = true
activity_name = "Test Activity"

[[participants]]
name = "Test User"
carte_acces = "01234567890123"
telephone = "5145551234"
age = 30
""")

        mock_reg_instance = MagicMock()
        mock_reg_instance.run = AsyncMock(return_value=RegistrationStatus.TIMEOUT)
        mock_reg_bot.return_value = mock_reg_instance

        result = runner.invoke(app, ["register", "--config", str(config), "--no-verify"])

        assert result.exit_code == 1
        assert "timed out" in result.stdout.lower()

    @patch("longueuil_aweille.__main__.RegistrationBot")
    def test_register_timeout_with_cli_option(self, mock_reg_bot, tmp_path: Path):
        config = tmp_path / "config.toml"
        config.write_text("""
headless = true
timeout = 600
activity_name = "Test Activity"

[[participants]]
name = "Test User"
carte_acces = "01234567890123"
telephone = "5145551234"
age = 30
""")

        mock_reg_instance = MagicMock()
        mock_reg_instance.run = AsyncMock(return_value=RegistrationStatus.TIMEOUT)
        mock_reg_bot.return_value = mock_reg_instance

        result = runner.invoke(
            app, ["register", "--config", str(config), "--timeout", "30", "--no-verify"]
        )

        assert result.exit_code == 1
        settings_arg = mock_reg_bot.call_args[0][0]
        assert settings_arg.timeout == 30


class TestVerify:
    @patch("longueuil_aweille.__main__.VerificationBot")
    def test_verify_valid(self, mock_bot):
        mock_instance = MagicMock()
        mock_instance.run = AsyncMock(return_value=VerificationStatus.VALID)
        mock_bot.return_value = mock_instance

        result = runner.invoke(app, ["verify", "--carte", "01234567890123", "--tel", "5145551234"])

        assert result.exit_code == 0
        assert "valid" in result.stdout.lower()

    @patch("longueuil_aweille.__main__.VerificationBot")
    def test_verify_invalid(self, mock_bot):
        mock_instance = MagicMock()
        mock_instance.run = AsyncMock(return_value=VerificationStatus.INVALID)
        mock_bot.return_value = mock_instance

        result = runner.invoke(app, ["verify", "--carte", "01234567890123", "--tel", "5145551234"])

        assert result.exit_code == 1
        assert "invalid" in result.stdout.lower()

    def test_verify_missing_args(self):
        result = runner.invoke(app, ["verify"])
        assert result.exit_code != 0


class TestBrowse:
    @patch("longueuil_aweille.__main__.ActivityScraper")
    def test_browse_no_activities(self, mock_scraper):
        mock_instance = MagicMock()
        mock_instance.run = AsyncMock(return_value=[])
        mock_scraper.return_value = mock_instance

        result = runner.invoke(app, ["browse", "--headless"])

        assert result.exit_code == 0
        assert "No activities found" in result.stdout

    @patch("longueuil_aweille.__main__.ActivityScraper")
    def test_browse_with_activities(self, mock_scraper):
        from longueuil_aweille.browse import Activity
        from longueuil_aweille.status import ActivityStatus

        mock_instance = MagicMock()
        mock_instance.run = AsyncMock(
            return_value=[
                Activity(
                    name="Test Activity",
                    code="ABC123",
                    domain="Test Domain",
                    age_min=5,
                    age_max=12,
                    start_date="1 janvier 2025",
                    end_date="31 mars 2025",
                    promoter="Test Promoter",
                    spots=10,
                    price="50$",
                    days="Lundi",
                    times="18:00-19:00",
                    location="Test Location",
                    status=ActivityStatus.AVAILABLE,
                )
            ]
        )
        mock_instance.filter_activities.return_value = mock_instance.run.return_value
        mock_scraper.return_value = mock_instance

        result = runner.invoke(app, ["browse", "--headless"])

        assert result.exit_code == 0
        assert "Test Activity" in result.stdout
        assert "1 found" in result.stdout

    @patch("longueuil_aweille.__main__.ActivityScraper")
    def test_browse_domain_not_found(self, mock_scraper):
        from longueuil_aweille.browse import DomainNotFoundError

        mock_instance = MagicMock()
        mock_instance.run = AsyncMock(
            side_effect=DomainNotFoundError("Bad Domain", ["Domain A", "Domain B"])
        )
        mock_scraper.return_value = mock_instance

        result = runner.invoke(app, ["browse", "--domain", "Bad Domain", "--headless"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()
        assert "Domain A" in result.stdout
