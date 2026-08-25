import request from './request'

export const getWeatherForecast = (params) => request.get('/weather/forecast', { params })
