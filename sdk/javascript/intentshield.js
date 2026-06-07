/**
 * IntentShield JavaScript SDK stub.
 * Full implementation not required for MVP.
 */
class IntentShieldClient {
  constructor(baseUrl = "http://localhost:8000", apiKey = null) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
  }

  async sendIntent(intent, userId = null) {
    const headers = { "Content-Type": "application/json" };
    if (this.apiKey) {
      headers["X-API-Key"] = this.apiKey;
    }

    const payload = { intent };
    if (userId !== null) {
      payload.user_id = userId;
    }

    const response = await fetch(`${this.baseUrl}/intent`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`IntentShield request failed: ${response.status}`);
    }

    return response.json();
  }
}

module.exports = { IntentShieldClient };
