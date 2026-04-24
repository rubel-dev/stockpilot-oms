export type PaginatedResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

export type SessionUser = {
  id: string;
  workspace_id: string;
  name: string;
  email: string;
  role: string;
};

export type SessionState = {
  accessToken: string;
  user: SessionUser;
};

