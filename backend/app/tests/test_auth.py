from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.services.auth_service import AuthService, CurrentUser


class FakeAuthRepository:
    def __init__(self) -> None:
        self.connection = __import__("app.tests.conftest", fromlist=["FakeConnection"]).FakeConnection()
        self.users_by_email = {}
        self.user_row = None
        self.activity_logged = False

    def get_user_by_email(self, email: str):
        return self.users_by_email.get(email)

    def create_workspace(self, *, name: str, slug: str):
        return {"id": "ws-1", "name": name, "slug": slug}

    def create_user(self, *, workspace_id: str, name: str, email: str, password_hash: str, role: str):
        user = {
            "id": "user-1",
            "workspace_id": workspace_id,
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "is_active": True,
            "created_at": None,
        }
        self.users_by_email[email] = user
        return user

    def create_activity_log(self, **kwargs):
        self.activity_logged = True

    def get_user_with_workspace(self, user_id: str, workspace_id: str):
        if user_id == "user-1" and workspace_id == "ws-1":
            return {
                "id": "user-1",
                "workspace_id": "ws-1",
                "name": "Rubel Hossain",
                "email": "rubel@example.com",
                "role": "owner",
                "is_active": True,
                "created_at": None,
                "workspace_id_check": "ws-1",
                "workspace_name": "Northstar Supply Co",
                "workspace_slug": "northstar-supply-co",
            }
        return None


class FakeWorkspaceRepository:
    def __init__(self) -> None:
        self.existing_slugs = set()

    def slug_exists(self, slug: str) -> bool:
        return slug in self.existing_slugs


def build_service() -> AuthService:
    return AuthService(
        auth_repository=FakeAuthRepository(),
        workspace_repository=FakeWorkspaceRepository(),
        settings=get_settings(),
    )


def test_register_creates_owner_and_token():
    service = build_service()

    response = service.register(
        workspace_name="Northstar Supply Co",
        name="Rubel Hossain",
        email="rubel@example.com",
        password="strongpassword",
    )

    assert response.user.role == "owner"
    assert response.user.workspace_id == "ws-1"
    assert response.access_token


def test_register_rejects_duplicate_email():
    service = build_service()
    service.auth_repository.users_by_email["rubel@example.com"] = {"id": "existing"}

    try:
        service.register(
            workspace_name="Northstar Supply Co",
            name="Rubel Hossain",
            email="rubel@example.com",
            password="strongpassword",
        )
        assert False, "Expected duplicate email conflict"
    except ConflictError:
        assert True


def test_login_rejects_invalid_password():
    service = build_service()
    registered = service.register(
        workspace_name="Northstar Supply Co",
        name="Rubel Hossain",
        email="rubel@example.com",
        password="strongpassword",
    )
    assert registered.access_token

    try:
        service.login(email="rubel@example.com", password="wrongpassword")
        assert False, "Expected auth error"
    except AuthenticationError:
        assert True


def test_get_current_user_profile():
    service = build_service()

    profile = service.get_current_user_profile(CurrentUser(user_id="user-1", workspace_id="ws-1", role="owner"))

    assert profile.user.email == "rubel@example.com"
    assert profile.workspace.slug == "northstar-supply-co"

