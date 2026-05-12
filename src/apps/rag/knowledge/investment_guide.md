# Equity Flow – Investor Guide

## Overview

As an investor on Equity Flow, you have access to a curated marketplace of startup funding campaigns. This guide explains how to browse startups, evaluate campaigns using financial metrics, read campaign updates, and perform due diligence before committing capital.

All investor actions require a valid JWT `access_token` in the `Authorization: Bearer <token>` header.

---

## Browsing Startups

To view a specific startup's profile, make a `GET` request to:

```
GET /api/startup/{startup_id}
```

This returns the startup's full profile, including its name, description, location, website, team size, industry category, funding stage, and founding date. Use this to get a high-level overview of the company before diving into its campaigns.

---

## Viewing Campaigns

To view the details of a specific funding campaign, make a `GET` request to:

```
GET /api/startup/compaign/{campaign_id}
```

This returns all campaign data, including fundraising targets, financial metrics, campaign status, deadline, and the amount raised so far.

---

## Understanding Campaign Metrics

When evaluating a campaign, pay close attention to the following fields:

| Metric | What It Tells You |
|---|---|
| `target_amount` | The total amount the startup is trying to raise in this round |
| `raised_amount` | How much has been committed so far — track this against the target |
| `min_investment` | The minimum you must invest to participate in this campaign |
| `valuation` | The startup's pre-money valuation — lower valuations mean potentially higher upside |
| `revenue_share` | The percentage of future revenue you will receive as a return on your investment |

---

## What Is Revenue Share in Equity Crowdfunding?

Revenue sharing (also called a revenue-based investment) is an alternative to traditional equity. Instead of receiving shares in the company, investors receive a percentage of the startup's future revenue until a defined return multiple is paid out.

**Example:** If you invest $10,000 into a campaign with a 5% revenue share and a 2x return cap, you would receive 5% of the startup's monthly revenue each month until you have received $20,000 (your original $10,000 x 2).

Revenue share deals are often more flexible for startups than traditional equity and can provide investors with earlier returns if the startup generates revenue quickly.

---

## Understanding Financial Health Metrics

Before investing, assess the startup's financial fundamentals:

- **Burn Rate:** Monthly cash spend. A burn rate that is high relative to revenue is a warning sign unless the startup is in early-stage hyper-growth mode.
- **Runway:** How many months the startup can operate before running out of cash. A runway below 6 months without a clear funding path is a significant risk.
- **Gross Margin:** The percentage of revenue retained after the direct costs of producing the product or service. Software startups typically have margins above 60–70%. Below 30% may indicate a cost-heavy model.
- **Active Customers:** The number of paying or engaged customers. Growing customer count alongside revenue is a positive sign of product-market fit.
- **Revenue:** Current revenue gives you a baseline to evaluate the valuation and revenue share terms. A startup with $0 revenue and a $10M valuation requires a higher risk tolerance than one generating $50K/month.

---

## What to Look for Before Investing

Use this checklist as a starting point for evaluating any campaign on Equity Flow:

1. **Clear problem and solution.** Does the startup's description articulate a real, sizeable problem? Is the solution differentiated?
2. **Credible team.** Review the team size and website. Does the team have relevant experience?
3. **Realistic valuation.** Compare the valuation to the revenue and stage. Is it reasonable for the sector?
4. **Sufficient runway.** Does the startup have enough runway to deploy the capital from this round effectively?
5. **Revenue traction.** Is the startup generating revenue? Is it growing?
6. **Healthy gross margin.** Can the business scale profitably?
7. **Clear use of funds.** Campaign updates and descriptions should explain how the raised capital will be used.

---

## Campaign Deadlines and Statuses

| Status | What It Means for You |
|---|---|
| `OPEN` | The campaign is actively accepting investments — you can participate now |
| `CLOSED` | The deadline has passed and the target was not reached — no new investments |
| `FUNDED` | The target was successfully met — this round is complete |

Act promptly on campaigns you are interested in. Once the `deadline` passes or the campaign is marked `FUNDED` or `CLOSED`, the round is no longer available.

---

## Reading Campaign Updates

Campaign updates are posted by the startup team during an active round. To read an update:

```
GET /api/startup/compaign-update/{update_id}
```

Updates contain a `title` and a `body` with the latest news from the startup. Regularly updated campaigns signal an engaged and communicative founding team — a positive indicator for investors.

---

## Due Diligence Checklist

- [ ] Read the full startup profile and visit the company website
- [ ] Review all campaign financial metrics (valuation, runway, burn rate, gross margin)
- [ ] Check the campaign deadline and current `raised_amount` vs `target_amount`
- [ ] Read all campaign updates for recent developments
- [ ] Evaluate revenue trends and active customer growth
- [ ] Understand the revenue share terms and expected return timeline
- [ ] Assess whether the `min_investment` aligns with your portfolio strategy

---

## Risk Factors in Equity Crowdfunding

Investing in early-stage startups carries inherent risks. Be aware of the following:

- **High failure rate.** Many startups do not survive beyond their first few years. You may lose your entire investment.
- **Illiquidity.** Unlike public stocks, startup investments are illiquid — you cannot easily sell your position.
- **Dilution.** Future funding rounds may dilute your effective ownership or reduce the revenue share pool.
- **Execution risk.** Even great ideas fail due to poor execution, market timing, or team issues.
- **No guaranteed returns.** Revenue share depends on the startup generating sufficient revenue — if the company fails, payments stop.

Always invest only what you can afford to lose, and consider diversifying across multiple campaigns to spread risk.
