"""设备业务服务。"""

from sqlalchemy.engine import Engine

from src.modules.device.repository import DeviceRepository


class DeviceService:
    """编排设备查询用例。"""

    def __init__(self, repository: DeviceRepository) -> None:
        self._repository = repository

    @classmethod
    def from_engine(cls, engine: Engine) -> "DeviceService":
        return cls(DeviceRepository(engine))

    def list_devices(self, plot_id: int | None = None) -> list[dict]:
        return self._repository.list_devices(plot_id)

    def get_status(self, device_id: int) -> dict | None:
        return self._repository.get_status(device_id)

    def bind_device(self, device_id: int, plot_id: int) -> dict | None:
        return self._repository.bind_device(device_id, plot_id)

    def unbind_device(self, device_id: int) -> bool:
        return self._repository.unbind_device(device_id)

    def create_device(
        self,
        device_code: str,
        mqtt_device_id: str,
        device_type: str,
        plot_id: int,
    ) -> dict:
        return self._repository.create_device(
            device_code, mqtt_device_id, device_type, plot_id
        )