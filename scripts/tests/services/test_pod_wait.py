import unittest

from k8s_cluster.services.pod_wait import PodWaitState, PodStateTracker, classify_pod_state, get_failed_exit_code


class TestClassifyPodState(unittest.TestCase):
    def test_pending_when_pod_missing(self):
        state = classify_pod_state(None, expect_succeeded=False, has_seen_running=False)
        self.assertEqual(state, PodWaitState.PENDING)

    def test_finished_when_succeeded_expected(self):
        pod = {"status": {"phase": "Succeeded"}}
        state = classify_pod_state(pod, expect_succeeded=True, has_seen_running=False)
        self.assertEqual(state, PodWaitState.FINISHED)

    def test_failed_when_container_exit_nonzero(self):
        pod = {
            "status": {
                "phase": "Failed",
                "containerStatuses": [{"state": {"terminated": {"exitCode": 1}}}],
            }
        }
        self.assertEqual(get_failed_exit_code(pod), 1)
        state = classify_pod_state(pod, expect_succeeded=False, has_seen_running=False)
        self.assertEqual(state, PodWaitState.FAILED)


class TestPodStateTracker(unittest.TestCase):
    def test_started_sets_has_seen_running(self):
        tracker = PodStateTracker("test-pod")
        tracker.observe(PodWaitState.STARTED)
        self.assertTrue(tracker.has_seen_running)

    def test_progressing_re_echo_only_after_interval(self):
        tracker = PodStateTracker("test-pod")
        tracker.observe(PodWaitState.PROGRESSING)
        self.assertEqual(tracker.last_printed_state, PodWaitState.PROGRESSING)
