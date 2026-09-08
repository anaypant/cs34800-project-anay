# CS348-AI-Anay

Anay Pant  
CS 34800 — Fall 2026  
Instructor: Blaine Rothrock  

This file discloses how I used AI on Project Stage 1, as required by the Stage 1 assignment (“You may use AI for this deliverable; if you do, disclose how you used it in a separate file”) and the course AI policy (AI is allowed on the application project for coding assistance and planning; technical decisions made with AI must be disclosed and justified).

## What I used

I used Cursor as a coding agent (model: Grok 4.6) in this workspace. I did not use AI for the Stage 1 written project plan. That write-up was my own. I also did not use AI to create the required demo video.

## What AI did on this deliverable

I asked the agent to:

1. Treat `C:\Users\anayp\cs34800-project-anay` as my main Cursor project for this course.
2. Read the syllabus (`syl-348.pdf`), Stage 1 assignment (`ps1-348.pdf`), and my own Stage 1 write-up so the workspace matched the assignment.
3. Scaffold a Next.js app (App Router, TypeScript, Tailwind) as the Stage 1 “hello world” stack proof.
4. Replace the default create-next-app homepage with a page that displays **cs34800 project anay**, so the submission is clearly edited and not an untouched template.
5. Create this disclosure file from the Stage 1 and syllabus AI rules.

I reviewed the generated files, confirmed the homepage text, and kept this disclosure in my own words.

## Technical decisions (and what AI did vs. what I decided)

These stack choices are mine from the Stage 1 write-up. I already knew Next.js and want to use SQL more directly with Supabase over the semester.

| Decision | Who decided | Why |
| --- | --- | --- |
| Next.js (App Router) + TypeScript | Me | I am most familiar with this frontend stack, which satisfies Stage 1’s “pick a web or mobile stack and install it” requirement. The stack can change later if needed. |
| Tailwind CSS | create-next-app default / agent scaffold | Included by the official Next.js starter. I accepted it because it is the usual Next.js setup and I already use it. |
| Vercel for hosting (later) | Me | Matches Next.js and is the hosting plan in my write-up. Not configured in Stage 1. |
| Supabase / Postgres (later) | Me | Needed for NFL data, multiple related tables, and the course SQL requirements. Not installed in Stage 1; the assignment says not to design or install the database yet. |

AI did not invent the product idea (NFL / football companion site). It only helped install the web stack and make the homepage an obvious student edit.

## Distinguishing alterations

The default create-next-app homepage (Next.js logo, “To get started, edit the page.tsx file,” Deploy / Documentation links) was removed. The homepage is a single heading: **cs34800 project anay**. The document title was changed from “Create Next App” to “CS34800 Project Anay.”

## What I will not use AI for

Per the syllabus and Stage 1 rubric:

- I will not use AI when I am asked to write *about* the project (write-ups, explanations).
- I will not use AI to produce the demo video or its audio.
- I will not use AI on homework, in-class participation, or exams.

I am responsible for understanding any code the agent helps produce. Later stages will keep updating this file when AI is used again.
