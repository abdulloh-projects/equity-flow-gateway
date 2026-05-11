# Equity Flow – Authentication Guide

## Overview

Equity Flow uses a secure, token-based authentication system. All users — whether investors or startup founders — must register, verify their email address, and then log in to access the platform. This three-step flow ensures account integrity and protects both parties in the investment process.

---

## Step 1: Registration

To create an account, send a `POST` request to `/api/auth/register` with the following fields in the request body:

| Field | Type | Description |
|---|---|---|
| `email` | string | A valid, unique email address |
| `password` | string | A strong password (see requirements below) |
| `first_name` | string | Your first name |
| `last_name` | string | Your last name |
| `role` | string | Either `INVESTOR` or `STARTUPPER` |

> **Important:** Choose your role carefully at registration. The `INVESTOR` role gives you access to browse startups and campaigns. The `STARTUPPER` role allows you to create a startup profile, launch campaigns, and manage fundraising.

### Password Requirements

Equity Flow enforces strong password policies to keep your account secure:
- Minimum of 8 characters in length
- Should include a mix of uppercase and lowercase letters
- Should include at least one number
- Should include at least one special character (e.g., `!`, `@`, `#`, `$`)

Never share your password with anyone. Equity Flow staff will never ask for your password.

---

## Step 2: Email Verification via OTP

After registration, your account is created but **not yet active**. You must verify your email address using a One-Time Password (OTP) before you can log in.

### Send OTP

Send a `POST` request to `/api/auth/send-otp` with:
```
{ "email": "you@example.com" }
```

The platform will send a time-sensitive OTP code to the provided email address. Check your inbox (and spam folder if necessary).

### Verify OTP

Once you have the code, send a `POST` request to `/api/auth/verify-otp` with:
```
{ "email": "you@example.com", "otp": "123456" }
```

On success, your account is activated and you can proceed to log in. OTP codes expire after a short window — if yours expires, simply call `/api/auth/send-otp` again to receive a fresh code.

---

## Step 3: Login

Send a `POST` request to `/api/auth/login` with your credentials:

```
{ "email": "you@example.com", "password": "YourStr0ng!Pass" }
```

A successful login returns:

| Field | Description |
|---|---|
| `access_token` | A short-lived JWT used to authenticate API requests |
| `refresh_token` | A long-lived token used to obtain a new access token |

Store these tokens securely. Do **not** store them in browser `localStorage` if possible — prefer secure cookies or an in-memory store.

---

## Using the Access Token

Every protected endpoint on Equity Flow requires the `access_token` to be included in the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

If this header is missing or the token is invalid/expired, the API will return a `401 Unauthorized` error.

---

## Token Expiry and Refresh Flow

- The `access_token` is short-lived (typically 15–60 minutes). When it expires, API calls will return `401 Unauthorized`.
- Use the `refresh_token` to obtain a new `access_token` without requiring the user to log in again.
- The `refresh_token` itself has a longer lifespan but will also expire eventually, requiring a fresh login.
- Always handle `401` responses in your application gracefully by attempting a token refresh before prompting the user to re-authenticate.

---

## Role Capabilities

| Capability | INVESTOR | STARTUPPER |
|---|---|---|
| Browse startup profiles | Yes | Yes |
| View campaigns | Yes | Yes |
| Create a startup profile | No | Yes |
| Launch fundraising campaigns | No | Yes |
| Post campaign updates | No | Yes |
| Add bank information | No | Yes |

---

## Security Best Practices

- **Never expose tokens in URLs.** Always send tokens via HTTP headers.
- **Use HTTPS.** All API communication must be over HTTPS to prevent token interception.
- **Revoke sessions when done.** Log out and discard tokens when you are finished with a session.
- **Monitor for suspicious activity.** If you suspect your account has been compromised, change your password immediately and contact Equity Flow support.
- **Do not reuse passwords.** Use a unique password for your Equity Flow account.
