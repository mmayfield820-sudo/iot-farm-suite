import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { approveRegistration, getRegistrationApplications, register as registerApi, rejectRegistration } from '@/api/auth'
import { formatDateTime, unwrapList } from '@/utils/dataAdapters'

const APPLICATION_KEY = 'smart-agriculture-registration-applications'
const APPROVED_ACCOUNT_KEY = 'smart-agriculture-approved-accounts'
const isMock = import.meta.env.VITE_USE_MOCK === 'true'

const readStorage = (key, fallback = []) => {
  try { return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback)) }
  catch { return fallback }
}

const nowText = () => formatDateTime(new Date())
const statusText = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
const normalizeApplication = (item) => ({
  ...item,
  id: String(item.id || item.applicationId || item.application_id),
  roles: item.roles || item.roleCodes || item.role_codes || [],
  plotIds: (item.plotIds || item.plot_ids || []).map(String),
  farmIds: (item.farmIds || item.farm_ids || []).map(String),
  status: statusText[item.status] || item.status || '待审核',
  createdAt: item.createdAt || item.created_at || '',
  reviewedAt: item.reviewedAt || item.reviewed_at || '',
  rejectReason: item.rejectReason || item.reject_reason || '',
})

export const useRegistrationStore = defineStore('registration', () => {
  const applications = ref(isMock ? readStorage(APPLICATION_KEY) : [])
  const pendingCount = computed(() => applications.value.filter((item) => item.status === '待审核').length)

  function persist() {
    localStorage.setItem(APPLICATION_KEY, JSON.stringify(applications.value))
  }

  async function loadApplications() {
    if (isMock) return
    const response = await getRegistrationApplications()
    applications.value = unwrapList(response).map(normalizeApplication)
  }

  async function submitApplication(payload) {
    const username = payload.username.trim()
    const existing = applications.value.find((item) => item.username === username)
    if (existing?.status === '待审核') throw new Error('该用户名已有待审核申请，请勿重复提交')
    if (existing?.status === '已通过') throw new Error('该用户名已注册，请直接登录')

    let application = {
      ...payload,
      id: existing?.id || `REG${Date.now()}`,
      username,
      status: '待审核',
      createdAt: nowText(),
      reviewedAt: '',
      rejectReason: '',
    }
    if (!isMock) {
      const response = await registerApi({
        username: payload.username,
        password: payload.password,
        real_name: payload.realName,
        email: payload.email,
        phone: payload.phone,
        role_codes: payload.roles,
        plot_ids: payload.plotIds,
        farm_ids: payload.farmIds,
      })
      application = { ...application, ...normalizeApplication(response?.data || response), password: undefined }
    }
    if (existing) Object.assign(existing, application)
    else applications.value.unshift(application)
    if (isMock) persist()
    return application
  }

  async function approveApplication(id) {
    const application = applications.value.find((item) => item.id === id)
    if (!application || application.status !== '待审核') return null
    if (!isMock) await approveRegistration(id)
    application.status = '已通过'
    application.reviewedAt = nowText()
    if (!isMock) return { application, account: null }
    const approvedAccounts = readStorage(APPROVED_ACCOUNT_KEY)
    const account = {
      id: `U${Date.now()}`,
      username: application.username,
      password: application.password,
      displayName: application.realName,
      email: application.email,
      phone: application.phone,
      status: 'normal',
      roles: application.roles,
      accessiblePlots: application.plotIds,
      roleScopes: {
        ...(application.roles.includes('farmer') ? { farmer: { plotIds: application.plotIds } } : {}),
        ...(application.roles.includes('farmAdmin') ? { farmAdmin: { farmIds: application.farmIds } } : {}),
      },
    }
    approvedAccounts.push(account)
    localStorage.setItem(APPROVED_ACCOUNT_KEY, JSON.stringify(approvedAccounts))
    if (isMock) persist()
    return { application, account }
  }

  async function rejectApplication(id, reason) {
    const application = applications.value.find((item) => item.id === id)
    if (!application || application.status !== '待审核') return
    if (!isMock) await rejectRegistration(id, { reason })
    application.status = '已拒绝'
    application.rejectReason = reason
    application.reviewedAt = nowText()
    if (isMock) persist()
  }

  return { applications, pendingCount, loadApplications, submitApplication, approveApplication, rejectApplication }
})
