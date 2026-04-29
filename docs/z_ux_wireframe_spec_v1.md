# Z-UX Wireframe Spec v1

Agent:
Z-UX

Purpose:
Define the first implementation-ready mobile wireframe structure for the ZILFIT customer journey.

Scope:
This spec covers the first conversion-focused user flow for:
- scan intake
- fit summary
- recommendation
- checkout
- post-purchase feedback

Hero Product:
ZILFIT VITAL-RECOVER

Design Rules:
- mobile-first
- one hero product
- one primary CTA per screen
- minimal text
- high clarity
- high trust
- no medical-treatment language
- fast path to checkout
- clear scan guidance
- easy retry paths

## Screen 1 — Welcome
Screen ID:
welcome_first_impression

Goal:
Create immediate understanding and trust.

Layout Blocks:
- logo / brand
- hero headline
- short supporting text
- one primary CTA
- optional trust strip

Headline:
Smart footwear, guided by your foot profile.

Supporting Text:
A fast guided experience to help us match your foot shape, movement, and comfort needs.

Primary CTA:
Start my fit

Secondary CTA:
None

Z-Guide Message:
Welcome — I’ll guide you through a quick foot scan and help you find your best ZILFIT fit.

Inputs:
None

Outputs:
- session_start

Error States:
None

Notes:
Keep first screen clean and visually calm.

---

## Screen 2 — Goal Selection
Screen ID:
goal_selection

Goal:
Identify the user’s main intent in one step.

Layout Blocks:
- short title
- 4 selectable goal cards
- continue CTA

Title:
What are you mainly looking for today?

Options:
- Recovery after activity
- Daily comfort
- Standing fatigue
- Women-specific comfort

Primary CTA:
Continue

Secondary CTA:
Back

Z-Guide Message:
Choose the goal that best matches what you want today.

Inputs:
- user_goal_selection

Outputs:
- user_goal

Error States:
- no option selected

Notes:
Do not show too many choices.

---

## Screen 3 — Guided Scan Intro
Screen ID:
guided_scan_intro

Goal:
Prepare the user for the scan process without confusion.

Layout Blocks:
- short intro title
- preparation checklist
- scan steps preview
- start CTA

Title:
Your scan takes about 1 minute

Preparation Checklist:
- your foot
- a plain sheet or reference surface
- good lighting

Scan Preview:
- top view
- side view
- optional short walking clip

Primary CTA:
Start scan

Secondary CTA:
Back

Z-Guide Message:
Keep it simple — I’ll show you exactly what to do at each step.

Inputs:
None

Outputs:
- scan_intent_started

Error States:
None

Notes:
Use icons and visual guidance more than text.

---

## Screen 4A — Top View Capture
Screen ID:
scan_capture_top

Goal:
Capture foot outline for length and width estimation.

Layout Blocks:
- camera frame
- short instruction
- capture CTA
- retry / back action

Instruction:
Place your foot flat and keep the full outline visible.

Primary CTA:
Capture top view

Secondary CTA:
Back

Z-Guide Message:
Make sure your whole foot is visible inside the frame.

Inputs:
- top_view_image

Outputs:
- top_image

Error States:
- foot cropped
- low light
- blur
- reference missing

Notes:
Show outline overlay in camera frame.

---

## Screen 4B — Side View Capture
Screen ID:
scan_capture_side

Goal:
Capture side profile for heel and arch estimation.

Layout Blocks:
- camera frame
- short instruction
- capture CTA
- retry / back action

Instruction:
Turn slightly sideways and keep the heel and arch visible.

Primary CTA:
Capture side view

Secondary CTA:
Back

Z-Guide Message:
Keep your heel and arch visible for a better profile read.

Inputs:
- side_view_image

Outputs:
- side_image

Error States:
- heel hidden
- arch hidden
- blur
- low light

Notes:
Keep instruction short and visual.

---

## Screen 4C — Optional Gait Clip
Screen ID:
scan_capture_gait_optional

Goal:
Allow optional movement capture for a better profile.

Layout Blocks:
- short explanation
- record CTA
- skip CTA

Instruction:
Walk a few natural steps if you’d like a better movement profile.

Primary CTA:
Record short walk

Secondary CTA:
Skip

Z-Guide Message:
This step is optional, but it may help improve movement-related guidance.

Inputs:
- optional_gait_video

Outputs:
- optional_gait_clip

Error States:
- unstable recording
- too dark
- subject out of frame

Notes:
Keep this optional to avoid friction.

---

## Screen 5 — Scan Quality Check
Screen ID:
scan_quality_check

Goal:
Approve usable scan input or request retry.

Layout Blocks:
- scan status
- brief reason if failed
- success or retry CTA

Success Copy:
Scan looks good

Retry Copy:
We need a clearer image

Possible Failure Reasons:
- foot not fully visible
- too dark
- blurry image
- missing reference

Primary CTA Success:
See my result

Primary CTA Failure:
Retake

Secondary CTA:
Back

Z-Guide Message:
I’m checking image quality so your fit result is more reliable.

Inputs:
- top_image
- side_image
- optional_gait_clip

Outputs:
- scan_quality_score
- scan_status

Error States:
- failed_quality_check

Notes:
Show one clear reason at a time.

---

## Screen 6 — Smart Result Summary
Screen ID:
smart_result_summary

Goal:
Show a simple, non-medical fit summary.

Layout Blocks:
- summary title
- 3 to 4 bullet insights
- recommendation CTA

Title:
Your fit summary

Summary Fields:
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

Secondary CTA:
Back

Z-Guide Message:
Here’s a simple summary based on your scan and selected goal.

Inputs:
- fit_processing_packet

Outputs:
- fit_summary_packet

Error States:
- incomplete_summary
- low_confidence_summary

Notes:
Avoid clinical or diagnostic tone.

---

## Screen 7 — Product Recommendation
Screen ID:
product_recommendation

Goal:
Recommend one clear product path.

Layout Blocks:
- recommended product card
- short why explanation
- primary checkout CTA
- secondary summary review CTA

Recommendation Title:
Recommended for you:
ZILFIT VITAL-RECOVER

Explanation:
Based on your scan and your goal, this path best matches recovery-focused comfort and foot guidance.

Primary CTA:
Continue to checkout

Secondary CTA:
Review my fit summary

Z-Guide Message:
This is the clearest first match for your current profile.

Inputs:
- fit_summary_packet
- recommendation_logic

Outputs:
- recommended_product
- recommendation_confidence

Error States:
- low_recommendation_confidence
- missing_product_mapping

Notes:
Do not show multiple competing products here.

---

## Screen 8 — Fast Checkout
Screen ID:
fast_checkout

Goal:
Complete purchase with minimal friction.

Layout Blocks:
- product summary
- fit summary snippet
- price
- express payment options
- shipping form
- pay CTA

Rules:
- no forced account creation
- no long explanatory text
- no early product branching

Primary CTA:
Pay now

Secondary CTA:
Back

Z-Guide Message:
You’re almost done — keep it quick and simple.

Inputs:
- selected_product
- fit_summary_packet
- shipping_info
- payment_method

Outputs:
- order_created
- payment_status
- shipping_info_confirmed

Error States:
- payment_failed
- invalid_address
- incomplete_shipping_info

Notes:
Prioritize Apple Pay / Google Pay if available.

---

## Screen 9 — Order Confirmation
Screen ID:
order_confirmation

Goal:
Confirm purchase and reinforce trust.

Layout Blocks:
- confirmation title
- order number
- next steps
- done CTA

Title:
Your ZILFIT order is confirmed

Copy:
We’ve received your order and fit profile. Your next update will include order progress and follow-up guidance.

Primary CTA:
Done

Secondary CTA:
Track order

Z-Guide Message:
Thank you — your fit data and order are now in progress.

Inputs:
- successful_order_data

Outputs:
- order_confirmation
- tracking_initialized

Error States:
None

Notes:
Reassure the user that both order and fit data were saved.

---

## Screen 10 — Post-Purchase Follow-up
Screen ID:
post_purchase_followup

Goal:
Collect structured comfort feedback after use.

Layout Blocks:
- comfort score
- issue zone selector
- simple questions
- submit CTA

Questions:
- How does it feel so far?
- Comfort from 1 to 10
- Any pressure points?
- Better after activity?
- Need adjustment review?

Primary CTA:
Submit feedback

Secondary CTA:
Skip for now

Z-Guide Message:
Your feedback helps us improve fit, comfort, and future design updates.

Inputs:
- comfort_score
- issue_zones
- recovery_feedback
- adjustment_request

Outputs:
- comfort_score_saved
- issue_zones_saved
- satisfaction_trend
- adjustment_request_logged

Error States:
- empty_submission
- invalid_score_range

Notes:
Keep this short to increase completion rate.

---

## Agent Routing Logic

After Smart Result Summary:
- send fit_summary_packet to Z-Claims
- send fit_summary_packet to Z-Sim
- send fit_summary_packet to Z-CAD

After Product Recommendation:
- keep recommendation wording aligned with Z-Claims policy

After Checkout:
- store fit and order data for later review

After Post-Purchase Follow-up:
- send feedback packet to Z-UX
- send feedback packet to Z-Claims
- send feedback packet to Z-Sim
- send feedback packet to Z-CAD

## Conversion Principles
- one main action per screen
- low text density
- visible progress
- strong trust cues
- short scan instructions
- retry without frustration
- checkout in the fewest possible steps

## Success Standard
A first-time user should be able to:
1. understand the value quickly
2. choose a goal quickly
3. complete scan steps clearly
4. receive one understandable recommendation
5. pay with minimal friction
6. submit follow-up feedback after use

## Status
READY_FOR_HERMES_REVIEW
