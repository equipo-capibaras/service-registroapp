from typing import Any

from models import Role


def gen_token(*, user_id: str, client_id: str | None, role: Role, assigned: bool) -> dict[str, Any]:
    return {
        'sub': user_id,
        'cid': client_id,
        'role': role.value,
        'aud': ('' if assigned else 'unassigned_') + role.value,
    }
