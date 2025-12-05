from pathlib import Path

from app.services.access import AccessControl


def test_access_control_roles_and_permissions(tmp_path: Path) -> None:
    storage = tmp_path / "access.json"
    root_id = 1
    ac = AccessControl(storage, root_admin_id=root_id)

    # Root is always admin and allowed
    assert ac.is_root(root_id)
    assert ac.is_admin(root_id)
    assert ac.is_allowed(root_id)

    # Add regular user
    assert ac.add_user(10)
    assert ac.is_allowed(10)
    assert not ac.is_admin(10)

    # Promote new admin
    assert ac.promote(20)
    assert ac.is_admin(20)
    assert ac.is_allowed(20)

    # Demote keeps access but drops admin rights
    assert ac.demote(20)
    assert not ac.is_admin(20)
    assert ac.is_allowed(20)

    # Remove strips access entirely
    assert ac.remove_user(20)
    assert not ac.is_allowed(20)
    assert not ac.is_admin(20)

    # Root cannot be modified via remove or promote/demote
    assert not ac.remove_user(root_id)
    assert not ac.promote(root_id)
    assert not ac.demote(root_id)
