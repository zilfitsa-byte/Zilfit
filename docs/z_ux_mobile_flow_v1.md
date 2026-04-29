# Z-UX Mobile Flow v1

Agent:
Z-UX

Mission:
Design the first conversion-focused mobile app flow for ZILFIT.

Primary Goal:
Help a first-time user understand the product quickly, complete a guided foot scan, receive a simple recommendation, and finish checkout with minimal friction.

Hero Product:
ZILFIT VITAL-RECOVER

Flow Principles:
- mobile-first
- one hero product
- one guided path
- minimal text
- high trust
- no medical overclaiming
- fast checkout
- clear CTA hierarchy

## Screen 1 — Welcome / First Impression
Goal:
Create immediate clarity and confidence.

User sees:
- ZILFIT brand
- short value proposition
- one primary CTA

Suggested Headline:
Smart footwear, guided by your foot profile.

Suggested Subtext:
A fast guided experience to help us match your foot shape, movement, and comfort needs.

Primary CTA:
Start my fit

Z-Guide Prompt:
Welcome — I’ll guide you through a quick foot scan and help you find your best ZILFIT fit.

System Event:
session_start

---

## Screen 2 — Goal Selection
Goal:
Identify the user's primary intent quickly.

User sees:
- Recovery after activity
- Daily comfort
- Standing fatigue
- Women-specific comfort

Primary CTA:
Continue

Z-Guide Prompt:
What are you mainly looking for today?

System Data:
user_goal

---

## Screen 3 — Guided Scan Intro
Goal:
Prepare the user for scanning without confusion.

User sees:
- short preparation steps
- simple illustration
- reassurance of speed

Suggested Copy:
You’ll need:
- your foot
- a plain sheet or reference surface
- 1 minute

We’ll capture:
- top view
- side view
- optional short walking clip

Primary CTA:
Start scan

Z-Guide Prompt:
Keep it simple — I’ll show you exactly what to do at each step.

System Event:
scan_intent_started

---

## Screen 4 — Scan Capture
Goal:
Collect the required scan inputs.

### 4A — Top View
Prompt:
Place your foot flat and keep the full outline visible.

CTA:
Capture top view

### 4B — Side View
Prompt:
Turn slightly sideways and keep the heel and arch visible.

CTA:
Capture side view

### 4C — Optional Gait Video
Prompt:
Walk a few natural steps if you’d like a better movement profile.

CTA:
Record short walk

Z-Guide Prompt:
Great — just follow the frame and keep your foot clearly visible.

System Data:
- top_image
- side_image
- optional_gait_clip

---

## Screen 5 — Scan Quality Check
Goal:
Block weak scans and allow only usable scan data.

Success Copy:
Scan looks good

Retry Copy:
We need a clearer image

Possible Error Reasons:
- foot not fully visible
- too dark
- blurry image
- missing reference

Success CTA:
See my result

Retry CTA:
Retake

Z-Guide Prompt:
I’m checking image quality so your fit result is more reliable.

System Data:
- scan_quality_score
- scan_status

---

## Screen 6 — Smart Result Summary
Goal:
Show a simple, non-medical summary.

User sees:
- estimated length profile
- width profile
- comfort priority
- movement note

Example Summary:
Estimated fit profile:
- Standard length
- Slightly wider forefoot
- Recovery-focused comfort suggested

Primary CTA:
See my recommendation

Z-Guide Prompt:
Here’s a simple summary based on your scan and selected goal.

System Data:
fit_summary_packet

---

## Screen 7 — Product Recommendation
Goal:
Recommend one clear product path.

User sees:
Recommended for you:
ZILFIT VITAL-RECOVER

Suggested Explanation:
Based on your scan and your goal, this path best matches recovery-focused comfort and foot guidance.

Primary CTA:
Continue to checkout

Secondary CTA:
Review my fit summary

Z-Guide Prompt:
This is the clearest first match for your current profile.

System Data:
- recommended_product
- recommendation_confidence

---

## Screen 8 — Fast Checkout
Goal:
Complete purchase with minimal friction.

User sees:
- selected product
- fit summary
- price
- Apple Pay / Google Pay
- shipping details

Rules:
- no forced account creation
- no long explanation blocks
- no early multi-product branching

Primary CTA:
Pay now

Z-Guide Prompt:
You’re almost done — keep it quick and simple.

System Data:
- order_created
- payment_status
- shipping_info

---

## Screen 9 — Order Confirmation
Goal:
Confirm success and reinforce trust.

User sees:
Your ZILFIT order is confirmed

Suggested Copy:
We’ve received your order and fit profile. Your next update will include order progress and follow-up guidance.

Primary CTA:
Done

Z-Guide Prompt:
Thank you — your fit data and order are now in progress.

System Data:
order_confirmation

---

## Screen 10 — Post-Purchase Follow-up
Goal:
Capture comfort and usage feedback for improvement.

User sees:
- comfort rating
- pressure point question
- recovery question
- adjustment request option

Questions:
- How does it feel so far?
- Comfort from 1 to 10
- Any pressure points?
- Better after activity?
- Need adjustment review?

Primary CTA:
Submit feedback

Z-Guide Prompt:
Your feedback helps us improve fit, comfort, and future design updates.

System Data:
- comfort_score
- issue_zones
- satisfaction_trend
- adjustment_request

---

## Backend Routing Notes
After result summary and recommendation:
- route fit packet to Z-Claims
- route fit packet to Z-Sim
- route fit packet to Z-CAD
- route execution notes later to Z-Printability

After post-purchase follow-up:
- route feedback to Z-UX
- route feedback to Z-Claims
- route feedback to Z-Sim
- route feedback to Z-CAD

## Success Standard
The user should be able to:
1. understand the product quickly
2. complete scan intake without confusion
3. receive one clear recommendation
4. complete checkout fast
5. submit feedback after use

## Status
READY_FOR_HERMES_REVIEW
