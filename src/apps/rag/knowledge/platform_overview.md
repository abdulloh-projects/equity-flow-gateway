# Equity Flow – Platform Overview

## What Is Equity Flow?

Equity Flow is an equity crowdfunding platform that bridges the gap between ambitious startups and forward-thinking investors. Rather than relying on traditional venture capital gatekeepers, Equity Flow democratizes access to early-stage investment opportunities by allowing startups to raise funding directly from a community of individual and institutional investors in exchange for equity or revenue-sharing agreements.

The platform is built on the belief that great ideas deserve funding regardless of geography, network, or background. Startups get the capital they need to grow, and investors gain access to high-potential opportunities that were previously reserved for a privileged few.

---

## How the Platform Works — End to End

1. **Startups register and build a profile.** A founder registers with the STARTUPPER role, verifies their email via OTP, and creates a detailed startup profile that includes the company name, description, location, website, team size, founding date, industry category, and funding stage.

2. **Startups launch funding campaigns.** Once a profile is established, startups create equity rounds (campaigns) that define how much capital they want to raise, the minimum investment amount, key financial metrics (revenue, burn rate, runway, gross margin, valuation), and a campaign deadline.

3. **Investors discover and evaluate opportunities.** Users with the INVESTOR role can browse startup profiles and active campaigns. They review financial metrics, campaign updates, and company details to make informed investment decisions.

4. **Transparent communication through campaign updates.** Startups post regular updates to keep investors informed about milestones, financials, and company progress throughout an active campaign.

5. **Secure fund collection via bank information.** Startups add verified bank details so that investment funds can be routed securely when a campaign reaches its goals.

---

## The Two Main User Types

### Startups (STARTUPPER Role)
Founders and startup teams use Equity Flow to raise capital by presenting their company to a broad investor audience. They are responsible for building an honest, detailed company profile, launching campaigns with clear financial terms, and maintaining investor trust through regular updates.

### Investors (INVESTOR Role)
Investors are individuals or entities looking to support early-stage companies in exchange for future financial returns. They browse active campaigns, assess financial health indicators, and decide which startups align with their investment thesis and risk appetite.

---

## Key Platform Concepts

| Concept | Description |
|---|---|
| **Startup Profile** | The public-facing company page containing name, description, location, website, team size, category, stage, and founding date. |
| **Campaign (Equity Round)** | A time-bound fundraising event where a startup seeks a target amount from investors with defined equity or revenue-share terms. |
| **Equity Round** | The specific terms of investment, including valuation, revenue share percentage, and minimum investment amount. |
| **Bank Information** | The startup's verified banking details (MFO code, account number, recipient name) used for receiving investor funds. |
| **Campaign Updates** | Posts made by startups during an active campaign to share progress, milestones, and financial news with investors. |
| **Startup Stage** | A classification of the company's maturity level — from idea-stage through Early, Seed, Series A, and beyond — identified by a `stage_id`. |
| **Startup Category** | The industry or sector a startup operates in (e.g., fintech, health, edtech), identified by a `category_id`. |

---

## Platform Values

- **Transparency:** Every campaign displays real financial metrics — burn rate, runway, gross margin, revenue, and active customer count — so investors can make data-driven decisions.
- **Accessibility:** Equity Flow lowers the barrier to both raising and investing capital by removing the need for warm introductions or minimum wealth thresholds.
- **Growth:** The platform is designed to help startups grow by connecting them not just with capital, but with a community of engaged, knowledgeable investors.

---

## How the Technology Works

Equity Flow is built as a modern cloud-native application using a **microservices architecture**. Each domain (authentication, startup management, campaigns, bank info, campaign updates) runs as an independent **gRPC microservice**, enabling high performance, independent deployability, and clear separation of concerns.

All client interactions — whether from a web application or mobile app — go through a centralized **FastAPI REST API gateway**. This gateway translates incoming HTTP requests into gRPC calls to the appropriate backend service and returns structured JSON responses to the client.

**Authentication** is handled using **JWT (JSON Web Tokens)**. Upon login, users receive a short-lived `access_token` used to authenticate API requests, and a long-lived `refresh_token` used to obtain new access tokens without re-logging in. All protected endpoints require the `Authorization: Bearer <access_token>` header.

This architecture ensures the platform is secure, scalable, and easy to extend as new features are introduced.
