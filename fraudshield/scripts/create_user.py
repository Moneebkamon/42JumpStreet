"""Create or update a staff account.

  python scripts/create_user.py <username> <analyst|admin>            (asks for the password, hidden)
  python scripts/create_user.py <username> <role> --generate          (makes a random password, writes it to a file)

With --generate the password is written to data/interim/credentials-<username>.txt (git-ignored), never printed.
"""
import getpass
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.auth import ROLES, hash_password  # noqa: E402
from app.repositories import user_repo  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in ROLES:
        print(__doc__)
        return 2
    username, role = argv[0].strip(), argv[1]
    if "--generate" in argv:
        password = secrets.token_urlsafe(12)
        out = Path(__file__).resolve().parents[1] / "data" / "interim" / f"credentials-{username}.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f"username: {username}\nrole: {role}\npassword: {password}\n")
        print(f"Created {role} '{username}'. The password was written to {out}")
    else:
        password = getpass.getpass("Password (min 8 characters): ")
        if len(password) < 8:
            print("Password too short.")
            return 2
        print(f"Created {role} '{username}'.")
    user_repo.upsert(username, hash_password(password), role)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
