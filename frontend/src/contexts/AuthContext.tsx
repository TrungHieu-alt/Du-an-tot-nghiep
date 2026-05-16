import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  authApi,
  ApiError,
  type CandidateProfile,
  type MeResponse,
  type Organization,
  type RecruiterProfile,
  type Role,
  type UserSummary,
} from "@/lib/api";

// ── State shape ───────────────────────────────────────────────────────────────

interface AuthState {
  token: string | null;
  user: UserSummary | null;
  candidateProfile: CandidateProfile | null;
  recruiterProfile: RecruiterProfile | null;
  organization: Organization | null;
  /** true while the initial token-restore /me call is in flight */
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, role: Role) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<MeResponse | null>;
}

// ── Storage helpers ───────────────────────────────────────────────────────────

const TOKEN_KEY = "jc_token";

function loadToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function saveToken(t: string) {
  try {
    localStorage.setItem(TOKEN_KEY, t);
  } catch {
    // ignore storage errors
  }
}

function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore
  }
}

// ── Context ───────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    token: null,
    user: null,
    candidateProfile: null,
    recruiterProfile: null,
    organization: null,
    loading: true,
  });

  // Restore session on mount
  useEffect(() => {
    const stored = loadToken();
    if (!stored) {
      setState((s) => ({ ...s, loading: false }));
      return;
    }
    authApi
      .me(stored)
      .then((me) => {
        setState({
          token: stored,
          user: me.user,
          candidateProfile: me.candidate_profile,
          recruiterProfile: me.recruiter_profile,
          organization: me.organization,
          loading: false,
        });
      })
      .catch((err) => {
        // 401 means token is expired/invalid — clear it
        if (err instanceof ApiError && err.status === 401) {
          clearToken();
        }
        setState((s) => ({ ...s, token: null, user: null, loading: false }));
      });
  }, []);

  const applyAuth = useCallback((token: string, me: MeResponse) => {
    saveToken(token);
    setState({
      token,
      user: me.user,
      candidateProfile: me.candidate_profile,
      recruiterProfile: me.recruiter_profile,
      organization: me.organization,
      loading: false,
    });
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const auth = await authApi.login(email, password);
      const me = await authApi.me(auth.access_token);
      applyAuth(auth.access_token, me);
    },
    [applyAuth],
  );

  const register = useCallback(
    async (email: string, password: string, role: Role) => {
      const auth = await authApi.register(email, password, role);
      const me = await authApi.me(auth.access_token);
      applyAuth(auth.access_token, me);
    },
    [applyAuth],
  );

  const logout = useCallback(async () => {
    if (state.token) {
      await authApi.logout(state.token).catch(() => {
        // best-effort
      });
    }
    clearToken();
    setState({
      token: null,
      user: null,
      candidateProfile: null,
      recruiterProfile: null,
      organization: null,
      loading: false,
    });
  }, [state.token]);

  const refreshMe = useCallback(async () => {
    if (!state.token) return null;
    try {
      const me = await authApi.me(state.token);
      setState((s) => ({
        ...s,
        user: me.user,
        candidateProfile: me.candidate_profile,
        recruiterProfile: me.recruiter_profile,
        organization: me.organization,
      }));
      return me;
    } catch {
      return null;
    }
  }, [state.token]);

  const value = useMemo<AuthContextValue>(
    () => ({ ...state, login, register, logout, refreshMe }),
    [state, login, register, logout, refreshMe],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
