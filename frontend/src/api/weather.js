import request from './request'

export const getWeatherForecast = (plotId) => request.get('/weather/forecast', { params: { plotId } })
