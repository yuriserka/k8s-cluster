import unittest

from k8s_cluster.commands.pipeline.planner import PipelinePlanError, build_execution_plan


class TestBuildExecutionPlan(unittest.TestCase):
    def _clone_pipeline(self, extra: dict) -> dict:
        return {
            "clone-app": {"kind": "clone"},
            **extra,
        }

    def test_clone_without_depends_on(self):
        steps = self._clone_pipeline({"env": {"depends_on": "clone-app", "cmd": ["true"]}})
        waves = build_execution_plan(steps)
        self.assertEqual(waves[0], ["clone-app"])

    def test_linear_chain_one_step_per_wave(self):
        steps = self._clone_pipeline(
            {
                "env": {"depends_on": "clone-app", "cmd": ["true"]},
                "install": {"depends_on": "env", "cmd": ["true"]},
            }
        )
        waves = build_execution_plan(steps)
        self.assertEqual(waves, [["clone-app"], ["env"], ["install"]])

    def test_siblings_run_in_same_wave(self):
        steps = self._clone_pipeline(
            {
                "test": {"depends_on": "clone-app", "cmd": ["true"]},
                "pub-a": {"depends_on": "test", "kind": "publish"},
                "pub-b": {"depends_on": "test", "kind": "publish"},
            }
        )
        waves = build_execution_plan(steps)
        self.assertEqual(waves[0], ["clone-app"])
        self.assertEqual(waves[1], ["test"])
        self.assertEqual(set(waves[2]), {"pub-a", "pub-b"})

    def test_diamond_single_parent_chain(self):
        steps = self._clone_pipeline(
            {
                "a": {"depends_on": "clone-app"},
                "b": {"depends_on": "a"},
                "c": {"depends_on": "b"},
                "d": {"depends_on": "c"},
            }
        )
        waves = build_execution_plan(steps)
        self.assertEqual(waves, [["clone-app"], ["a"], ["b"], ["c"], ["d"]])

    def test_missing_depends_on_raises(self):
        with self.assertRaises(PipelinePlanError):
            build_execution_plan(self._clone_pipeline({"env": {"cmd": ["true"]}}))

    def test_unknown_depends_on_raises(self):
        with self.assertRaises(PipelinePlanError):
            build_execution_plan(self._clone_pipeline({"env": {"depends_on": "missing"}}))

    def test_cycle_raises(self):
        steps = self._clone_pipeline(
            {
                "a": {"depends_on": "b"},
                "b": {"depends_on": "a"},
            }
        )
        with self.assertRaises(PipelinePlanError):
            build_execution_plan(steps)

    def test_missing_clone_raises(self):
        with self.assertRaises(PipelinePlanError):
            build_execution_plan({"env": {"depends_on": "clone-app", "cmd": ["true"]}})

    def test_duplicate_clone_raises(self):
        with self.assertRaises(PipelinePlanError):
            build_execution_plan(
                {
                    "clone-a": {"kind": "clone"},
                    "clone-b": {"kind": "clone"},
                }
            )

    def test_non_clone_without_depends_on_raises(self):
        with self.assertRaises(PipelinePlanError):
            build_execution_plan(
                {
                    "clone-app": {"kind": "clone"},
                    "env": {"cmd": ["true"]},
                }
            )

    def test_clone_with_depends_on_raises(self):
        with self.assertRaises(PipelinePlanError):
            build_execution_plan({"clone-app": {"kind": "clone", "depends_on": "other"}})


if __name__ == "__main__":
    unittest.main()
