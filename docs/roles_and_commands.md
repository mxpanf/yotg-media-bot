# Roles and Commands

## Roles
- **Root admin**: Telegram user ID from `root_admin_id` in `config/settings.yaml`. Cannot be removed or demoted.
- **Admin**: Can grant/revoke user access. Root admin can promote/demote admins.
- **User**: Can use the bot if allowed. Anyone else is ignored silently.

## Access rules
- Only allowed users and admins can interact; others receive no replies.
- Forwarding a user's message to the bot (by an admin) grants that user access automatically and sends them a notification.

## Commands
- `/add {user_id}` — grant access to a user (admin+).
- `/remove {user_id}` — revoke access and admin rights (admin+).
- `/op {user_id}` — promote to admin (root admin only; also grants access).
- `/deop {user_id}` — demote admin to regular user, access remains (root admin only).
- `/settings` — choose language (for allowed users).
- `/help` — usage overview; shows admin commands when the requester is an admin.

## Notes
- Access data is stored in `data_dir/access.json` (configurable via `data_dir` in settings).
- Promotion/demotion and removal do not affect the root admin.***
