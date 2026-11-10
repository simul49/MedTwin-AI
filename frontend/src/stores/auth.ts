import { defineStore } from 'pinia';
import { auth as authApi } from '@/api/endpoints';
import type { Role, User } from '@/api/types';

interface State {
  user: User | null;
  loading: boolean;
  ready: boolean;
}

export const useAuthStore = defineStore('auth', {
  state: (): State => ({ user: null, loading: false, ready: false }),

  getters: {
    isAuthenticated: (state): boolean => state.user !== null,
    role: (state): Role | null => state.user?.role ?? null,
    isPatient: (state): boolean => state.user?.role === 'PATIENT',
    isDoctor: (state): boolean => state.user?.role === 'DOCTOR',
    isAdmin: (state): boolean => state.user?.role === 'ADMIN',
    homePath(): string {
      if (this.isPatient) return '/patient';
      if (this.isDoctor) return '/doctor';
      if (this.isAdmin) return '/admin';
      return '/';
    },
  },

  actions: {
    async bootstrap() {
      if (this.ready) return;
      this.loading = true;
      try {
        this.user = await authApi.me();
      } catch {
        this.user = null;
      } finally {
        this.loading = false;
        this.ready = true;
      }
    },

    async login(email: string, password: string) {
      this.loading = true;
      try {
        this.user = await authApi.login(email, password);
        this.ready = true;
        return this.user;
      } finally {
        this.loading = false;
      }
    },

    async register(payload: Record<string, unknown>) {
      this.loading = true;
      try {
        this.user = await authApi.register(payload);
        this.ready = true;
        return this.user;
      } finally {
        this.loading = false;
      }
    },

    async logout() {
      try {
        await authApi.logout();
      } finally {
        this.user = null;
        this.ready = true;
      }
    },

    async refresh() {
      try {
        this.user = await authApi.me();
      } catch {
        this.user = null;
      }
    },

    async updateProfile(payload: Record<string, unknown>) {
      if (!this.user) return null;
      this.user = await authApi.updateMe(payload);
      return this.user;
    },
  },
});
