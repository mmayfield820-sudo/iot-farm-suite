import request from './request'

export const getPlotOverview = () => request.get('/plots/overview')

export const getPlotDetail = (plotId) => request.get(`/plots/${plotId}/detail`)

export const getPlotList = (params) => request.get('/plots', { params })

