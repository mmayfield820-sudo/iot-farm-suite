import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { login as loginApi } from '@/api/auth'

const STORAGE_KEY = 'smart-agriculture-user'
const APPROVED_ACCOUNT_KEY = 'smart-agriculture-approved-accounts'
export const ROLE_HOME = { farmer: '/farmer/dashboard', farmAdmin: '/farm/dashboard', systemAdmin: '/admin/dashboard' }
export const ROLE_LABEL = { farmer: '农户', farmAdmin: '农场管理员', systemAdmin: '系统管理员' }
const ROLE_CODE_MAP = { farmer: 'farmer', FARMER: 'farmer', 农户: 'farmer', farm_admin: 'farmAdmin', FARM_ADMIN: 'farmAdmin', farmAdmin: 'farmAdmin', 农场管理员: 'farmAdmin', system_admin: 'systemAdmin', SYSTEM_ADMIN: 'systemAdmin', systemAdmin: 'systemAdmin', 系统管理员: 'systemAdmin' }
const asArray = (value) => Array.isArray(value) ? value : typeof value === 'string' ? value.split(',').map((item) => item.trim()).filter(Boolean) : []

// 后端接入前，用固定账号模拟“一个账号对应多个角色”的登录结果。
const mockAccounts = [
  {
    id: 'U001',
    username: 'demo_admin',
    password: 'DemoPass123!',
    displayName: '张园长',
    email: 'admin@orange.local',
    status: 'normal',
    roles: ['farmAdmin'],
    permissions: ['*'],
    accessiblePlots: [],
    roleScopes: { farmAdmin: { farmIds: ['F001', 'F002'] } },
  },
  {
    id: 'U002',
    username: 'demo_farmer',
    password: 'DemoPass123!',
    displayName: '李果农',
    email: 'farmer@orange.local',
    status: 'normal',
    roles: ['farmer'],
    permissions: ['*'],
    accessiblePlots: ['P001', 'P002', 'P003', 'P004'],
    roleScopes: { farmer: { plotIds: ['P001', 'P002', 'P003', 'P004'] } },
  },
  {
    id: 'U003',
    username: 'demo_system',
    password: 'DemoPass123!',
    displayName: '王管理员',
    email: 'system@orange.local',
    status: 'normal',
    roles: ['systemAdmin'],
    permissions: ['*'],
    accessiblePlots: [],
    roleScopes: { systemAdmin: { global: true } },
  }
]

function normalizeUser(raw = {}) {
  const rawRoles = asArray(raw.roles || raw.roleList || raw.role_list || raw.role)
  const roles = [...new Set(rawRoles.map((item) => ROLE_CODE_MAP[item?.roleCode || item?.role_code || item?.code || item]).filter(Boolean))]
  const requestedActiveRole = ROLE_CODE_MAP[raw.activeRole || raw.active_role]
  const activeRole = roles.includes(requestedActiveRole) ? requestedActiveRole : roles[0] || ''
  const assignmentActive = (item) => {
    if (item?.active === false || item?.Active === false) return false
    if (!item?.expiresAt && !item?.expires_at) return true
    return new Date(item.expiresAt || item.expires_at).getTime() > Date.now()
  }
  const farmerAssignments = (raw.userPlotRoles || raw.user_plot_roles || []).filter(assignmentActive)
  const farmAssignments = (raw.userFarmRoles || raw.user_farm_roles || []).filter(assignmentActive)
  const suppliedScopes = raw.roleScopes || raw.role_scopes || {}
  const plotIds = asArray(suppliedScopes.farmer?.plotIds || suppliedScopes.farmer?.plot_ids || raw.accessiblePlots || raw.plotIds || raw.plot_ids || farmerAssignments.map((item) => item.plotId || item.plot_id))
  const farmIds = asArray(suppliedScopes.farmAdmin?.farmIds || suppliedScopes.farmAdmin?.farm_ids || raw.farmIds || raw.farm_ids || farmAssignments.map((item) => item.farmId || item.farm_id))
  const permissions = (raw.permissions || []).map((item) => {
    if (typeof item === 'string') return item
    const code = item?.permissionCode || item?.permission_code || item?.code
    const resource = item?.resourceType || item?.resource_type || item?.resource
    const action = item?.actionType || item?.action_type || item?.action
    return code || (resource && action ? `${resource}:${action}` : '')
  }).filter(Boolean)
  return {
    id: String(raw.id || raw.userId || raw.user_id || ''),
    username: raw.username || '',
    displayName: raw.displayName || raw.realName || raw.username || '',
    email: raw.email || '',
    phone: raw.phone || raw.Phone || '',
    status: raw.active === false || raw.Active === false ? 'disabled' : raw.status || 'normal',
    roles,
    permissions,
    accessiblePlots: plotIds.map(String),
    roleScopes: {
      ...(roles.includes('farmer') ? { farmer: { plotIds: plotIds.map(String) } } : {}),
      ...(roles.includes('farmAdmin') ? { farmAdmin: { farmIds: farmIds.map(String) } } : {}),
      ...(roles.includes('systemAdmin') ? { systemAdmin: { global: true } } : {}),
    },
    activeRole,
  }
}

export const useUserStore = defineStore('user', () => {
  let saved = null
  try { saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null') } catch { localStorage.removeItem(STORAGE_KEY) }
  const refreshedMock = import.meta.env.VITE_USE_MOCK === 'true' && saved
    ? mockAccounts.find((item) => item.id === saved.id)
    : null
  const restoredProfile = refreshedMock ? { ...refreshedMock, activeRole: saved.activeRole } : saved
  const user = ref(restoredProfile ? normalizeUser(restoredProfile) : null)
  const roles = computed(() => user.value?.roles || [])
  const role = computed(() => user.value?.activeRole || '')
  const isLoggedIn = computed(() => Boolean(user.value?.id && roles.value.length))
  const permissions = computed(() => user.value?.permissions || [])

  function persistUser() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(user.value))
  }

  async function login(payload) {
    let profile
    let token

    if (import.meta.env.VITE_USE_MOCK === 'true') {
      let approvedAccounts = []
      try { approvedAccounts = JSON.parse(localStorage.getItem(APPROVED_ACCOUNT_KEY) || '[]') } catch { approvedAccounts = [] }
      const account = [...mockAccounts, ...approvedAccounts].find((item) => item.username === payload.username.trim() && item.password === payload.password)
      if (!account) throw new Error('用户名或密码错误')
      const { password: _password, ...safeAccount } = account
      profile = safeAccount
      token = `mock-token-${account.id}`
    } else {
      const response = await loginApi({ username: payload.username.trim(), password: payload.password })
      profile = response.user || response.data?.user || response.data || response
      token = response.token || response.data?.token
    }

    user.value = normalizeUser(profile)
    if (['disabled', '禁用'].includes(user.value.status)) {
      user.value = null
      throw new Error('该账号已被禁用，请联系系统管理员')
    }
    if (!user.value.roles.length) {
      user.value = null
      throw new Error('该账号尚未分配角色，请联系系统管理员')
    }
    persistUser()
    if (token) localStorage.setItem('smart-agriculture-token', token)
    return ROLE_HOME[user.value.activeRole]
  }

  function switchRole(nextRole) {
    if (!roles.value.includes(nextRole)) throw new Error('当前账号没有该角色的访问权限')
    user.value.activeRole = nextRole
    persistUser()
    return ROLE_HOME[nextRole]
  }

  function can(resource, action) {
    if (permissions.value.includes('*')) return true
    if (!permissions.value.length) return isLoggedIn.value
    const actionAliases = { read: ['read', 'view', 'select', '查看', '查询'], modify: ['modify', 'update', 'edit', '修改', '更新'], create: ['create', 'insert', 'add', '新增', '创建'], delete: ['delete', 'remove', '删除'], control: ['control', 'execute', '控制', '执行'] }
    const resources = [resource, resource.replaceAll('_', ''), resource.replaceAll('_', '-')]
    const actions = actionAliases[action] || [action]
    const normalized = permissions.value.map((item) => String(item).toLowerCase())
    return resources.some((resourceName) => actions.some((actionName) => [`${resourceName}:${actionName}`, `${resourceName}.${actionName}`, `${resourceName}_${actionName}`, `${resourceName}:*`, `${resourceName}.*`].some((candidate) => normalized.includes(candidate.toLowerCase()))))
  }

  function logout() {
    user.value = null
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem('smart-agriculture-token')
  }

  return { user, roles, role, permissions, isLoggedIn, login, switchRole, can, logout }
})
