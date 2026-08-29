import { farmerAlerts, farmerIrrigationRecords, farmerPlots } from './farmerData'

// 管理员端与农户端共用同一套橙园主数据，避免离线演示时出现两个数据口径。
export const mockPlots = farmerPlots
export const mockAlerts = farmerAlerts
export const mockIrrigationRecords = farmerIrrigationRecords
