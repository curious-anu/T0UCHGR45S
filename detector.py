import numpy as np
from sklearn.ensemble import IsolationForest

rng = np.random.default_rng(42)

training_data = np.column_stack([
    rng.choice([3, 4, 6], 1000, p=[0.65, 0.30, 0.05]),
    rng.integers(0, 100, 1000),
    rng.integers(0, 81, 1000),
    np.ones(1000),
    rng.choice([0, 1], 1000, p=[0.95, 0.05])
])

model = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42
)

model.fit(training_data)


def analyze_event(event):
    function_code = int(event.get("function_code", 3))
    register = int(event.get("register", 0))
    value = int(event.get("value", 0))
    source = str(event.get("source", "UNKNOWN"))

    is_write = function_code in [5, 6, 15, 16]
    authorized = source == "PLC-SIM-01"

    features = [[
        function_code,
        register,
        value,
        int(authorized),
        int(is_write)
    ]]

    anomaly_score = float(-model.decision_function(features)[0])
    ml_anomaly = model.predict(features)[0] == -1

    reasons = []

    if not authorized:
        reasons.append("Unrecognized source")

    if is_write and register in [100, 101]:
        reasons.append("Write to protected register")

    if is_write and register == 120 and not 0 <= value <= 80:
        reasons.append("Setpoint outside configured range (0-80)")

    if reasons:
        severity = "HIGH"
        status = "SUSPICIOUS"
        recommendation = (
            "Verify the source and requested change. "
            "Follow the site's approved safety procedure."
        )
    elif ml_anomaly:
        severity = "MEDIUM"
        status = "ANOMALY"
        recommendation = (
            "Review the event against expected operating behaviour."
        )
    else:
        severity = "LOW"
        status = "NORMAL"
        recommendation = "No configured rule was triggered."

    return {
        "status": status,
        "severity": severity,
        "anomaly_score": round(anomaly_score, 4),
        "ml_anomaly": bool(ml_anomaly),
        "reasons": reasons,
        "recommendation": recommendation,
        "source_type": event.get("source_type", "SIMULATED")
    }