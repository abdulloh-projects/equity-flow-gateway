# Equity Flow – Startup Guide

## Overview

This guide is for founders and startup teams using Equity Flow to raise capital. As a `STARTUPPER`, you can build a public company profile, launch equity funding campaigns, provide banking details for fund collection, and keep investors engaged with regular campaign updates.

All endpoints described below require a valid JWT `access_token` in the `Authorization: Bearer <token>` header.

---

## Creating Your Startup Profile

Your startup profile is the first thing investors see. It should be detailed, accurate, and compelling. To create a profile, send a `POST` request to `/api/startup/create` with the following fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Your company's official name |
| `description` | string | Yes | A clear summary of what your startup does and the problem it solves |
| `location` | string | Yes | City and country where your startup is headquartered |
| `website_url` | string | Yes | Your company's public website |
| `team_size` | integer | Yes | Current number of full-time team members |
| `category_id` | integer | Yes | ID of your industry category (e.g., fintech, healthtech, edtech) |
| `stage_id` | integer | Yes | ID representing your current funding stage |
| `founded_at` | string | Yes | Company founding date in ISO 8601 format (e.g., `2022-03-15T00:00:00Z`) |

To update your profile later, send a `PUT` request to `/api/startup/update` with `startup_id` (required) and any fields you wish to change. To remove your startup from the platform, send a `DELETE` request to `/api/startup/delete` with the `startup_id`.

### Best Practices for Your Startup Profile

- **Be specific in your description.** Investors read dozens of pitches. Clearly state the problem, your solution, and your target market within the first few sentences.
- **Keep your team size current.** Investors pay attention to team growth as a signal of momentum.
- **Use a professional website.** Investors will visit your site — make sure it is live and reflects your brand.
- **Select the right category and stage.** These are used to surface your startup to investors filtering by domain and investment preference.

---

## Understanding Startup Stages and Categories

### Stages (via `stage_id`)
The stage represents where your company is in its lifecycle:

| Stage | Typical Characteristics |
|---|---|
| **Idea / Pre-seed** | Concept stage, no revenue, building MVP |
| **Early** | MVP launched, initial users, validating product-market fit |
| **Seed** | Growing user base, early revenue, refining business model |
| **Series A** | Proven model, scaling operations and team |
| **Series B+** | Significant revenue, expanding into new markets |

Use the appropriate `stage_id` that maps to your current stage. Contact support or refer to the categories endpoint for the full list of available IDs.

### Categories (via `category_id`)
Categories represent the industry vertical your startup operates in — such as fintech, healthtech, edtech, logistics, SaaS, e-commerce, and more. Investors often filter campaigns by category, so choosing the most accurate one is important for discoverability.

---

## Launching a Funding Campaign

A campaign (equity round) is a time-bound fundraising event tied to your startup profile. To create a campaign, send a `POST` request to `/api/startup/compaign` with the following fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `startup_id` | integer | Yes | ID of your startup profile |
| `target_amount` | number | Yes | Total amount you aim to raise (in your base currency) |
| `min_investment` | number | Yes | The minimum a single investor can contribute |
| `revenue` | number | Yes | Your current monthly or annual revenue |
| `revenue_share` | number | Yes | Percentage of future revenue shared with investors |
| `burn_rate` | number | Yes | Monthly cash expenditure |
| `runway` | number | Yes | Number of months your current cash reserves will last |
| `active_customers` | integer | No | Current number of paying or active customers |
| `valuation` | number | Yes | Your startup's current pre-money valuation |
| `gross_margin` | number | Yes | Gross margin as a percentage |
| `status` | string | Yes | Campaign status: `OPEN`, `CLOSED`, or `FUNDED` |
| `deadline` | string | Yes | Campaign end date in ISO 8601 format |

---

## Campaign Status Explained

| Status | Meaning |
|---|---|
| `OPEN` | The campaign is live and accepting investments |
| `CLOSED` | The campaign period has ended without reaching the target |
| `FUNDED` | The campaign successfully reached its fundraising target |

Set the status to `OPEN` when you are ready to go live. You can update a campaign's status at any time using `PUT /api/startup/compaign/update`.

---

## Understanding Campaign Financial Metrics

Providing honest and accurate financial data is critical to investor trust. Here is what each metric means:

- **Burn Rate:** The amount of cash your startup spends each month. A lower burn rate signals leaner operations. Investors use this to assess how efficiently you operate.
- **Runway:** Calculated as `cash reserves / monthly burn rate`, this is how many months your startup can operate without additional funding. A runway of 12+ months is generally reassuring.
- **Gross Margin:** `(Revenue - Cost of Goods Sold) / Revenue * 100`. A higher gross margin indicates a more scalable business model.
- **Valuation:** Your startup's estimated worth before new capital is raised (pre-money valuation). This determines the equity dilution investors experience.
- **Revenue Share:** The percentage of future revenue you commit to sharing with investors until a defined return multiple is achieved. This is a key term for investors evaluating their potential return.

---

## Adding Bank Information

Before you can receive investment funds, you must add your startup's banking details. Send a `POST` request to `/api/startup/bank-info` with:

| Field | Type | Description |
|---|---|---|
| `startup_id` | integer | The ID of your startup |
| `mfo` | string | The bank's MFO (interbank routing code) |
| `account_number` | string | Your company bank account number |
| `receipant_name` | string | The registered name on the bank account |

Ensure all banking details are accurate. Incorrect bank information can delay or prevent fund transfers. You may update these details at any time using `PUT /api/startup/bank-info/update`.

---

## Posting Campaign Updates

Investors who have shown interest in your campaign appreciate regular, transparent communication. Use campaign updates to share milestones, financial progress, product launches, or any news that affects your startup's trajectory.

Send a `POST` request to `/api/startup/compaign-update` with:

| Field | Type | Description |
|---|---|---|
| `compaign_id` | integer | The ID of the campaign this update belongs to |
| `title` | string | A short, descriptive headline for the update |
| `body` | string | The full text of the update |

### Tips for Effective Campaign Updates

- **Post at least bi-weekly** during an active campaign to maintain investor confidence.
- **Be honest about challenges.** Investors respect transparency. Hiding problems erodes trust.
- **Celebrate milestones.** New customer wins, product launches, and partnerships are worth sharing.
- **Include numbers wherever possible.** "We grew MRR by 15% this month" is far more compelling than "we had a great month."

---

## Managing Multiple Campaigns

A single startup profile can host multiple campaigns over time (e.g., a seed round followed later by a Series A round). Only one campaign should typically be `OPEN` at a time to avoid investor confusion. When a round concludes, update its status to `CLOSED` or `FUNDED` before launching a new one.
