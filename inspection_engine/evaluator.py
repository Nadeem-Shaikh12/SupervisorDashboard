"""
inspection_engine/evaluator.py
===============================
Rule engine evaluating temperatures against dataset thresholds.
"""

def evaluate_temperature(temperature: float, normal_max: float, failure_max: float) -> str:
    """
    Evaluates OK/NOK status based on rules:
    - <= normal_max: OK
    - > normal_max and < failure_max: WARNING
    - >= failure_max: NOK
    """
    if temperature <= normal_max:
        return "OK"
    elif temperature < failure_max:
        return "WARNING"
    else:
        return "NOK"
