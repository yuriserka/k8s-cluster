from enum import Enum
from abc import abstractmethod
from typing import Optional
import logging
import time

from kafkaworker.core.logging.trace_context import (
    bind_mock_trace_context,
    reset_trace_context,
)


class ScheduleJobType(Enum):
    INTERVAL = 'interval'
    CRON = 'cron'


logger = logging.getLogger(__name__)


class ScheduleJob:
    def __init__(
        self,
        name: str,
        type: ScheduleJobType,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        max_instances: Optional[int] = None,
    ):
        self.name = name
        self.type = type
        self.max_instances = max_instances or 1
        self.__assert_valid(interval_seconds, cron_expression)

    @abstractmethod
    async def execute(self) -> None:
        raise NotImplementedError()

    async def run(self):
        bind_mock_trace_context()
        try:
            start_time = time.time()
            logger.info(f'starting to run job {self.name}')
            await self.execute()
            elapsed_time = time.time() - start_time
            logger.info(f'job {self.name} completed successfully in {elapsed_time} seconds')
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f'error running job {self.name}: {e}',
                extra={'job': self.name, 'elapsed_time': elapsed_time},
                exc_info=True
            )
            raise
        finally:
            reset_trace_context()

    def __assert_valid(self, interval: Optional[int], cron: Optional[str]):
        if self.type == ScheduleJobType.INTERVAL:
            if interval is None:
                raise ValueError('Interval is required for interval jobs')
            self.interval_seconds = interval
        elif self.type == ScheduleJobType.CRON:
            if cron is None:
                raise ValueError('Cron expression is required for cron jobs')
            self.cron_expression = cron
        else:
            raise ValueError(f'Invalid job type: {self.type}')
