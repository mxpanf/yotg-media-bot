from pathlib import Path

from app.config import AppConfig
from app.services.access import AccessControl
from app.services.preferences import UserPreferences


def test_preferences_reload(tmp_path: Path) -> None:
    prefs_path = tmp_path / "prefs.json"
    prefs = UserPreferences(prefs_path, "en")
    prefs.set_locale(10, "ru")

    # Reload and ensure value persists
    prefs2 = UserPreferences(prefs_path, "en")
    assert prefs2.get_locale(10) == "ru"


def test_access_root_seed(tmp_path: Path) -> None:
    path = tmp_path / "access.json"
    ac = AccessControl(path, root_admin_id=7)
    assert ac.is_root(7)
    assert ac.is_admin(7)
    assert ac.is_allowed(7)

    # Persist and reload
    ac2 = AccessControl(path, root_admin_id=7)
    assert ac2.is_admin(7)
    assert ac2.is_allowed(7)


def test_app_config_overrides(tmp_path: Path, monkeypatch) -> None:
    yaml_path = tmp_path / "settings.yaml"
    yaml_path.write_text(
        "bot_token: TEST\nlocale_default: en\ntmp_dir: /tmp/test\ndata_dir: /tmp/data\nroot_admin_id: 42\n"
    )
    monkeypatch.setenv("YOTG_CONFIG_FILE", str(yaml_path))
    cfg = AppConfig()  # type: ignore[call-arg]
    assert cfg.bot_token == "TEST"
    assert cfg.locale_default == "en"
    assert cfg.tmp_dir == Path("/tmp/test")
    assert cfg.data_dir == Path("/tmp/data")
    assert cfg.root_admin_id == 42
