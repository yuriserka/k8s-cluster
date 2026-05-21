import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from kafkaworker.containers.scheduler.jobs.schedule_job import ScheduleJob, ScheduleJobType


logger = logging .getLogger(__name__)


class Scheduler:
    def __init__(self, jobs: list[ScheduleJob]):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_jobstore(MemoryJobStore(), 'default')
        for job in jobs:
            if job.type == ScheduleJobType.INTERVAL:
                self.scheduler.add_job(
                    job.run,
                    trigger=IntervalTrigger(seconds=job.interval_seconds),
                    max_instances=job.max_instances
                )
            elif job.type == ScheduleJobType.CRON:
                self.scheduler.add_job(
                    job.run,
                    trigger=CronTrigger(cron=job.cron_expression),
                    max_instances=job.max_instances
                )

    def start(self):
        self.scheduler.start()
