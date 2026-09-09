"""Safe Attack Simulator package for RansomWatch."""

__all__ = ["SafeAttackSimulator"]

def __getattr__(name):
    if name == "SafeAttackSimulator":
        from attack_simulator.simulator import SafeAttackSimulator
        return SafeAttackSimulator
    raise AttributeError(f"module {__name__} has no attribute {name}")
