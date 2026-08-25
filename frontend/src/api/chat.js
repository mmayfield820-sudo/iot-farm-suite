import request from './request'

export const sendChatMessage = (sessionId, data) => request.post(`/chat/sessions/${sessionId}/messages`, data)
