# Z-Guide Prompt Pack v1

Agent:
Z-Guide

Purpose:
Provide live in-app prompt messages for the first ZILFIT customer journey.

Tone:
- calm
- human
- concise
- premium
- supportive
- non-medical
- confidence-building
- low-friction

Global Rules:
- keep prompts short
- do not sound robotic
- do not sound clinical
- do not make treatment claims
- do not overload the user with too much instruction at once
- always focus on the next immediate step

## Prompt Group 1 — Welcome

Trigger:
welcome_first_impression

Primary Prompt:
Welcome — I’ll guide you through a quick foot scan and help you find your best ZILFIT fit.

Alternative Prompt 1:
Let’s make this simple — I’ll guide you step by step.

Alternative Prompt 2:
You’re in the right place. We’ll keep this quick and clear.

Fallback Prompt:
I’m here to guide you through the next step.

---

## Prompt Group 2 — Goal Selection

Trigger:
goal_selection

Primary Prompt:
What are you mainly looking for today?

Alternative Prompt 1:
Choose the goal that feels closest to what you want today.

Alternative Prompt 2:
Start with the goal that best matches your current need.

Fallback Prompt:
Please choose one option to continue.

---

## Prompt Group 3 — Scan Intro

Trigger:
guided_scan_intro

Primary Prompt:
Keep it simple — I’ll show you exactly what to do at each step.

Alternative Prompt 1:
Your scan only takes about a minute.

Alternative Prompt 2:
Good lighting and a clear foot view will help a lot.

Fallback Prompt:
I’ll guide you through the scan step by step.

---

## Prompt Group 4 — Top View Capture

Trigger:
scan_capture_top

Primary Prompt:
Place your foot flat and keep the full outline visible.

Alternative Prompt 1:
Try to keep your whole foot inside the frame.

Alternative Prompt 2:
A clear top view helps us build a better fit profile.

Fallback Prompt:
Please capture a clear top view.

---

## Prompt Group 5 — Side View Capture

Trigger:
scan_capture_side

Primary Prompt:
Turn slightly sideways and keep the heel and arch visible.

Alternative Prompt 1:
A clear side view helps us read your profile more clearly.

Alternative Prompt 2:
Keep the frame steady and your heel visible.

Fallback Prompt:
Please capture a clear side view.

---

## Prompt Group 6 — Optional Gait Clip

Trigger:
scan_capture_gait_optional

Primary Prompt:
This step is optional, but it may help improve movement-related guidance.

Alternative Prompt 1:
A short natural walking clip can give us a better movement profile.

Alternative Prompt 2:
You can skip this step if you want to keep moving quickly.

Fallback Prompt:
You can record a short walk or skip this step.

---

## Prompt Group 7 — Scan Quality Pass

Trigger:
scan_quality_check_success

Primary Prompt:
Your scan looks good — we can continue.

Alternative Prompt 1:
Great, your scan quality is clear enough for the next step.

Alternative Prompt 2:
That worked well. Let’s move on.

Fallback Prompt:
Your scan is ready.

---

## Prompt Group 8 — Scan Quality Retry

Trigger:
scan_quality_check_failure

Primary Prompt:
We need a clearer image so your fit result is more reliable.

Alternative Prompt 1:
Let’s try that again with a clearer view.

Alternative Prompt 2:
A better scan usually leads to a better fit summary.

Fallback Prompt:
Please retake the scan.

---

## Prompt Group 9 — Fit Summary

Trigger:
smart_result_summary

Primary Prompt:
Here’s a simple summary based on your scan and selected goal.

Alternative Prompt 1:
This is a fit-oriented summary to help guide your next step.

Alternative Prompt 2:
We’ve turned your scan into a simple fit profile.

Fallback Prompt:
Here is your fit summary.

---

## Prompt Group 10 — Recommendation

Trigger:
product_recommendation

Primary Prompt:
This is the clearest first match for your current profile.

Alternative Prompt 1:
Based on your scan and goal, this is the best first path to start with.

Alternative Prompt 2:
We’re starting with one clear recommendation to keep things simple.

Fallback Prompt:
Here’s your recommended product.

Low Confidence Prompt:
This is a lighter-confidence match and may improve with a clearer scan.

---

## Prompt Group 11 — Checkout

Trigger:
fast_checkout

Primary Prompt:
You’re almost done — keep it quick and simple.

Alternative Prompt 1:
Your selected product and fit summary are ready for checkout.

Alternative Prompt 2:
You can finish this without adding extra steps.

Fallback Prompt:
You’re ready to complete checkout.

---

## Prompt Group 12 — Payment Retry

Trigger:
checkout_payment_failure

Primary Prompt:
Your payment didn’t go through. Please try again.

Alternative Prompt 1:
Something interrupted the payment. Let’s try once more.

Alternative Prompt 2:
Your order is not complete yet — please retry payment.

Fallback Prompt:
Please try the payment again.

---

## Prompt Group 13 — Order Confirmation

Trigger:
order_confirmation

Primary Prompt:
Thank you — your fit data and order are now in progress.

Alternative Prompt 1:
Your order is confirmed and the next update will follow soon.

Alternative Prompt 2:
You’re all set. We’ve saved your order and fit profile.

Fallback Prompt:
Your order has been confirmed.

---

## Prompt Group 14 — Post-Purchase Feedback

Trigger:
post_purchase_followup

Primary Prompt:
Your feedback helps us improve fit, comfort, and future design updates.

Alternative Prompt 1:
How does it feel so far?

Alternative Prompt 2:
A quick check-in helps us improve the experience.

Fallback Prompt:
Please share your feedback when you’re ready.

## Escalation Rule

If wording feels uncertain:
Route through Z-Claims before public use.

If prompt may imply diagnosis:
Block and rewrite.

If prompt becomes too long:
Compress to one sentence and one action.

## Status
READY_FOR_HERMES_REVIEW
