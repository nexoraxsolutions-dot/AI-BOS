const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface DashboardSummary {
  total_users: number;
  active_users: number;
  total_companies: number;
  total_sales_monthly: number;
  total_tasks_pending: number;
  recent_users_count: number;
  recent_companies_count: number;
}

export interface DashboardResponse {
  summary: DashboardSummary;
  message: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  username: string | null;
  is_active: boolean;
  is_superuser: boolean;
  company_id: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface Company {
  id: number;
  name: string;
  domain: string;
  description?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  logo_url?: string;
  tax_id?: string;
  industry?: string;
  employee_count?: number;
  subscription_plan?: string;
  subscription_status?: string;
  subscription_expires_at?: string;
  settings?: Record<string, unknown>;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  user_count?: number;
}

export interface CompanyCreate {
  name: string;
  domain: string;
  description?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  logo_url?: string;
  tax_id?: string;
  industry?: string;
  employee_count?: number;
  subscription_plan?: string;
  subscription_status?: string;
  subscription_expires_at?: string;
  settings?: Record<string, unknown>;
}

export interface CompanyUpdate {
  name?: string;
  domain?: string;
  description?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  logo_url?: string;
  tax_id?: string;
  industry?: string;
  employee_count?: number;
  is_active?: boolean;
  subscription_plan?: string;
  subscription_status?: string;
  subscription_expires_at?: string;
  settings?: Record<string, unknown>;
}

export interface CompanyStats {
  total_companies: number;
  active_companies: number;
  inactive_companies: number;
  total_users_across_companies: number;
  avg_employees: number | null;
  plan_distribution: Record<string, number>;
}

export interface CompanyListResponse {
  items: Company[];
  total: number;
  page: number;
  page_size: number;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('ai_bos_token');
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail || 'Login failed');
  }

  return response.json();
}


export async function refreshToken(refresh_token: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Token refresh failed' }));
    throw new Error(error.detail || 'Token refresh failed');
  }

  return response.json();
}

export async function getDashboardSummary(): Promise<DashboardResponse> {
  return request<DashboardResponse>('/dashboard/summary');
}

export async function getUsers(): Promise<User[]> {
  return request<User[]>('/users/');
}

export async function getUser(id: number): Promise<User> {
  return request<User>(`/users/${id}`);
}

export async function getCompanies(): Promise<Company[]> {
  return request<Company[]>('/companies/');
}

export async function getCompany(id: number): Promise<Company> {
  return request<Company>(`/companies/${id}`);
}

export async function createUser(data: {
  email: string;
  full_name?: string;
  username?: string;
  password: string;
}): Promise<User> {
  return request<User>('/users/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateUser(id: number, data: {
  email?: string;
  full_name?: string;
  username?: string;
  password?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  company_id?: number | null;
}): Promise<User> {
  return request<User>(`/users/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteUser(id: number): Promise<void> {
  await request(`/users/${id}`, {
    method: 'DELETE',
  });
}

export async function getMyProfile(): Promise<User> {
  return request<User>('/users/me');
}

export async function updateMyProfile(data: {
  full_name?: string;
  username?: string;
  email?: string;
}): Promise<User> {
  return request<User>('/users/me/profile', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function changeMyPassword(current_password: string, new_password: string): Promise<{ message: string }> {
  return request<{ message: string }>('/users/me/change-password', {
    method: 'POST',
    body: JSON.stringify({ current_password, new_password }),
  });
}

export async function searchUsers(query: string): Promise<User[]> {
  return request<User[]>(`/users/?search=${encodeURIComponent(query)}`);
}

export async function createCompany(data: CompanyCreate): Promise<Company> {
  return request<Company>('/companies/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateCompany(id: number, data: CompanyUpdate): Promise<Company> {
  return request<Company>(`/companies/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteCompany(id: number): Promise<void> {
  await request(`/companies/${id}`, {
    method: 'DELETE',
  });
}

export async function getCompanyList(
  params?: {
    skip?: number;
    limit?: number;
    search?: string;
    is_active?: boolean;
    industry?: string;
    subscription_plan?: string;
    sort_by?: string;
    sort_order?: string;
  }
): Promise<CompanyListResponse> {
  const searchParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
  }
  const query = searchParams.toString();
  return request<CompanyListResponse>(`/companies/?${query}`);
}

export async function getCompanyStats(): Promise<CompanyStats> {
  return request<CompanyStats>('/companies/stats');
}

export async function getCompanyByDomain(domain: string): Promise<Company> {
  return request<Company>(`/companies/by-domain/${encodeURIComponent(domain)}`);
}

// Redis API functions
export interface RedisHealth {
  status: string;
  version?: string;
  connected_clients?: number;
  used_memory_human?: string;
  uptime_in_seconds?: number;
  error?: string;
}

export interface CacheStats {
  total_keys: number;
  used_memory_human: string;
  connected_clients: number;
  hits: number;
  misses: number;
  hit_rate: number;
}

export async function getRedisHealth(): Promise<RedisHealth> {
  return request<RedisHealth>('/redis/health');
}

export async function getCacheStats(): Promise<CacheStats> {
  return request<CacheStats>('/redis/stats');
}

export async function flushCache(): Promise<{ message: string }> {
  return request<{ message: string }>('/redis/flush', {
    method: 'DELETE',
  });
}

// Environment Variables API functions
export interface EnvironmentVariable {
  id: number;
  key: string;
  value?: string;
  masked_value?: string;
  description?: string;
  is_secret: boolean;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentVariableCreate {
  key: string;
  value: string;
  description?: string;
  is_secret: boolean;
}

export interface EnvironmentVariableUpdate {
  value?: string;
  description?: string;
  is_secret?: boolean;
}

export async function getEnvironmentVariables(): Promise<EnvironmentVariable[]> {
  return request<EnvironmentVariable[]>('/environment-variables/');
}

export async function getEnvironmentVariable(id: number): Promise<EnvironmentVariable> {
  return request<EnvironmentVariable>(`/environment-variables/${id}`);
}

export async function getEnvironmentVariableByKey(key: string): Promise<EnvironmentVariable> {
  return request<EnvironmentVariable>(`/environment-variables/key/${key}`);
}

export async function createEnvironmentVariable(data: EnvironmentVariableCreate): Promise<EnvironmentVariable> {
  return request<EnvironmentVariable>('/environment-variables/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateEnvironmentVariable(id: number, data: EnvironmentVariableUpdate): Promise<EnvironmentVariable> {
  return request<EnvironmentVariable>(`/environment-variables/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteEnvironmentVariable(id: number): Promise<void> {
  await request(`/environment-variables/${id}`, {
    method: 'DELETE',
  });
}

export async function exportEnvironmentVariables(): Promise<Record<string, string>> {
  return request<Record<string, string>>('/environment-variables/export/.env');
}

// Tenant Management API functions
export interface TenantStats {
  total_users: number;
  active_users: number;
  total_companies: number;
  active_companies: number;
  total_environment_variables: number;
  storage_used_estimate: string;
}

export interface TenantUserSummary {
  id: number;
  email: string;
  full_name: string | null;
  username: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at?: string;
}

export interface TenantDetail {
  id: number;
  name: string;
  domain: string;
  description?: string;
  industry?: string;
  employee_count?: number;
  subscription_plan: string;
  subscription_status: string;
  is_active: boolean;
  user_count: number;
  users?: TenantUserSummary[];
  created_at?: string;
  updated_at?: string;
}

export interface TenantListResponse {
  items: TenantDetail[];
  total: number;
  page: number;
  page_size: number;
}

export interface UserCompanyAssignment {
  user_id: number;
  company_id: number;
}

export interface TenantInviteRequest {
  email: string;
  full_name?: string;
}

export async function getTenantStats(): Promise<TenantStats> {
  return request<TenantStats>('/tenants/stats');
}

export async function getMyTenant(): Promise<TenantDetail> {
  return request<TenantDetail>('/tenants/my-tenant');
}

export async function getMyTenantDashboard(): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>('/tenants/my-tenant/dashboard');
}

export async function getMyTenantUsers(params?: {
  skip?: number;
  limit?: number;
  search?: string;
}): Promise<TenantUserSummary[]> {
  const searchParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
  }
  const query = searchParams.toString();
  return request<TenantUserSummary[]>(`/tenants/my-tenant/users?${query}`);
}

export async function getTenants(params?: {
  skip?: number;
  limit?: number;
  search?: string;
  is_active?: boolean;
  subscription_plan?: string;
}): Promise<TenantListResponse> {
  const searchParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
  }
  const query = searchParams.toString();
  return request<TenantListResponse>(`/tenants/?${query}`);
}

export async function getTenantDetail(id: number): Promise<TenantDetail> {
  return request<TenantDetail>(`/tenants/${id}`);
}

export async function getTenantUsers(companyId: number, params?: {
  skip?: number;
  limit?: number;
  search?: string;
}): Promise<TenantUserSummary[]> {
  const searchParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
  }
  const query = searchParams.toString();
  return request<TenantUserSummary[]>(`/tenants/${companyId}/users?${query}`);
}

export async function assignUserToCompany(data: UserCompanyAssignment): Promise<{ message: string; user_id: number; company_id: number }> {
  return request<{ message: string; user_id: number; company_id: number }>('/tenants/assign', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function removeUserFromCompany(userId: number): Promise<{ message: string; user_id: number }> {
  return request<{ message: string; user_id: number }>(`/tenants/remove?user_id=${userId}`, {
    method: 'POST',
  });
}
