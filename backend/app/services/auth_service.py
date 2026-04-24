import re
from dataclasses import dataclass

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.auth_repository import AuthRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.auth import AuthUser, CurrentUserResponse, TokenResponse, WorkspaceSummary


@dataclass(slots=True)
class CurrentUser:
    user_id: str
    workspace_id: str
    role: str


class AuthService:
    def __init__(
        self,
        *,
        auth_repository: AuthRepository,
        workspace_repository: WorkspaceRepository,
        settings: Settings,
    ) -> None:
        self.auth_repository = auth_repository
        self.workspace_repository = workspace_repository
        self.settings = settings

    def register(self, *, workspace_name: str, name: str, email: str, password: str) -> TokenResponse:
        if self.auth_repository.get_user_by_email(email):
            raise ConflictError("An account with this email already exists.")

        slug = self._build_unique_workspace_slug(workspace_name)
        with self.auth_repository.connection.transaction():
            workspace = self.auth_repository.create_workspace(name=workspace_name.strip(), slug=slug)
            user = self.auth_repository.create_user(
                workspace_id=workspace["id"],
                name=name.strip(),
                email=email.lower(),
                password_hash=hash_password(password),
                role="owner",
            )
            self.auth_repository.create_activity_log(
                workspace_id=workspace["id"],
                actor_user_id=user["id"],
                action="workspace.created",
                entity_type="workspace",
                entity_id=workspace["id"],
                summary=f"Workspace {workspace['name']} was created",
                metadata={"workspace_slug": workspace["slug"]},
            )

        return self._build_token_response(user)

    def login(self, *, email: str, password: str) -> TokenResponse:
        user = self.auth_repository.get_user_by_email(email.lower())
        if not user or not verify_password(password, user["password_hash"]):
            raise AuthenticationError("Invalid email or password.")
        if not user["is_active"]:
            raise AuthenticationError("This account is inactive.")
        return self._build_token_response(user)

    def get_current_user_profile(self, current_user: CurrentUser) -> CurrentUserResponse:
        row = self.auth_repository.get_user_with_workspace(current_user.user_id, current_user.workspace_id)
        if not row:
            raise NotFoundError("Authenticated user was not found.")
        return CurrentUserResponse(
            user=AuthUser(
                id=row["id"],
                workspace_id=row["workspace_id"],
                name=row["name"],
                email=row["email"],
                role=row["role"],
                is_active=row["is_active"],
                created_at=row["created_at"],
            ),
            workspace=WorkspaceSummary(
                id=row["workspace_id_check"],
                name=row["workspace_name"],
                slug=row["workspace_slug"],
            ),
        )

    def _build_token_response(self, user: dict) -> TokenResponse:
        token = create_access_token(
            subject=user["id"],
            workspace_id=user["workspace_id"],
            role=user["role"],
            settings=self.settings,
        )
        return TokenResponse(
            access_token=token,
            user=AuthUser(
                id=user["id"],
                workspace_id=user["workspace_id"],
                name=user["name"],
                email=user["email"],
                role=user["role"],
                is_active=user["is_active"],
                created_at=user.get("created_at"),
            ),
        )

    def _build_unique_workspace_slug(self, workspace_name: str) -> str:
        base_slug = re.sub(r"[^a-z0-9]+", "-", workspace_name.strip().lower()).strip("-") or "workspace"
        candidate = base_slug
        suffix = 2
        while self.workspace_repository.slug_exists(candidate):
            candidate = f"{base_slug}-{suffix}"
            suffix += 1
        return candidate

