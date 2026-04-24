from dataclasses import dataclass


@dataclass(slots=True)
class PaginationParams:
    page: int = 1
    page_size: int = 25

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def normalize_pagination(page: int = 1, page_size: int = 25) -> PaginationParams:
    safe_page = max(page, 1)
    safe_page_size = min(max(page_size, 1), 100)
    return PaginationParams(page=safe_page, page_size=safe_page_size)

