"""灌溉指令业务服务。"""

from sqlalchemy.engine import Engine

from src.modules.command.repository import CommandRepository


class CommandService:
    """编排灌溉指令查询用例。"""

    def __init__(self, repository: CommandRepository) -> None:
        self._repository = repository

    @classmethod
    def from_engine(cls, engine: Engine) -> "CommandService":
        return cls(CommandRepository(engine))

    def get_command(self, record_id: int) -> dict | None:
        return self._repository.get_command(record_id)

    def create_command(
        self, device_id: int, action: str, operator_id: int | None = None
    ) -> dict | None:
        return self._repository.create_command(device_id, action, operator_id)

    def get_mqtt_device_id(self, record_id: int) -> str | None:
        return self._repository.get_mqtt_device_id(record_id)

    def mark_publish_failed(self, record_id: int) -> None:
        self._repository.mark_publish_failed(record_id)
