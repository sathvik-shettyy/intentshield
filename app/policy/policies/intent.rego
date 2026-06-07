package intentshield

default allow = false

allow {
    input.category == "general_action"
}

allow {
    input.category == "financial_action"
    input.risk_score < 80
}
