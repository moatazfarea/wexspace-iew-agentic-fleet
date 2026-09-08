"""TEST ONLY: deterministic model responses; the Strands Agent and tools are real.

This is neither a Google response nor a deployed/live-agent demonstration.
"""
import json
import os

from strands.models.model import Model


class ScriptedModel(Model):
    def __init__(self, actions=()):
        self.actions = list(actions)
        self.calls = 0
        self.config = {"model_id": "test-only-scripted-model"}

    def update_config(self, **config):
        self.config.update(config)

    def get_config(self):
        return self.config

    async def structured_output(self, *args, **kwargs):
        raise NotImplementedError("Not used by this test harness")
        yield  # async generator contract

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        self.calls += 1
        action = self.actions.pop(0) if self.actions else None
        if action == "CRASH":
            os._exit(23)  # deliberately skip finalizers in the bounded test process
        yield {"messageStart": {"role": "assistant"}}
        if action:
            tool_id = f"test-call-{self.calls}"
            yield {"contentBlockStart": {"start": {"toolUse": {"toolUseId": tool_id, "name": action}}, "contentBlockIndex": 0}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps({})}}, "contentBlockIndex": 0}}
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            yield {"contentBlockStart": {"start": {}, "contentBlockIndex": 0}}
            yield {"contentBlockDelta": {"delta": {"text": "Review the durable work status."}, "contentBlockIndex": 0}}
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "end_turn"}}
