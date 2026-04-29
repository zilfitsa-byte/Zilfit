# Z-UX Microcopy Pack v1

Agent:
Z-UX

Purpose:
Provide implementation-ready microcopy for the first ZILFIT mobile customer journey.

Scope:
This pack covers:
- welcome
- goal selection
- scan onboarding
- scan capture
- scan validation
- fit summary
- recommendation
- checkout
- order confirmation
- post-purchase feedback

Tone Rules:
- calm
- clear
- premium
- supportive
- minimal
- human
- non-medical
- non-diagnostic
- confidence without exaggeration

Banned Writing Patterns:
- cures pain
- treats injury
- fixes gait
- medical grade result
- guaranteed improvement
- diagnostic result
- clinical correction
- hormone regulation
- injury prevention guarantee

## Screen 1 — Welcome

Screen ID:
welcome_first_impression

Headline:
Smart footwear, guided by your foot profile.

Subtext:
A fast guided experience to help us match your foot shape, movement, and comfort needs.

Primary CTA:
Start my fit

Support Copy:
Takes about 1 minute to begin.

Trust Copy:
Your scan is used to improve fit guidance and product matching.

Z-Guide Message:
Welcome — I’ll guide you through a quick foot scan and help you find your best ZILFIT fit.

---

## Screen 2 — Goal Selection

Screen ID:
goal_selection

Title:
What are you mainly looking for today?

Option 1:
Recovery after activity

Option 2:
Daily comfort

Option 3:
Standing fatigue

Option 4:
Women-specific comfort

Primary CTA:
Continue

Secondary CTA:
Back

Helper Text:
Choose the goal that feels closest to what you want today.

Z-Guide Message:
Choose the goal that best matches what you want today.

Error Copy:
Please select one option to continue.

---

## Screen 3 — Guided Scan Intro

Screen ID:
guided_scan_intro

Title:
Your scan takes about 1 minute

Preparation Title:
You’ll need

Preparation Items:
- your foot
- a plain sheet or reference surface
- good lighting

Capture Title:
We’ll capture

Capture Items:
- top view
- side view
- optional short walking clip

Primary CTA:
Start scan

Secondary CTA:
Back

Helper Text:
We’ll guide you step by step.

Z-Guide Message:
Keep it simple — I’ll show you exactly what to do at each step.

---

## Screen 4A — Top View Capture

Screen ID:
scan_capture_top

Title:
Capture top view

Instruction:
Place your foot flat and keep the full outline visible.

Primary CTA:
Capture top view

Secondary CTA:
Back

Retry CTA:
Retake

Helper Text:
Keep your whole foot inside the frame.

Z-Guide Message:
Make sure your whole foot is visible inside the frame.

Error Copy 1:
We couldn’t see the full foot clearly.

Error Copy 2:
Try again in brighter light.

Error Copy 3:
Please keep the reference area visible.

---

## Screen 4B — Side View Capture

Screen ID:
scan_capture_side

Title:
Capture side view

Instruction:
Turn slightly sideways and keep the heel and arch visible.

Primary CTA:
Capture side view

Secondary CTA:
Back

Retry CTA:
Retake

Helper Text:
A clear side view helps us read the profile more accurately.

Z-Guide Message:
Keep your heel and arch visible for a better profile read.

Error Copy 1:
Your heel is not fully visible.

Error Copy 2:
Your arch is unclear in this image.

Error Copy 3:
Please retake the image with steadier framing.

---

## Screen 4C — Optional Gait Clip

Screen ID:
scan_capture_gait_optional

Title:
Optional walking clip

Instruction:
Walk a few natural steps if you’d like a better movement profile.

Primary CTA:
Record short walk

Secondary CTA:
Skip

Helper Text:
This step is optional.

Z-Guide Message:
This step is optional, but it may help improve movement-related guidance.

Error Copy 1:
We couldn’t read the movement clearly.

Error Copy 2:
Try a steadier recording with better light.

---

## Screen 5 — Scan Quality Check

Screen ID:
scan_quality_check

Success Title:
Scan looks good

Success Text:
Your scan quality is good enough to continue.

Failure Title:
We need a clearer image

Failure Text:
A clearer scan helps us give you a better fit summary.

Primary CTA Success:
See my result

Primary CTA Failure:
Retake

Secondary CTA:
Back

Possible Failure Reason 1:
The foot is not fully visible.

Possible Failure Reason 2:
The image is too dark.

Possible Failure Reason 3:
The image is blurry.

Possible Failure Reason 4:
The reference area is missing.

Z-Guide Message:
I’m checking image quality so your fit result is more reliable.

---

## Screen 6 — Smart Result Summary

Screen ID:
smart_result_summary

Title:
Your fit summary

Summary Intro:
Here’s a simple summary based on your scan and selected goal.

Example Line 1:
Standard length profile

Example Line 2:
Slightly wider forefoot

Example Line 3:
Recovery-focused comfort suggested

Primary CTA:
See my recommendation

Secondary CTA:
Back

Helper Text:
This is a fit-oriented summary, not a medical result.

Z-Guide Message:
Here’s a simple summary based on your scan and selected goal.

Low Confidence Copy:
We have a lighter-confidence read here, so you may want to retake your scan for a clearer result.

---

## Screen 7 — Product Recommendation

Screen ID:
product_recommendation

Title:
Recommended for you

Product Name:
ZILFIT VITAL-RECOVER

Explanation:
Based on your scan and your goal, this path best matches recovery-focused comfort and foot guidance.

Primary CTA:
Continue to checkout

Secondary CTA:
Review my fit summary

Support Copy:
We’re starting with the clearest first match for your current profile.

Z-Guide Message:
This is the clearest first match for your current profile.

Low Confidence Copy:
This recommendation is a lighter-confidence match and may improve with a clearer scan.

---

## Screen 8 — Fast Checkout

Screen ID:
fast_checkout

Title:
Checkout

Section Label 1:
Your selected product

Section Label 2:
Fit summary

Section Label 3:
Shipping details

Primary CTA:
Pay now

Secondary CTA:
Back

Helper Text:
You can complete checkout without creating an account first.

Trust Copy:
Your fit profile and order details will be saved together for follow-up.

Z-Guide Message:
You’re almost done — keep it quick and simple.

Payment Error Copy:
Payment did not go through. Please try again.

Address Error Copy:
Please complete the shipping details to continue.

Field Hint:
Use the address where you’d like your ZILFIT order delivered.

---

## Screen 9 — Order Confirmation

Screen ID:
order_confirmation

Title:
Your ZILFIT order is confirmed

Body Copy:
We’ve received your order and fit profile. Your next update will include order progress and follow-up guidance.

Primary CTA:
Done

Secondary CTA:
Track order

Support Copy:
Thank you for starting your ZILFIT journey.

Z-Guide Message:
Thank you — your fit data and order are now in progress.

---

## Screen 10 — Post-Purchase Follow-up

Screen ID:
post_purchase_followup

Title:
How does it feel so far?

Question 1:
Comfort from 1 to 10

Question 2:
Any pressure points?

Question 3:
Does it feel better after activity?

Question 4:
Would you like an adjustment review?

Primary CTA:
Submit feedback

Secondary CTA:
Skip for now

Helper Text:
Your feedback helps us improve fit, comfort, and future design updates.

Z-Guide Message:
Your feedback helps us improve fit, comfort, and future design updates.

Success Copy:
Thank you — your feedback has been saved.

Empty State Error:
Please answer at least one item before submitting.

## Global Retry Messages

Retry Message 1:
Let’s try that again with a clearer image.

Retry Message 2:
A better scan usually leads to a better fit summary.

Retry Message 3:
Take your time — good lighting helps.

## Global Trust Messages

Trust Message 1:
Your scan is used to improve fit guidance and product matching.

Trust Message 2:
We keep the experience simple so you can move from scan to checkout without confusion.

Trust Message 3:
Your feedback helps improve future ZILFIT design updates.

## Global Writing Guard

Approved Style:
- simple
- direct
- premium
- supportive
- non-medical
- low-friction

Do Not Use:
- diagnostic language
- treatment claims
- guaranteed outcomes
- exaggerated performance promises

## Status
READY_FOR_HERMES_REVIEW
