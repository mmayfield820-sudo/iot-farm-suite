import request from './request'

export const getChatHealth = () => request.get('/chat/health')
export const sendChatMessage = (sessionId, data) => request.post(
  `/chat/sessions/${sessionId}/messages`,
  data,
  { timeout: Number(import.meta.env.VITE_AI_REQUEST_TIMEOUT_MS || 120000) },
)
