package intentshield

default allow = false

data_export_blocked {
    contains(input.intent, "export")
    input.role != "admin"
}

data_modification_blocked {
    input.category == "data_modification"
    input.role != "admin"
}

allow {
    input.category == "general_action"
    input.role in ["admin", "user"]
    not data_export_blocked
}

allow {
    input.category == "financial_action"
    input.risk_score < 80
    input.role in ["admin", "user"]
    not data_export_blocked
}

allow {
    input.category == "data_modification"
    input.role == "admin"
    not data_export_blocked
}
