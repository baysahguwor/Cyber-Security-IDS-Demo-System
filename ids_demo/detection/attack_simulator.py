from typing import Tuple


class AttackSimulator:
    @staticmethod
    def simulate_remote_attack() -> Tuple[str, str]:
        attack_type = "REMOTE_ATTACK"
        description = (
            "Simulated Remote Intrusion Attempt\n"
            "Source IP: 192.168.1.45\n"
            "Activity: Port Scan Detected"
        )
        return attack_type, description
