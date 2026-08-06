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
    is_email_verified?: boolean;
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
    user?: {
      id: number;
      email: string;
      full_name?: string | null;
      username?: string | null;
      is_active: boolean;
      is_superuser: boolean;
      company_id?: number | null;
    };
  }

  export interface RegisterResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    user: {
      id: number;
      email: string;
      full_name?: string | null;
      username?: string | null;
      is_active: boolean;
      is_superuser: boolean;
      company_id?: number | null;
    };
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

    // Handle responses with no content (204)
    if (response.status === 204) {
      return undefined as T;
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

  export async function register(
    email: string,
    password: string,
    fullName?: string,
    username?: string,
  ): Promise<RegisterResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, full_name: fullName, username }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(error.detail || 'Registration failed');
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

  // ==================== Company Onboarding / Membership API ====================

  export interface UserCompanyOut {
    id: number;
    name: string;
    domain: string;
    role?: string;
    is_active?: boolean;
    is_current?: boolean;
    created_at?: string;
  }

  export interface UserCompaniesResponse {
    items: UserCompanyOut[];
    total: number;
    active_company_id?: number | null;
  }

  export interface OnboardCompanyRequest {
    name: string;
    domain?: string;
    industry?: string;
    employee_count?: number;
    website?: string;
    logo_url?: string;
    settings?: Record<string, unknown>;
  }

  export interface OnboardCompanyResponse extends Company {
    membership_role?: string;
    default_department?: Record<string, unknown> | null;
    organization_settings?: Record<string, unknown> | null;
  }

  export interface SwitchCompanyResponse {
    message: string;
    active_company_id: number;
  }

  export interface CompanyInvitationDetail {
    id: number;
    company_id: number;
    company_name: string;
    email: string;
    role: string;
    status: string;
    expires_at: string;
    created_at?: string;
  }

  export interface InvitationActionResponse {
    message: string;
    invitation_id?: number;
    company_id?: number;
    company_name?: string;
    joined: boolean;
  }

  export async function listUserCompanies(): Promise<UserCompaniesResponse> {
    return request<UserCompaniesResponse>('/companies/my');
  }

  export async function onboardCompany(
    data: OnboardCompanyRequest,
  ): Promise<OnboardCompanyResponse> {
    return request<OnboardCompanyResponse>('/companies/onboard', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  export async function switchCompany(companyId: number): Promise<SwitchCompanyResponse> {
    return request<SwitchCompanyResponse>('/companies/switch', {
      method: 'POST',
      body: JSON.stringify({ company_id: companyId }),
    });
  }

  export async function getInvitation(
    token: string,
  ): Promise<CompanyInvitationDetail> {
    return request<CompanyInvitationDetail>(
      `/companies/invitations/${encodeURIComponent(token)}`,
    );
  }

  export async function acceptInvitation(token: string): Promise<InvitationActionResponse> {
    return request<InvitationActionResponse>(
      `/companies/invitations/${encodeURIComponent(token)}/accept`,
      { method: 'POST' },
    );
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

  // Audit Log API functions
  export interface AuditLog {
    id: number;
    action: string;
    resource_type: string;
    resource_id?: number;
    user_id?: number;
    ip_address?: string;
    user_agent?: string;
    details?: Record<string, unknown>;
    created_at: string;
  }

  export interface AuditLogListResponse {
    items: AuditLog[];
    total: number;
    page: number;
    page_size: number;
  }

  export async function getAuditLogs(params?: {
    skip?: number;
    limit?: number;
    action?: string;
    resource_type?: string;
    user_id?: number;
  }): Promise<AuditLogListResponse> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return request<AuditLogListResponse>(`/audit-logs/?${query}`);
  }

  export async function getMyAuditLogs(params?: {
    skip?: number;
    limit?: number;
    action?: string;
    resource_type?: string;
  }): Promise<AuditLogListResponse> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return request<AuditLogListResponse>(`/audit-logs/my-logs/?${query}`);
  }

  // Token Management API functions
  export interface TokenInfo {
    id: number;
    user_id: number;
    token: string;
    token_type: string;
    client_ip?: string;
    user_agent?: string;
    is_revoked: boolean;
    expires_at: string;
    created_at?: string;
  }

  export interface TokenListResponse {
    items: TokenInfo[];
    total: number;
    page: number;
    page_size: number;
  }

  export interface TokenRevokeResponse {
    message: string;
    token_id: number;
    revoked: boolean;
  }

  export interface TokenCleanupResponse {
    message: string;
    deleted_count: number;
  }

  export async function getTokens(
    skip: number = 0,
    limit: number = 50,
    include_revoked: boolean = false
  ): Promise<TokenListResponse> {
    const params = new URLSearchParams();
    params.append('skip', String(skip));
    params.append('limit', String(limit));
    params.append('include_revoked', String(include_revoked));
    return request<TokenListResponse>(`/tokens/?${params.toString()}`);
  }

  export async function getTokenById(id: number): Promise<TokenInfo> {
    return request<TokenInfo>(`/tokens/${id}`);
  }

  export async function revokeToken(token_id: number): Promise<TokenRevokeResponse> {
    return request<TokenRevokeResponse>('/tokens/revoke', {
      method: 'POST',
      body: JSON.stringify({ token_id }),
    });
  }

  export async function revokeAllTokens(): Promise<{ message: string; revoked_count: number }> {
    return request<{ message: string; revoked_count: number }>('/tokens/revoke-all', {
      method: 'POST',
    });
  }

  export async function cleanupTokens(): Promise<TokenCleanupResponse> {
    return request<TokenCleanupResponse>('/tokens/cleanup', {
      method: 'POST',
    });
  }

  // Session Management API functions
  export interface SessionInfo {
    id: number;
    user_id: number;
    session_token: string;
    ip_address?: string;
    user_agent?: string;
    device_name?: string;
    device_type?: string;
    browser?: string;
    os?: string;
    is_active: boolean;
    last_activity_at?: string;
    expires_at: string;
    created_at?: string;
    terminated_at?: string;
  }

  export interface SessionListResponse {
    items: SessionInfo[];
    total: number;
    page: number;
    page_size: number;
  }

  export interface SessionStats {
    total_sessions: number;
    active_sessions: number;
    inactive_sessions: number;
    expired_sessions: number;
    device_type_breakdown: Record<string, number>;
  }

  export interface SessionTerminateResponse {
    message: string;
    session_id: number;
    terminated: boolean;
  }

  export interface SessionCleanupResponse {
    message: string;
    deleted_count: number;
  }

  export async function getSessions(
    skip: number = 0,
    limit: number = 50,
    include_inactive: boolean = false
  ): Promise<SessionListResponse> {
    const params = new URLSearchParams();
    params.append('skip', String(skip));
    params.append('limit', String(limit));
    params.append('include_inactive', String(include_inactive));
    return request<SessionListResponse>(`/sessions/?${params.toString()}`);
  }

  export async function getSessionStats(): Promise<SessionStats> {
    return request<SessionStats>('/sessions/stats');
  }

  export async function getSessionById(id: number): Promise<SessionInfo> {
    return request<SessionInfo>(`/sessions/${id}`);
  }

  export async function terminateSession(session_id: number): Promise<SessionTerminateResponse> {
    return request<SessionTerminateResponse>('/sessions/terminate', {
      method: 'POST',
      body: JSON.stringify({ session_id }),
    });
  }

  export async function terminateAllSessions(): Promise<{ message: string; terminated_count: number }> {
    return request<{ message: string; terminated_count: number }>('/sessions/terminate-all', {
      method: 'POST',
    });
  }

  export async function cleanupSessions(): Promise<SessionCleanupResponse> {
    return request<SessionCleanupResponse>('/sessions/cleanup', {
      method: 'POST',
    });
  }

  // API Keys API functions
  export interface ApiKeyInfo {
    id: number;
    user_id: number;
    key_name: string;
    api_key: string;
    permissions?: string;
    is_active: boolean;
    expires_at?: string;
    last_used_at?: string;
    created_at?: string;
    updated_at?: string;
  }

  export interface ApiKeyListResponse {
    items: ApiKeyInfo[];
    total: number;
    page: number;
    page_size: number;
  }

  export interface ApiKeyCreateResponse {
    id: number;
    key_name: string;
    api_key: string;
    message: string;
  }

  export async function getApiKeys(
    skip: number = 0,
    limit: number = 50,
    include_inactive: boolean = false
  ): Promise<ApiKeyListResponse> {
    const params = new URLSearchParams();
    params.append('skip', String(skip));
    params.append('limit', String(limit));
    params.append('include_inactive', String(include_inactive));
    return request<ApiKeyListResponse>(`/api-keys/?${params.toString()}`);
  }

  export async function createApiKey(data: {
    key_name: string;
    permissions?: string;
    expires_at?: string;
  }): Promise<ApiKeyCreateResponse> {
    return request<ApiKeyCreateResponse>('/api-keys/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  export async function getApiKeyById(id: number): Promise<ApiKeyInfo> {
    return request<ApiKeyInfo>(`/api-keys/${id}`);
  }

  export async function updateApiKey(id: number, data: {
    key_name?: string;
    permissions?: string;
    expires_at?: string;
    is_active?: boolean;
  }): Promise<ApiKeyInfo> {
    return request<ApiKeyInfo>(`/api-keys/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  export async function deleteApiKey(id: number): Promise<void> {
    await request(`/api-keys/${id}`, {
      method: 'DELETE',
    });
  }

  export async function revokeApiKey(id: number): Promise<{ message: string }> {
    return request<{ message: string }>(`/api-keys/revoke/${id}`, {
      method: 'POST',
    });
  }

  // Email Verification API functions
  export interface VerifyEmailResponse {
    message: string;
    email_verified: boolean;
  }

  export interface ResendVerificationResponse {
    message: string;
  }

  export async function verifyEmail(token: string): Promise<VerifyEmailResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/verify-email/${encodeURIComponent(token)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Verification failed' }));
      throw new Error(error.detail || 'Verification failed');
    }

    return response.json();
  }

  export async function resendVerification(email: string): Promise<ResendVerificationResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/resend-verification`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to resend verification' }));
      throw new Error(error.detail || 'Failed to resend verification');
    }

    return response.json();
  }

  // Forgot Password API functions
  export interface ForgotPasswordResponse {
    message: string;
  }

  export interface ResetPasswordResponse {
    message: string;
  }

  export async function forgotPassword(email: string): Promise<ForgotPasswordResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  export async function resetPassword(token: string, newPassword: string, confirmPassword: string): Promise<ResetPasswordResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token, new_password: newPassword, confirm_password: confirmPassword }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Reset failed' }));
      throw new Error(error.detail || 'Reset failed');
    }

    return response.json();
  }

  // Account Lock API functions
  export interface AccountLockStatus {
    is_locked: boolean;
    reason: string | null;
    failed_attempts: number;
    locked_until: string | null;
  }

  export interface LockedAccount extends User {
    failed_login_attempts: number;
    locked_until: string | null;
    lock_reason: string | null;
  }

  export async function getMyAccountLockStatus(): Promise<AccountLockStatus> {
    return request<AccountLockStatus>('/account-lock/me/status');
  }

  export async function getLockedAccounts(skip: number = 0, limit: number = 20): Promise<LockedAccount[]> {
    const params = new URLSearchParams();
    params.append('skip', String(skip));
    params.append('limit', String(limit));
    return request<LockedAccount[]>(`/account-lock/locked?${params.toString()}`);
  }

  export async function unlockAccount(userId: number): Promise<User> {
    return request<User>(`/account-lock/${userId}/unlock`, {
      method: 'POST',
    });
  }

  // Role Management API functions
  export interface Role {
    id: number;
    name: string;
    description?: string;
    is_system_role: boolean;
    created_at: string;
    permissions: Array<{ id: number; name: string; resource: string; action: string }>;
    permission_count?: number;
    user_count?: number;
  }

  export interface Permission {
    id: number;
    name: string;
    resource: string;
    action: string;
    description?: string;
  }

  export async function getRoleUsers(roleId: number): Promise<UserWithRoles[]> {
    return request<UserWithRoles[]>(`/roles/${roleId}/users`);
  }

  export interface RoleList {
    id: number;
    name: string;
    description?: string;
    is_system_role: boolean;
    created_at: string;
    permission_count?: number;
    user_count?: number;
  }

  export async function getRoles(): Promise<RoleList[]> {
    return request<RoleList[]>('/roles/');
  }

  export async function getPermissions(): Promise<Permission[]> {
    return request<Permission[]>('/roles/permissions');
  }

  export async function getRole(id: number): Promise<Role> {
    return request<Role>(`/roles/${id}`);
  }

  export async function createRole(data: {
    name: string;
    description?: string;
    permission_ids?: number[];
  }): Promise<Role> {
    return request<Role>('/roles/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  export async function updateRole(id: number, data: {
    name?: string;
    description?: string;
    permission_ids?: number[];
  }): Promise<Role> {
    return request<Role>(`/roles/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  export async function deleteRole(id: number): Promise<void> {
    await request(`/roles/${id}`, {
      method: 'DELETE',
    });
  }

  export async function assignRoleToUser(userId: number, roleId: number): Promise<{ message: string }> {
    return request<{ message: string }>('/roles/assign', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, role_id: roleId }),
    });
  }

  export async function removeRoleFromUser(userId: number, roleId: number): Promise<{ message: string }> {
    return request<{ message: string }>('/roles/remove', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, role_id: roleId }),
    });
  }

  export interface UserWithRoles extends User {
    roles: Role[];
  }

  // Test Framework API functions
  export interface TestSuite {
    id: number
    name: string
    description?: string
    is_active: boolean
    is_automated: boolean
    company_id?: number
    created_by_id?: number
    created_at: string
    updated_at: string
  }

  export interface TestSuiteCreate {
    name: string
    description?: string
    is_active?: boolean
    is_automated?: boolean
    company_id?: number
  }

  export interface TestSuiteUpdate {
    name?: string
    description?: string
    is_active?: boolean
    is_automated?: boolean
    company_id?: number
  }

  export interface TestSuiteListResponse {
    items: TestSuite[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }

  export interface TestCase {
    id: number
    test_suite_id: number
    name: string
    description?: string
    priority: string
    test_type: string
    endpoint?: string
    method?: string
    payload?: string
    expected_status?: number
    expected_response?: string
    tags?: string
    timeout: number
    retry_count: number
    is_active: boolean
    order: number
    status: string
    last_run_at?: string
    last_run_status?: string
    last_run_duration?: number
    success_count: number
    failure_count: number
    created_at: string
    updated_at: string
  }

  export interface TestCaseCreate {
    test_suite_id: number
    name: string
    description?: string
    priority?: string
    test_type: string
    endpoint?: string
    method?: string
    payload?: string
    expected_status?: number
    expected_response?: string
    tags?: string
    timeout?: number
    retry_count?: number
    is_active?: boolean
    order?: number
  }

  export interface TestCaseUpdate {
    name?: string
    description?: string
    priority?: string
    test_type?: string
    endpoint?: string
    method?: string
    payload?: string
    expected_status?: number
    expected_response?: string
    tags?: string
    timeout?: number
    retry_count?: number
    is_active?: boolean
    order?: number
  }

  export interface TestCaseListResponse {
    items: TestCase[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }

  export interface TestRun {
    id: number
    test_suite_id: number
    triggered_by_id?: number
    status: string
    started_at: string
    completed_at?: string
    duration?: number
    total_tests: number
    passed_tests: number
    failed_tests: number
    skipped_tests: number
    error_tests: number
    success_rate?: number
    environment: string
    branch?: string
    commit_hash?: string
    triggered_by: string
    error_message?: string
    error_traceback?: string
    created_at: string
  }

  export interface TestRunSummary {
    id: number
    test_suite_name: string
    status: string
    started_at: string
    completed_at?: string
    duration?: number
    total_tests: number
    passed_tests: number
    failed_tests: number
    skipped_tests: number
    error_tests: number
    success_rate?: number
    environment: string
    triggered_by: string
    triggered_by_user?: string
    created_at: string
  }

  export interface TestRunCreate {
    test_suite_id: number
    environment?: string
    branch?: string
    commit_hash?: string
    triggered_by?: string
  }

  export interface TestRunListResponse {
    items: TestRunSummary[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }

  export interface TestResult {
    id: number
    test_run_id: number
    test_case_id: number
    status: string
    output?: string
    error_message?: string
    error_traceback?: string
    started_at: string
    completed_at?: string
    duration?: number
    request_url?: string
    request_method?: string
    request_headers?: string
    request_body?: string
    response_status?: number
    response_headers?: string
    response_body?: string
    retry_attempt: number
    environment: string
    created_at: string
  }

  export interface TestResultDetail extends TestResult {
    test_case_name: string
    test_suite_name: string
    test_type: string
    priority: string
  }

  export interface TestResultListResponse {
    items: TestResultDetail[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }

  export interface TestStatistics {
    total_suites: number
    total_cases: number
    total_runs: number
    total_results: number
    passed_tests: number
    failed_tests: number
    skipped_tests: number
    error_tests: number
    success_rate: number
    average_duration?: number
    most_failed_tests: Array<Record<string, unknown>>
    recent_runs: TestRunSummary[]
  }

  export interface TestRunCompleteRequest {
    status: string
    total_tests: number
    passed_tests: number
    failed_tests: number
    skipped_tests: number
    error_tests: number
    duration: number
    error_message?: string
    error_traceback?: string
  }

  export async function getTestSuites(params?: {
    skip?: number
    limit?: number
    search?: string
    company_id?: number
    is_active?: boolean
  }): Promise<TestSuiteListResponse> {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
    }
    const query = searchParams.toString()
    return request<TestSuiteListResponse>(`/testing/suites/?${query}`)
  }

  export async function getTestSuite(id: number): Promise<TestSuite> {
    return request<TestSuite>(`/testing/suites/${id}`)
  }

  export async function createTestSuite(data: TestSuiteCreate): Promise<TestSuite> {
    return request<TestSuite>('/testing/suites/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  export async function updateTestSuite(id: number, data: TestSuiteUpdate): Promise<TestSuite> {
    return request<TestSuite>(`/testing/suites/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  export async function deleteTestSuite(id: number): Promise<void> {
    await request(`/testing/suites/${id}`, {
      method: 'DELETE',
    })
  }

  export async function getTestCases(testSuiteId: number, params?: {
    skip?: number
    limit?: number
    priority?: string
    status?: string
    test_type?: string
    is_active?: boolean
  }): Promise<TestCaseListResponse> {
    const searchParams = new URLSearchParams()
    searchParams.append('test_suite_id', String(testSuiteId))
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
    }
    const query = searchParams.toString()
    return request<TestCaseListResponse>(`/testing/cases/?${query}`)
  }

  export async function getTestCase(id: number): Promise<TestCase> {
    return request<TestCase>(`/testing/cases/${id}`)
  }

  export async function createTestCase(data: TestCaseCreate): Promise<TestCase> {
    return request<TestCase>('/testing/cases/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  export async function updateTestCase(id: number, data: TestCaseUpdate): Promise<TestCase> {
    return request<TestCase>(`/testing/cases/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  export async function deleteTestCase(id: number): Promise<void> {
    await request(`/testing/cases/${id}`, {
      method: 'DELETE',
    })
  }

  export async function getTestRuns(params?: {
    skip?: number
    limit?: number
    test_suite_id?: number
    status?: string
    environment?: string
  }): Promise<TestRunListResponse> {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
    }
    const query = searchParams.toString()
    return request<TestRunListResponse>(`/testing/runs/?${query}`)
  }

  export async function getTestRun(id: number): Promise<TestRun> {
    return request<TestRun>(`/testing/runs/${id}`)
  }

  export async function createTestRun(data: TestRunCreate): Promise<TestRun> {
    return request<TestRun>('/testing/runs/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  export async function completeTestRun(id: number, data: TestRunCompleteRequest): Promise<TestRun> {
    return request<TestRun>(`/testing/runs/${id}/complete`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  export async function getTestResults(testRunId: number, params?: {
    skip?: number
    limit?: number
    status?: string
  }): Promise<TestResultListResponse> {
    const searchParams = new URLSearchParams()
    searchParams.append('test_run_id', String(testRunId))
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
    }
    const query = searchParams.toString()
    return request<TestResultListResponse>(`/testing/results/?${query}`)
  }

  export async function getTestStatistics(params?: {
    company_id?: number
  }): Promise<TestStatistics> {
    const searchParams = new URLSearchParams()
    if (params?.company_id) {
      searchParams.append('company_id', String(params.company_id))
    }
    const query = searchParams.toString()
    return request<TestStatistics>(`/testing/statistics/?${query}`)
  }

  // Department Management API functions
  export interface Department {
    id: number;
    name: string;
    description?: string;
    company_id: number;
    manager_id?: number;
    budget?: string;
    location?: string;
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
    manager_name?: string;
    company_name?: string;
    employee_count?: number;
  }

  export interface DepartmentCreate {
    name: string;
    description?: string;
    company_id: number;
    manager_id?: number;
    budget?: string;
    location?: string;
    is_active?: boolean;
  }

  export interface DepartmentUpdate {
    name?: string;
    description?: string;
    manager_id?: number;
    budget?: string;
    location?: string;
    is_active?: boolean;
  }

  export interface DepartmentStats {
    total_departments: number;
    active_departments: number;
    inactive_departments: number;
    total_companies_with_departments: number;
    avg_departments_per_company: number | null;
    departments_by_company: Record<string, number>;
  }

  export interface DepartmentListResponse {
    items: Department[];
    total: number;
    page: number;
    page_size: number;
  }

  export async function getDepartments(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    company_id?: number;
    is_active?: boolean;
    manager_id?: number;
    sort_by?: string;
    sort_order?: string;
  }): Promise<DepartmentListResponse> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return request<DepartmentListResponse>(`/departments/?${query}`);
  }

  export async function getDepartment(id: number): Promise<Department> {
    return request<Department>(`/departments/${id}`);
  }

  export async function createDepartment(data: DepartmentCreate): Promise<Department> {
    return request<Department>('/departments/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  export async function updateDepartment(id: number, data: DepartmentUpdate): Promise<Department> {
    return request<Department>(`/departments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  export async function deleteDepartment(id: number): Promise<void> {
    await request(`/departments/${id}`, {
      method: 'DELETE',
    });
  }

  export async function getDepartmentStats(): Promise<DepartmentStats> {
    return request<DepartmentStats>('/departments/stats');
  }

  // Device Management API functions
  export interface DeviceInfo {
    id: number;
    user_id: number;
    device_name?: string;
    device_type?: string;
    browser?: string;
    os?: string;
    ip_address?: string;
    user_agent?: string;
    is_current?: boolean;
    is_active: boolean;
    last_active_at?: string;
    created_at?: string;
  }

  export interface DeviceListResponse {
    items: DeviceOut[];
    total: number;
    page: number;
    page_size: number;
  }

  export interface DeviceStats {
    total_devices: number;
    active_devices: number;
    revoked_devices?: number;
    expiring_soon?: number;
    device_type_breakdown: Record<string, number>;
    browser_breakdown: Record<string, number>;
  }

  export interface DeviceRevokeResponse {
    message: string;
    device_id: number;
    revoked: boolean;
  }

  export async function getDevices(options: {
    skip?: number;
    limit?: number;
    include_revoked?: boolean;
  } = {}): Promise<DeviceListResponse> {
    const params = new URLSearchParams();
    params.append('skip', String(options.skip ?? 0));
    params.append('limit', String(options.limit ?? 50));
    if (options.include_revoked !== undefined) {
      params.append('include_revoked', String(options.include_revoked));
    }
    return request<DeviceListResponse>(`/devices/?${params.toString()}`);
  }

  export async function getDeviceStats(): Promise<DeviceStats> {
    return request<DeviceStats>('/devices/stats');
  }

  export async function markDeviceCurrent(device_id: number): Promise<DeviceRevokeResponse> {
    return request<DeviceRevokeResponse>('/devices/current', {
      method: 'POST',
      body: JSON.stringify({ device_id }),
    });
  }

  export interface DeviceOut {
    id: number;
    user_id: number;
    device_name?: string;
    device_type?: string;
    browser?: string;
    os?: string;
    client_ip?: string;
    is_current?: boolean;
    is_revoked?: boolean;
    is_active?: boolean;
    expires_at?: string;
    created_at?: string;
    last_used_at?: string;
    user_agent?: string;
  }

  export async function revokeDevice(device_id: number): Promise<DeviceRevokeResponse> {
    return request<DeviceRevokeResponse>('/devices/revoke', {
      method: 'POST',
      body: JSON.stringify({ device_id }),
    });
  }

  export async function revokeAllDevices(): Promise<{ message: string; revoked_count: number }> {
    return request<{ message: string; revoked_count: number }>('/devices/revoke-all', {
      method: 'POST',
    });
  }

  // Two-Factor Authentication API functions
  export async function get2FAStatus(): Promise<{ is_2fa_enabled: boolean }> {
    return getTwoFactorStatus();
  }

  export async function getBackupCodesRemaining(): Promise<{ remaining: number }> {
    return request<{ remaining: number }>('/two-factor/backup-codes-remaining');
  }

  export interface TwoFactorSetupResponse {
    secret: string;
    qr_code_url: string;
    otpauth_url?: string;
    backup_codes: string[];
  }

  export interface TwoFactorVerifyResponse {
    message: string;
    verified: boolean;
  }

  export interface TwoFactorDisableResponse {
    message: string;
    disabled: boolean;
  }

  export interface BackupCodesResponse {
    backup_codes: string[];
  }

  export async function setup2FA(): Promise<TwoFactorSetupResponse> {
    return request<TwoFactorSetupResponse>('/two-factor/setup', {
      method: 'POST',
    });
  }

  export async function verify2FA(totp_code: string): Promise<TwoFactorVerifyResponse> {
    return request<TwoFactorVerifyResponse>('/two-factor/verify', {
      method: 'POST',
      body: JSON.stringify({ totp_code }),
    });
  }

  export async function disable2FA(password: string): Promise<TwoFactorDisableResponse> {
    return request<TwoFactorDisableResponse>('/two-factor/disable', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
  }

  export async function regenerateBackupCodes(): Promise<BackupCodesResponse> {
    return request<BackupCodesResponse>('/two-factor/backup-codes', {
      method: 'POST',
    });
  }

  export async function getTwoFactorStatus(): Promise<{ is_2fa_enabled: boolean }> {
    return request<{ is_2fa_enabled: boolean }>('/two-factor/status');
  }

  // Security Dashboard API functions
  export interface SecurityDashboardData {
    security_score: number;
    total_users: number;
    users_with_2fa: number;
    locked_accounts: number;
    users_with_failed_logins: number;
    active_sessions: number;
    failed_logins_24h: number;
    failed_logins_7d: number;
    account_lockouts_30d: number;
    password_changes_30d: number;
    two_fa_enabled_30d: number;
    suspicious_ips_count: number;
    recent_events: Array<{
      id: number;
      action: string;
      user_id?: number;
      ip_address?: string;
      created_at: string;
      details?: Record<string, unknown>;
    }>;
  }

  export interface SecurityScoreResponse {
    security_score: number;
    recommendations: string[];
  }

    export async function getSecurityDashboardSummary(): Promise<SecurityDashboardData> {
    return request<SecurityDashboardData>('/security');
  }

  export async function getSecurityScore(): Promise<SecurityScoreResponse> {
    return request<SecurityScoreResponse>('/security/score');
  }

  // ==================== Logging History API ====================

  export interface LogEntry {
    id: number;
    level: string;
    logger_name: string;
    message: string;
    module?: string;
    func_name?: string;
    line_no?: number;
    pathname?: string;
    thread_name?: string;
    process?: string;
    timestamp: string;
    user_id?: number | null;
    ip_address?: string | null;
    user_agent?: string | null;
    extra_data?: Record<string, unknown> | null;
  }

  export interface LogStats {
    total_entries: number;
    by_level: Record<string, number>;
    top_loggers: Array<{ logger_name: string; count: number }>;
    oldest_entry?: string | null;
    newest_entry?: string | null;
  }

  export interface LogEntryListResponse {
    items: LogEntry[];
    total: number;
    page: number;
    page_size: number;
  }

  export interface LogCleanupResponse {
    message: string;
    deleted_count: number;
  }

  export async function getLogEntries(params?: {
    skip?: number;
    limit?: number;
    level?: string;
    logger_name?: string;
    search?: string;
  }): Promise<LogEntryListResponse> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return request<LogEntryListResponse>(`/logging/?${query}`);
  }

  export async function getLogStats(): Promise<LogStats> {
    return request<LogStats>('/logging/stats');
  }

  export async function cleanupLogs(olderThanDays: number): Promise<LogCleanupResponse> {
    return request<LogCleanupResponse>(
      `/logging/?older_than_days=${olderThanDays}`,
      { method: 'DELETE' },
    );
  }

  // ==================== Logging Configuration API ====================

  export interface LoggingConfiguration {
    id: number;
    company_id: number;
    log_level: string;
    enable_database_logging: boolean;
    enable_console_logging: boolean;
    log_format: string;
    retention_days: number;
    created_at?: string | null;
    updated_at?: string | null;
  }

  export interface LoggingConfigurationUpdate {
    log_level?: string;
    enable_database_logging?: boolean;
    enable_console_logging?: boolean;
    log_format?: string;
    retention_days?: number;
  }

  export interface LoggingConfigurationCreate {
    company_id: number;
    log_level?: string;
    enable_database_logging?: boolean;
    enable_console_logging?: boolean;
    log_format?: string;
    retention_days?: number;
  }

  export async function getLoggingConfiguration(): Promise<LoggingConfiguration> {
    return request<LoggingConfiguration>('/logging-config/');
  }

  export async function updateLoggingConfiguration(
    data: LoggingConfigurationUpdate,
  ): Promise<LoggingConfiguration> {
    return request<LoggingConfiguration>('/logging-config/', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  export async function createLoggingConfiguration(
    data: LoggingConfigurationCreate,
  ): Promise<LoggingConfiguration> {
    return request<LoggingConfiguration>('/logging-config/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  export async function deleteLoggingConfiguration(): Promise<void> {
    await request<void>('/logging-config/', {
      method: 'DELETE',
    });
  }

  // ==================== Documentation / Knowledge Base API ====================

  export interface Document {
    id: number;
    title: string;
    slug?: string | null;
    summary?: string | null;
    content?: string | null;
    category?: string | null;
    tags?: string | null;
    status?: string | null;
    company_id?: number | null;
    version?: number | null;
    author_id?: number | null;
    is_active?: boolean;
    created_at?: string | null;
    updated_at?: string | null;
    author_name?: string | null;
    company_name?: string | null;
  }

  export interface DocumentCreate {
    title: string;
    slug?: string | null;
    summary?: string | null;
    content?: string | null;
    category?: string | null;
    tags?: string | null;
    status?: string | null;
    company_id?: number | null;
  }

  export interface DocumentUpdate {
    title?: string;
    slug?: string | null;
    summary?: string | null;
    content?: string | null;
    category?: string | null;
    tags?: string | null;
    status?: string | null;
    company_id?: number | null;
    is_active?: boolean;
  }

  export interface DocumentStats {
    total_documents: number;
    published_documents: number;
    draft_documents: number;
    archived_documents: number;
    total_companies_with_documents: number;
    avg_documents_per_company?: number | null;
    documents_by_category: Record<string, number>;
    documents_by_status: Record<string, number>;
  }

  export interface DocumentListResponse {
    items: Document[];
    total: number;
    page: number;
    page_size: number;
  }

  export async function getDocuments(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    category?: string;
    status?: string;
    company_id?: number;
    author_id?: number;
    is_active?: boolean;
    sort_by?: string;
    sort_order?: string;
  }): Promise<DocumentListResponse> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return request<DocumentListResponse>(`/documents/?${query}`);
  }

  export async function getDocumentStats(): Promise<DocumentStats> {
    return request<DocumentStats>('/documents/stats');
  }

  export async function getDocument(id: number): Promise<Document> {
    return request<Document>(`/documents/${id}`);
  }

  export async function createDocument(data: DocumentCreate): Promise<Document> {
    return request<Document>('/documents/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  export async function updateDocument(id: number, data: DocumentUpdate): Promise<Document> {
    return request<Document>(`/documents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  export async function deleteDocument(id: number): Promise<void> {
    await request(`/documents/${id}`, {
      method: 'DELETE',
    });
  }

  export async function publishDocument(id: number): Promise<Document> {
    return request<Document>(`/documents/${id}/publish`, {
      method: 'POST',
    });
  }

  // ==================== Organization Settings API ====================

  export interface OrganizationSettings {
    id: number;
    company_id: number;
    timezone: string;
    date_format: string;
    time_format: string;
    language: string;
    currency: string;
    password_min_length: number;
    password_require_uppercase: boolean;
    password_require_lowercase: boolean;
    password_require_numbers: boolean;
    password_require_special_chars: boolean;
    password_expiry_days: number;
    session_timeout_minutes: number;
    enforce_2fa: boolean;
    max_login_attempts: number;
    email_notifications_enabled: boolean;
    notify_on_user_creation: boolean;
    notify_on_user_deletion: boolean;
    notify_on_password_reset: boolean;
    notify_on_security_alerts: boolean;
    notify_on_subscription_changes: boolean;
    primary_color: string;
    logo_url?: string | null;
    custom_css?: string | null;
    enable_user_registration: boolean;
    enable_api_access: boolean;
    enable_audit_logs: boolean;
    enable_data_export: boolean;
    custom_settings?: Record<string, unknown> | null;
    created_at?: string | null;
    updated_at?: string | null;
  }

  export interface OrganizationSettingsUpdate {
    timezone?: string;
    date_format?: string;
    time_format?: string;
    language?: string;
    currency?: string;
    password_min_length?: number;
    password_require_uppercase?: boolean;
    password_require_lowercase?: boolean;
    password_require_numbers?: boolean;
    password_require_special_chars?: boolean;
    password_expiry_days?: number;
    session_timeout_minutes?: number;
    enforce_2fa?: boolean;
    max_login_attempts?: number;
    email_notifications_enabled?: boolean;
    notify_on_user_creation?: boolean;
    notify_on_user_deletion?: boolean;
    notify_on_password_reset?: boolean;
    notify_on_security_alerts?: boolean;
    notify_on_subscription_changes?: boolean;
    primary_color?: string;
    logo_url?: string | null;
    custom_css?: string | null;
    enable_user_registration?: boolean;
    enable_api_access?: boolean;
    enable_audit_logs?: boolean;
    enable_data_export?: boolean;
    custom_settings?: Record<string, unknown> | null;
  }

  export async function getOrganizationSettings(): Promise<OrganizationSettings> {
    return request<OrganizationSettings>('/organization-settings/');
  }

  export async function updateOrganizationSettings(data: OrganizationSettingsUpdate): Promise<OrganizationSettings> {
    return request<OrganizationSettings>('/organization-settings/', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  export async function getDefaultOrganizationSettings(): Promise<OrganizationSettings> {
    return request<OrganizationSettings>('/organization-settings/defaults');
  }

  // ==================== Password Policy API ====================

  export interface PasswordRequirement {
    id: string;
    label: string;
    key: string;
    value: unknown;
    met: boolean;
  }

  export interface PasswordPolicyResponse {
    min_length: number;
    require_uppercase: boolean;
    require_lowercase: boolean;
    require_numbers: boolean;
    require_special_chars: boolean;
    expiry_days: number;
    requirements: PasswordRequirement[];
  }

  export interface PasswordPolicyUpdate {
    min_length?: number;
    require_uppercase?: boolean;
    require_lowercase?: boolean;
    require_numbers?: boolean;
    require_special_chars?: boolean;
    expiry_days?: number;
  }

  export interface PasswordValidationResponse {
    valid: boolean;
    errors: string[];
    requirements: PasswordRequirement[];
  }

  export async function getPasswordPolicy(): Promise<PasswordPolicyResponse> {
    return request<PasswordPolicyResponse>('/password-policy/');
  }

  export async function validatePassword(password: string): Promise<PasswordValidationResponse> {
    return request<PasswordValidationResponse>('/password-policy/validate', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
  }

  export async function getDefaultPasswordPolicy(): Promise<PasswordPolicyResponse> {
    return request<PasswordPolicyResponse>('/password-policy/defaults');
  }

  export async function updatePasswordPolicy(data: PasswordPolicyUpdate): Promise<PasswordPolicyResponse> {
    return request<PasswordPolicyResponse>('/password-policy/', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

