import time

from transitions import Machine

from .config import plugin_config


class group_speaker(object):

    states: list = ["wait", "speak", "punish"]

    def __init__(self, uid: str):
        self.current_speaker: str = uid
        self.frequent_speaking_count: int = 0
        self.repeat_speaking_conut: int = 0
        self.frequent_timeout: bool = False
        self.start_timestamp: int = 0

        self.machine: Machine = Machine(
            model=self, states=group_speaker.states, initial="wait"
        )
        self.machine.add_transition(trigger="get_speak", source="wait", dest="speak")
        self.machine.add_transition(trigger="timeout", source="speak", dest="wait")
        self.machine.add_transition(trigger="continue_speak", source="speak", dest="=")
        self.machine.add_transition(
            trigger="frequent_timeout", source="speak", dest="punish"
        )
        self.machine.add_transition(
            trigger="repeat_timeout", source="speak", dest="punish"
        )
        self.machine.add_transition(
            trigger="punish_completed", source="punish", dest="wait"
        )
