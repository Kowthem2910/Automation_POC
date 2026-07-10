---
id: KB0002187
title: Restarting a hung Apache service
category: Infrastructure > Web Servers
last_reviewed: 2026-04-20
---

If a web application is returning 502/503 errors and monitoring shows
the Apache process is unresponsive:

1. Confirm the affected host in NetBox and check for any linked active
   incidents before restarting.
2. A restart can be requested through the ITSM Assistant chatbot using
   the approved "restart-apache-service" automation, which requires
   approval and is logged to the ticket audit trail.
3. Manual restart via SSH is only permitted for on-call engineers
   outside business hours per the standard change policy.
