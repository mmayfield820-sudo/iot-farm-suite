from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from ..access import parse_resource_id, require_plot_access
from ..auth import current_user
from ..db import engine, utc_isoformat


router = APIRouter(prefix="/api", tags=["plot-timeline"])


@router.get("/plots/{plot_id}/timeline")
def plot_timeline(
    plot_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    numeric_id = parse_resource_id(plot_id, "P")
    require_plot_access(numeric_id, user)
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT event_type, event_id, title, detail, event_at FROM (
                  SELECT 'TASK' event_type, CONCAT('TASK', task_id) event_id,
                    task_name title,
                    CONCAT(
                      COALESCE(NULLIF(completion_note, ''), NULLIF(task_note, ''), '已记录本项农事处理'),
                      ' · 状态：', CASE task_status
                        WHEN 'COMPLETED' THEN '已完成'
                        WHEN 'CANCELLED' THEN '已取消'
                        ELSE task_status END
                    ) detail,
                    COALESCE(completed_at, updated_at) event_at
                  FROM farm_task
                  WHERE plot_id=:plot_id AND task_status IN ('COMPLETED','CANCELLED')
                  UNION ALL
                  SELECT 'IRRIGATION', CONCAT('IR', record_id),
                    CONCAT('灌溉', IF(action_type='on','开启','关闭')),
                    CONCAT('执行状态：', status), COALESCE(executed_at, requested_at)
                  FROM irrigation_record WHERE plot_id=:plot_id
                  UNION ALL
                  SELECT 'ALERT', CONCAT('A', alert_id), '设备/农田告警',
                    alert_description, alert_datetime
                  FROM alert WHERE plot_id=:plot_id
                  UNION ALL
                  SELECT 'AUDIT', CONCAT('PCRSUB', request_id),
                    CASE request_type
                      WHEN 'STAGE_OVERRIDE' THEN '人工修正阶段并生成新管理计划'
                      WHEN 'PLANTING_CHANGE' THEN '修改种植信息并生成新管理计划'
                      ELSE '生成新的管理计划'
                    END,
                    CONCAT('申请原因：', request_reason, ' · 等待农场管理员确认'), submitted_at
                  FROM plan_change_request
                  WHERE plot_id=:plot_id AND submitted_at IS NOT NULL
                  UNION ALL
                  SELECT 'AUDIT', CONCAT('PCRREV', request.request_id),
                    CASE request.request_status
                      WHEN 'APPROVED' THEN '农场管理员已确认新管理计划'
                      WHEN 'ROLLED_BACK' THEN '农场管理员已退回并恢复原计划'
                      ELSE '农场管理员已处理计划变更'
                    END,
                    CONCAT('处理人：', COALESCE(reviewer.real_name, reviewer.username, '农场管理员'),
                      CASE WHEN request.review_comment IS NULL OR request.review_comment=''
                        THEN '' ELSE CONCAT(' · 说明：', request.review_comment) END), request.reviewed_at
                  FROM plan_change_request AS request
                  LEFT JOIN users AS reviewer ON reviewer.user_id=request.reviewed_by
                  WHERE request.plot_id=:plot_id AND request.reviewed_at IS NOT NULL
                  UNION ALL
                  SELECT 'AUDIT', CONCAT('CFG', config.plot_id), '灌溉配置最近调整',
                    CONCAT(
                      '湿度阈值 ', CAST(config.soil_moisture_threshold AS CHAR),
                      '% · 单次灌溉 ', config.irrigation_length,
                      ' 分钟 · 自动灌溉间隔 ', config.irrigation_interval, ' 分钟'
                    ), config.updated_at
                  FROM threshold_config AS config
                  WHERE config.plot_id=:plot_id
                    AND NOT EXISTS (
                      SELECT 1 FROM audit_log AS config_log
                      WHERE config_log.resource_id=:business_plot_id
                        AND config_log.resource_type='THRESHOLD_CONFIG'
                        AND config_log.created_at >= config.updated_at - INTERVAL 2 SECOND
                    )
                  UNION ALL
                  SELECT 'AUDIT', CONCAT('LOG', log_id), description,
                    CASE
                      WHEN resource_type='PLOT_STAGE' THEN CONCAT(
                        '修正原因：', COALESCE(
                          JSON_UNQUOTE(JSON_EXTRACT(after_data, '$.stageOverrideReason')),
                          '未填写'
                        )
                      )
                      WHEN resource_type='THRESHOLD_CONFIG' THEN '地块独立灌溉参数已更新'
                      WHEN resource_type='PLOT_PLANTING' THEN '地块种植信息已更新'
                      ELSE CONCAT(resource_type, ' / ', resource_id)
                    END, created_at
                  FROM audit_log WHERE resource_id=:business_plot_id
                ) timeline
                WHERE event_at IS NOT NULL
                ORDER BY event_at DESC, event_id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {
                "plot_id": numeric_id,
                "business_plot_id": f"P{numeric_id:03d}",
                "limit": limit,
                "offset": offset,
            },
        ).mappings().all()
    return [
        {
            "type": row["event_type"], "id": row["event_id"], "title": row["title"],
            "detail": row["detail"], "occurredAt": utc_isoformat(row["event_at"]),
        }
        for row in rows
    ]
