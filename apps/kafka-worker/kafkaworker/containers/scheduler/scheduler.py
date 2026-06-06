import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from kafkaworker.containers.scheduler.jobs.schedule_job import ScheduleJob, ScheduleJobType


logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, jobs: list[ScheduleJob]):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_jobstore(MemoryJobStore(), "default")
        for job in jobs:
            if job.type == ScheduleJobType.INTERVAL:
                self.scheduler.add_job(
                    job.run,
                    trigger=IntervalTrigger(seconds=job.interval_seconds),
                    **self._add_job_kwargs(job),
                )
            elif job.type == ScheduleJobType.CRON:
                self.scheduler.add_job(
                    job.run,
                    trigger=CronTrigger(cron=job.cron_expression),
                    **self._add_job_kwargs(job),
                )

    def _add_job_kwargs(self, job: ScheduleJob) -> dict:
        kwargs = {
            "id": job.name,
            "max_instances": job.max_instances,
        }
        if job.start_delay_seconds:
            kwargs["next_run_time"] = datetime.now(timezone.utc) + timedelta(seconds=job.start_delay_seconds)
        return kwargs

    def start(self):
        self.scheduler.start()

    def shutdown(self, wait: bool = True) -> None:
        self.scheduler.shutdown(wait=wait)
