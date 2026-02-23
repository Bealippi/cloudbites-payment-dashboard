# Business Impact Summary

CloudBites's support team handles 50+ daily tickets where customers report payment discrepancies — charges that appear on their bank statement but show as "Pending" in CloudBites, or refunds that processors completed but CloudBites never recorded. Each ticket requires an agent to manually log into one of three processor dashboards (PayFlow, StripeConnect, or LatamPay), locate the transaction using a different ID format, mentally translate the processor's status naming into CloudBites' terminology, and determine whether the internal record needs correction. This process takes 10-15 minutes per ticket.

The Payment Visibility Dashboard eliminates this manual cross-referencing by automatically querying all three processors, normalizing their different response formats into a unified view, and flagging status mismatches with severity classification. Agents can now detect and resolve ghost transactions in under 30 seconds with one-click reconciliation — reducing the daily ticket resolution time from 8+ hours to under 30 minutes.

## Domain Insights Beyond Status Matching

Real-world payment reconciliation involves more than comparing status strings. This dashboard addresses three categories of discrepancy that commonly cause revenue leakage in multi-processor architectures:

**1. Amount mismatches from unit conversion errors.** PayFlow and StripeConnect report amounts in minor units (cents), while LatamPay uses major units (decimal). A bug in the webhook handler that stores `15000` as `$15,000.00` instead of `$150.00` would be invisible in status-only reconciliation but immediately flagged by the amount mismatch detector. In production, this class of bug accounts for a disproportionate share of financial discrepancies because it passes all status checks.

**2. Ghost transactions from race conditions.** When a processor approves a payment but the webhook delivery fails (network timeout, queue backup, deployment during webhook), the internal DB stays at PENDING while the customer is charged. The severity classifier treats these MISSED_WEBHOOK cases as HIGH because they directly impact customer trust — the customer sees a charge but CloudBites shows no confirmation. The inverse (internal SUCCEEDED, processor DECLINED) is CRITICAL because it means CloudBites may have fulfilled an order that was never actually paid.

**3. Untracked refunds from out-of-band operations.** Processors allow merchants to issue refunds directly from their dashboards, bypassing CloudBites entirely. Without reconciliation, these refunds create phantom revenue in CloudBites's reporting. The UNTRACKED_REFUND classification catches these by detecting internal=SUCCEEDED when the processor reports REFUNDED.

These three patterns — unit conversion drift, webhook delivery failures, and out-of-band mutations — represent the most common sources of financial discrepancy in payment orchestration platforms. Catching them automatically is what transforms this from a status comparison tool into an operational safety net.
