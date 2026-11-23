# Demo script (about 5 minutes)

**Before you start:** `docker compose up -d`, open http://localhost:3000 in two windows (one normal, one private), have an analyst login and an admin login ready (`data/interim/credentials-*.txt`). Use only the made-up domains below. Never paste a real scam link on stage.

| Min | Do | Say | If it goes wrong |
|---|---|---|---|
| 0:00 | Home page | "Scam links reach people by SMS and search. FraudShield checks a link before you open it and says why." | Reload; the stack takes ~15 s after `up`. |
| 0:30 | Paste `https://adcb-secure-login.example.com/verify`, Check | "It never opens the page for this check. It reads the address: a bank's name on a domain that is not the bank's, pressure words, and a statistical hint." Point at the score, the plain-language paragraph, and the reasons with points. | If the score differs slightly, the point stands; read the reasons. |
| 1:15 | Paste `https://www.adcb.com/personal` | "The real bank scores low. Official domains are capped." | |
| 1:30 | **Sign in as analyst first (deep scan is staff only).** **Local backend only, not Docker** (the container cannot reach your laptop's staged server): run `scripts/start_staged_sites.py`, start the backend with `FRAUDSHIELD_SANDBOX_ALLOW_HOSTS=127.0.0.1`, tick the safe-browser box and scan the staged lookalike page | "For a deeper look it opens the page in an isolated browser: no downloads, no form is ever submitted, internal addresses blocked." Show the fake login form flagged. | Skip this minute when demoing from Docker (deep scan itself works there, just not against a staged page on the host). |
| 2:15 | Sign in as analyst, open Early detection | "Before anyone reports a scam, we watch newly issued certificates. This feed is a **simulated sample** for the demo." Point at the triage queue ranked by risk and exposure. | Say "simulated" out loud. |
| 2:45 | Open a case from a queue item | "Cases follow a fixed path. Every status change needs a reason and is recorded." Move to Under review. | |
| 3:15 | Freeze evidence, Verify hash, create a takedown draft | "Evidence is hashed so any later change is detectable. The draft says 'suspected' until a person confirms. FraudShield never sends anything." Show NOT YET CONFIRMED wording. | |
| 3:50 | Private window: `/report`, send a report | "Citizens can report a link; it is scored and joins the queue. Reports raise priority but never block anything by themselves." | |
| 4:15 | Sign in as admin: Scoring page, lower a weight, Preview | "Admins tune the scoring without redeploying. The preview re-scores recent scans first. Every change needs a reason and is audited." Do not save, or save and reset. | |
| 4:45 | Audit log | "Who did what and when. It cannot be edited from the interface." | |
| 5:00 | Done | Close with the honest limits (below). | |

**Say the limits yourself before a judge asks:** early detection runs on simulated certificate data here; accuracy has not been measured on real UAE data; evidence is the analysis, not screenshots yet; the URL model is a weak extra signal.

**Backup:** record a screen capture of one clean run (outside the repo) before the day.
