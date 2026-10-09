# Requirements questionnaire (draft)

**Purpose:** find out what intended users track today, what puts them off logging, and what feedback they want, so you can confirm the priorities in the proposal. Scope stays as submitted.

**Before sending:** get the answer from your supervisor on ethics clearance (ticket T-07), pilot it with two people, and build it in a form tool that does not collect email addresses or names. Aim for about 5 minutes and a target of around 30 responses. Recruit a convenience sample (for example gym-going students) and state that limitation in the report.

## Page 1: Introduction and consent (show before any question)

> **AdaptFit requirements survey**
> I am a Software Engineering student at USIU working on a fitness app project. This 5-minute survey asks about your training and tracking habits and what you would want from a fitness app.
> - Taking part is voluntary and you can stop at any time.
> - It is anonymous: please do not enter your name or contact details.
> - Answers are used only for this course project and are reported in summary form.
> - I do not ask about medical conditions.
>
> To take part, please confirm all of the following:
> - [ ] I am between 18 and 40 years old.
> - [ ] I train with weights, or plan to start.
> - [ ] I have no medical condition that limits my exercise.
> - [ ] I agree to take part.

If someone does not tick all four boxes, end the form with a thank-you message. This keeps sensitive health details out of your data, in line with the Kenya Data Protection Act (Republic of Kenya, 2019).

## Questions

| # | Question | Answer type and options | Informs |
|---|---|---|---|
| **A. Your training** | | | |
| 1 | How long have you been training? | Not started yet / under 6 months / 6-24 months / over 2 years | beginner vs experienced needs |
| 2 | How many sessions do you do in a typical week? | 0-1 / 2-3 / 4-5 / 6 or more | onboarding schedule, FR-3 |
| 3 | Which age group are you in? | 18-24 / 25-29 / 30-34 / 35-40 | sample description |
| **B. Tracking today** | | | |
| 4 | What do you track now? | Multi-select: workouts, body weight, sleep, food, none, other | which inputs matter, FR-3 |
| 5 | Which apps or tools do you use? | Open text (optional) | similar-systems review |
| 6 | Have you stopped using a fitness or tracking app? Why? | Multi-select: took too much time, I forgot, no visible results, felt boring, privacy worries, cost, never tried one, other | logging burden, dropout |
| 7 | How much time per week would you spend logging in an app you liked? | Under 2 min / 2-5 min / 5-10 min / over 10 min | weekly check-in length, NFR-3 |
| 8 | Having to log every day would put me off. | 1-5 agree scale | weekly vs daily logging |
| 9 | How would you prefer to log a session? | Tap options from a list / type it in / tick "done as planned" | FR-6, check-in design |
| **C. Feedback** | | | |
| 10 | What feedback would keep you going? | Multi-select: weekly progress summary, trends over time, suggestions for next week, reminders, comparison with past weeks, other | FR-9, FR-12, FR-13 |
| 11 | How often do you want suggestions? | Daily / weekly / monthly / only when I ask | suggestion cadence |
| 12 | I want to see why a suggestion was made. | 1-5 agree scale | FR-14, NFR-7 |
| **D. AI and privacy** | | | |
| 13 | I am comfortable receiving training suggestions written by AI. | 1-5 agree scale | LLM layer acceptance |
| 14 | I would trust AI suggestions more if they showed the evidence behind them. | 1-5 agree scale | evidence display, NFR-7 |
| 15 | Summary numbers (such as weekly adherence and weight trend, without your name or email) could be sent to an external AI service. | Fine / only if I agree each time / not at all | NFR-6, consent design |
| 16 | What worries you about sharing fitness data with an app? | Multi-select: who can see it, it being sold, it being wrong, data cost, nothing, other | privacy requirements |
| **E. Anything else** | | | |
| 17 | What would make you use, or stop using, an app like this? | Open text (optional) | free-form priorities |

## After the responses come in (ticket T-24)

1. Count each question and put the results in one summary table.
2. Pull out the three findings that change a priority, for example how long people will spend logging or whether they accept AI-written text.
3. Record what you changed in the requirements as a result, and what you did not change because the scope is locked.
4. In the report, list the sample size, how you recruited, and the limitations (convenience sample, self-reported answers).
