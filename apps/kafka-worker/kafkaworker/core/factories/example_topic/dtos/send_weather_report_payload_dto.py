from typing import NamedTuple


class SendWeatherReportEventPayloadDTO(NamedTuple):
    report_id: str
    address: str
    temperature: str
    wind_speed: str
    wind_direction: str
    timestamp: str
