import request from './request'

export const getIrrigationDecision = (plotId) => request.get('/irrigation/decision', { params: { plotId } })
export const controlIrrigation = (data) => request.post('/irrigation/control', data)
