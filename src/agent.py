import random

class RandomAgent:
    """
    baseline rnadom action agent to test the environment
    """
    def select_action(self, obs, valid_actions):
        return random.choice(valid_actions)