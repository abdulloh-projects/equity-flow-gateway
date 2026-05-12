# Equity Flow – API Reference

## Overview

This document provides a complete reference for all REST API endpoints exposed by the Equity Flow API gateway. All requests and responses use JSON. Protected endpoints require the `Authorization: Bearer <access_token>` header obtained after login.

**Base URL:** `https://api.equityflow.io` (or your configured gateway host)

**Content-Type:** All request bodies must use `Content-Type: application/json`.

---

## Authentication Endpoints

These endpoints do **not** require an `Authorization` header.

---

### POST /api/auth/register

Register a new user account.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | string | Yes | A valid, unique email address |
| `password` | string | Yes | A strong password (min 8 chars) |
| `first_name` | string | Yes | User's first name |
| `last_name` | string | Yes | User's last name |
| `role` | string | Yes | `INVESTOR` or `STARTUPPER` |

**Response:** `201 Created` — User account created. Email verification required before login.

---

### POST /api/auth/login

Authenticate a verified user and obtain JWT tokens.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | string | Yes | Registered email address |
| `password` | string | Yes | Account password |

**Response:** `200 OK`

```
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>"
}
```

---

### POST /api/auth/send-otp

Send a One-Time Password to the user's email for account verification.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | string | Yes | The email address to send the OTP to |

**Response:** `200 OK` — OTP sent successfully.

---

### POST /api/auth/verify-otp

Verify the OTP code received by email to activate the account.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | string | Yes | The email address associated with the account |
| `otp` | string | Yes | The OTP code received via email |

**Response:** `200 OK` — Account verified and activated.

---

## Startup Endpoints

All startup endpoints require: `Authorization: Bearer <access_token>`

---

### POST /api/startup/create

Create a new startup profile.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Startup name |
| `description` | string | Yes | Description of the startup |
| `location` | string | Yes | Headquarters location |
| `website_url` | string | Yes | Public website URL |
| `team_size` | integer | Yes | Number of team members |
| `category_id` | integer | Yes | Industry category ID |
| `stage_id` | integer | Yes | Funding stage ID |
| `founded_at` | string | Yes | Founding date (ISO 8601, e.g. `2021-06-01T00:00:00Z`) |

**Response:** `201 Created` — Returns created startup object with `startup_id`.

---

### PUT /api/startup/update

Update an existing startup profile.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `startup_id` | integer | Yes | ID of the startup to update |
| `name` | string | No | Updated startup name |
| `description` | string | No | Updated description |
| `location` | string | No | Updated location |
| `website_url` | string | No | Updated website |
| `team_size` | integer | No | Updated team size |
| `category_id` | integer | No | Updated category ID |
| `stage_id` | integer | No | Updated stage ID |
| `founded_at` | string | No | Updated founding date |

**Response:** `200 OK` — Returns updated startup object.

---

### DELETE /api/startup/delete

Delete a startup profile.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `startup_id` | integer | Yes | ID of the startup to delete |

**Response:** `200 OK` — Startup deleted successfully.

---

### GET /api/startup/{startup_id}

Retrieve a startup profile by ID.

**Path Parameter:** `startup_id` — The integer ID of the startup.

**Response:** `200 OK` — Returns the full startup profile object.

---

## Campaign Endpoints

All campaign endpoints require: `Authorization: Bearer <access_token>`

---

### POST /api/startup/compaign

Create a new fundraising campaign for a startup.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `startup_id` | integer | Yes | ID of the associated startup |
| `target_amount` | number | Yes | Total fundraising target |
| `min_investment` | number | Yes | Minimum investment per investor |
| `revenue` | number | Yes | Current revenue |
| `revenue_share` | number | Yes | Revenue share percentage offered |
| `burn_rate` | number | Yes | Monthly cash burn |
| `runway` | number | Yes | Months of runway remaining |
| `active_customers` | integer | No | Number of active customers |
| `valuation` | number | Yes | Pre-money valuation |
| `gross_margin` | number | Yes | Gross margin percentage |
| `status` | string | Yes | `OPEN`, `CLOSED`, or `FUNDED` |
| `deadline` | string | Yes | Campaign end date (ISO 8601) |

**Response:** `201 Created` — Returns created campaign object with `campaign_id`.

---

### PUT /api/startup/compaign/update

Update an existing campaign.

**Request Body:** `campaign_id` (required) + any of the campaign fields listed above (all optional).

**Response:** `200 OK` — Returns updated campaign object.

---

### DELETE /api/startup/compaign/delete

Delete a campaign.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `campaign_id` | integer | Yes | ID of the campaign to delete |

**Response:** `200 OK` — Campaign deleted.

---

### GET /api/startup/compaign/{campaign_id}

Retrieve a campaign by ID.

**Path Parameter:** `campaign_id` — The integer ID of the campaign.

**Response:** `200 OK` — Returns the full campaign object.

---

## Bank Info Endpoints

All bank info endpoints require: `Authorization: Bearer <access_token>`

---

### POST /api/startup/bank-info

Add bank information to a startup for receiving investment funds.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `startup_id` | integer | Yes | ID of the associated startup |
| `mfo` | string | Yes | Bank MFO (interbank routing code) |
| `account_number` | string | Yes | Bank account number |
| `receipant_name` | string | Yes | Registered account holder name |

**Response:** `201 Created` — Returns created bank info object with `bank_info_id`.

---

### PUT /api/startup/bank-info/update

Update existing bank information.

**Request Body:** `bank_info_id` (required) + any of `mfo`, `account_number`, `receipant_name` (all optional).

**Response:** `200 OK` — Returns updated bank info object.

---

### DELETE /api/startup/bank-info/delete

Delete bank information.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `bank_info_id` | integer | Yes | ID of the bank info record to delete |

**Response:** `200 OK` — Bank info deleted.

---

### GET /api/startup/bank-info/{bank_info_id}

Retrieve bank info by ID.

**Path Parameter:** `bank_info_id` — The integer ID of the bank info record.

**Response:** `200 OK` — Returns the bank info object.

---

## Campaign Update Endpoints

All campaign update endpoints require: `Authorization: Bearer <access_token>`

---

### POST /api/startup/compaign-update

Post a new update for an active campaign.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `compaign_id` | integer | Yes | ID of the campaign this update belongs to |
| `title` | string | Yes | Short headline for the update |
| `body` | string | Yes | Full content of the update |

**Response:** `201 Created` — Returns created update object with `update_id`.

---

### PUT /api/startup/compaign-update/update

Edit an existing campaign update.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `update_id` | integer | Yes | ID of the update to edit |
| `title` | string | No | Updated headline |
| `body` | string | No | Updated content |

**Response:** `200 OK` — Returns updated campaign update object.

---

### DELETE /api/startup/compaign-update/delete

Delete a campaign update.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `update_id` | integer | Yes | ID of the update to delete |

**Response:** `200 OK` — Update deleted.

---

### GET /api/startup/compaign-update/{update_id}

Retrieve a campaign update by ID.

**Path Parameter:** `update_id` — The integer ID of the campaign update.

**Response:** `200 OK` — Returns the campaign update object.

---

## Chatbot Endpoints

These endpoints do **not** require an `Authorization` header.

---

### POST /api/chat

Send a message to the Equity Flow AI assistant.

**Request Body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | Yes | The user's question or message |
| `session_id` | string | No | Session ID to maintain conversation context across messages |

**Response:** `200 OK`

```
{
  "response": "<assistant reply>",
  "session_id": "<session_id>",
  "sources": ["<source document>", ...]
}
```

---

### POST /api/chat/init

Initialize or reload the chatbot knowledge base from the markdown source files.

**Request Body:** None

**Response:** `200 OK` — Knowledge base initialized successfully.

---

### DELETE /api/chat/session/{session_id}

Clear the conversation history for a given session.

**Path Parameter:** `session_id` — The string session ID to clear.

**Response:** `200 OK` — Session history deleted.

---

### GET /api/chat/health

Check connectivity to the underlying Ollama LLM service.

**Response:** `200 OK` — Returns the health status of the Ollama backend.

---

## Error Codes

| HTTP Status | Meaning |
|---|---|
| `400 Bad Request` | The request was malformed, missing required fields, or contained invalid values. Check your request body. |
| `401 Unauthorized` | The `Authorization` header is missing, the token is invalid, or the token has expired. Re-authenticate or refresh your token. |
| `422 Unprocessable Entity` | The request body structure is valid JSON but failed validation (e.g., a field has the wrong type, a required field is null, or a value is out of range). |
| `500 Internal Server Error` | An unexpected error occurred on the server. This may indicate a temporary issue with one of the backend microservices. Retry after a short delay or contact support. |
