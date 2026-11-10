import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import PublicLayout from '@/views/layouts/PublicLayout.vue';
import AppLayout from '@/views/layouts/AppLayout.vue';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: PublicLayout,
    children: [
      { path: '', name: 'home', component: () => import('@/views/public/HomeView.vue') },
      { path: 'about', name: 'about', component: () => import('@/views/public/AboutView.vue') },
      { path: 'solutions', name: 'solutions', component: () => import('@/views/public/SolutionsView.vue') },
      { path: 'how-it-works', name: 'how-it-works', component: () => import('@/views/public/HowItWorksView.vue') },
      { path: 'research', name: 'research', component: () => import('@/views/public/ResearchView.vue') },
      { path: 'trust-safety', name: 'trust-safety', component: () => import('@/views/public/TrustSafetyView.vue') },
      { path: 'privacy', name: 'privacy', component: () => import('@/views/public/PrivacyView.vue') },
      { path: 'terms', name: 'terms', component: () => import('@/views/public/TermsView.vue') },
      { path: 'medical-disclaimer', name: 'medical-disclaimer', component: () => import('@/views/public/MedicalDisclaimerView.vue') },
      { path: 'contact', name: 'contact', component: () => import('@/views/public/ContactView.vue') },
      { path: 'login', name: 'login', component: () => import('@/views/public/LoginView.vue') },
      { path: 'register', name: 'register', component: () => import('@/views/public/RegisterView.vue') },
    ],
  },
  {
    path: '/patient',
    component: AppLayout,
    meta: { requiresAuth: true, role: 'PATIENT' },
    children: [
      { path: '', name: 'patient-overview', component: () => import('@/views/patient/PatientOverview.vue') },
      { path: 'twin', name: 'patient-twin', component: () => import('@/views/patient/PatientTwin.vue') },
      { path: 'records', name: 'patient-records', component: () => import('@/views/patient/PatientRecords.vue') },
      { path: 'documents', name: 'patient-documents', component: () => import('@/views/patient/PatientDocuments.vue') },
      { path: 'assistant', name: 'patient-assistant', component: () => import('@/views/patient/PatientAssistant.vue') },
      { path: 'recommendations', name: 'patient-recommendations', component: () => import('@/views/patient/PatientRecommendations.vue') },
      { path: 'consent', name: 'patient-consent', component: () => import('@/views/patient/PatientConsent.vue') },
      { path: 'appointments', name: 'patient-appointments', component: () => import('@/views/patient/PatientAppointments.vue') },
      { path: 'messages', name: 'patient-messages', component: () => import('@/views/patient/PatientMessages.vue') },
      { path: 'notifications', name: 'patient-notifications', component: () => import('@/views/patient/PatientNotifications.vue') },
      { path: 'settings', name: 'patient-settings', component: () => import('@/views/patient/PatientSettings.vue') },
    ],
  },
  {
    path: '/doctor',
    component: AppLayout,
    meta: { requiresAuth: true, role: 'DOCTOR' },
    children: [
      { path: '', name: 'doctor-overview', component: () => import('@/views/doctor/DoctorOverview.vue') },
      { path: 'patients', name: 'doctor-patients', component: () => import('@/views/doctor/DoctorPatients.vue') },
      { path: 'patients/:id', name: 'doctor-patient-detail', component: () => import('@/views/doctor/DoctorPatientDetail.vue') },
      { path: 'appointments', name: 'doctor-appointments', component: () => import('@/views/doctor/DoctorAppointments.vue') },
      { path: 'messages', name: 'doctor-messages', component: () => import('@/views/doctor/DoctorMessages.vue') },
      { path: 'safety', name: 'doctor-safety', component: () => import('@/views/doctor/DoctorSafety.vue') },
      { path: 'settings', name: 'doctor-settings', component: () => import('@/views/doctor/DoctorSettings.vue') },
    ],
  },
  {
    path: '/admin',
    component: AppLayout,
    meta: { requiresAuth: true, role: 'ADMIN' },
    children: [
      { path: '', name: 'admin-overview', component: () => import('@/views/admin/AdminOverview.vue') },
      { path: 'users', name: 'admin-users', component: () => import('@/views/admin/AdminUsers.vue') },
      { path: 'consent', name: 'admin-consent', component: () => import('@/views/admin/AdminConsent.vue') },
      { path: 'knowledge', name: 'admin-knowledge', component: () => import('@/views/admin/AdminKnowledge.vue') },
      { path: 'audit', name: 'admin-audit', component: () => import('@/views/admin/AdminAudit.vue') },
      { path: 'flags', name: 'admin-flags', component: () => import('@/views/admin/AdminFlags.vue') },
      { path: 'health', name: 'admin-health', component: () => import('@/views/admin/AdminHealth.vue') },
    ],
  },
  { path: '/forbidden', name: 'forbidden', component: () => import('@/views/errors/ForbiddenView.vue') },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/errors/NotFoundView.vue') },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (!auth.ready) await auth.bootstrap();

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } };
  }

  const role = to.meta.role as string | undefined;
  if (role && auth.role !== role) {
    return { name: 'forbidden' };
  }

  // Signed-in users do not need the login/register pages.
  if ((to.name === 'login' || to.name === 'register') && auth.isAuthenticated) {
    return { path: auth.homePath };
  }

  return true;
});
