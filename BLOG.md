# Sehat Sathi: Building a Voice Agent for Health Access in Bharat

*A 10-day journey building a multilingual health-access voice assistant with Murf Falcon, LiveKit, and a lot of trial and error.*

## The Problem and the Users

Most voice AI is built for people who already have smartphones, fast data plans, and comfort with English. That leaves out a huge number of people in India - someone in a small town with a mild fever who does not know if it is serious, a family member trying to find the nearest government hospital, or a caller who just needs to know whether to rest at home or see a doctor today.

That is the gap Sehat Sathi ("Health Companion") tries to fill. It is a voice-first health access assistant for the Health Access track of the 10 Days of Voice Agents - VoiceForBharat Edition challenge, run by Murf AI. The idea is simple: you should be able to just talk to it, in Hindi, English, or a natural mix of both, and get safe, honest guidance - not a diagnosis, but a clear next step.

## What the Voice Agent Does

Over ten days, Sehat Sathi grew from a simple talking demo into a system that can:

- Hold a natural, code-mixed Hindi-English conversation in an Indian voice
- Remember returning callers and pick up where the last conversation left off
- Look up the nearest government hospital by district
- Recognize when a symptom is serious enough to need a human, and escalate it - with the caller's permission
- Place real outbound phone calls with a proper, honest opening
- Track whether calls are actually succeeding, on a live dashboard
- Hand off appointment-booking questions to a dedicated specialist agent

## How the System Works

The core pipeline is the same shape used across the whole challenge:

Speech-to-Text -> LLM -> Text-to-Speech -> Real-time transport

- STT: Deepgram (nova-3, in multilingual mode) turns the caller's voice into text, correctly handling Hindi, English, and code-mixed speech in the same sentence.
- LLM: Google Gemini reasons about what the caller needs, decides when to call a tool, and writes replies in the caller's own language and script (Devanagari for Hindi, never romanized).
- TTS: Murf Falcon, using the Indian English voice Anisha, turns replies into natural-sounding speech with very low latency - Murf's TTFB (time-to-first-audio) consistently came in around 110-150ms in testing.
- Transport: LiveKit handles the real-time audio room, and later, SIP telephony for outbound phone calls over a Linphone SIP trunk.

## The Most Important Features

**An Indian voice, not a translated one.** Early on, hardcoding the voice's locale caused Hindi words to come out with an English accent. The fix was to not hardcode the locale at all, and instead set the STT to multilingual mode and let the voice adapt per sentence - a small config change that made every conversation sound dramatically more natural.

**Guardrails with a spine.** The agent will never diagnose a condition or name a specific medicine. If someone describes a red-flag symptom - chest pain, trouble breathing, heavy bleeding - it stops and tells them clearly to seek in-person or emergency care.

**Memory, with consent.** Before saving anything about a caller, the agent explicitly asks permission. If they say no, nothing is saved. Returning callers are greeted by name and the conversation continues naturally.

**A real tool with an honest fallback.** The facility-lookup tool speaks results naturally instead of reading raw data, and always tells the caller this is from a static reference list, not a live source. When a district is not in the list, it says so honestly and redirects to the local ASHA worker or India's emergency ambulance number - it never invents a hospital name.

**Human escalation, not silent failure.** For red-flag symptoms or direct requests for a diagnosis, the agent explains exactly what it wants to send to a human, asks permission, and only then creates a short, privacy-safe summary - no raw transcripts, no private data - delivered to a real Discord channel with a reference ID the caller can hold onto.

**Outbound calls that introduce themselves properly.** Since an outbound call is unexpected for the person receiving it, the opening states clearly, in the first two sentences, who is calling, why, and how to make it stop.

**A dashboard with real numbers.** Total, successful, and failed calls are pulled live from the same database the agent writes to - nothing hardcoded, and no caller-identifying information is ever shown.

**A specialist for a narrower job.** A clinic-and-appointment specialist agent, Meera, takes over only for booking-related questions, picking up the existing conversation without asking the caller to repeat themselves - and hands back cleanly if they mention a new symptom.

## Challenges and How I Solved Them

**The accent problem.** As mentioned above, hardcoding locale="en-IN" in the TTS config made Hindi words sound foreign. Removing the hardcoded locale and switching STT to multilingual mode fixed it completely.

**Speech-to-text misheard names.** An uncommon name was transcribed inconsistently across calls, which broke the memory lookup since it searched under a different, misheard name each time. This was not a bug in the code - it was a genuine STT accuracy limitation - so the fix was to test with clearer, more common names and add alternate spellings to lookup data where it mattered.

**A deprecated model silently broke outbound calls mid-conversation.** The outbound agent used a Gemini model name that had been deprecated between the browser agent and the outbound agent being written - the greeting played fine, but every reply after that failed with a 404 from the API. The fix was simply matching the model name to the one already working in the main agent.

**Recording a phone call is harder than it sounds.** The Linphone app deliberately blocks screen recording during calls, a privacy measure most VOIP apps share. The workaround was to put the call on speakerphone and record the phone with a laptop's built-in webcam instead.

**Mobile hotspots and WebSocket streaming do not mix well.** TTS streaming needs a sustained connection; on an unstable hotspot, calls would time out a few messages in even though basic connectivity tests all passed. Understanding why sustained connections behave differently from quick pings made it clear this was not a code problem, just a network reality to work around.

## How to Build and Run This Yourself

1. Get the starter. Fork murf-ai/murf-livekit-starter on GitHub and clone it.
2. Install dependencies. Backend: uv sync (Python, via uv). Frontend: pnpm install (Node.js).
3. Add your API keys - never commit them. Copy .env.example to .env.local in both backend/ and frontend/, and fill in your own keys for LiveKit, Murf, Deepgram, and your LLM provider. .env.local is already excluded by .gitignore, so keys never reach the public repo.
4. Run it. From the repo root: ./start_app.ps1 (Windows) or ./start_app.sh (Mac/Linux) starts the backend agent and frontend together.
5. Talk to it. Open http://localhost:3000, click Start talking, allow microphone access, and speak.
6. Customize the prompt and voice. The system prompt and Murf voice both live in backend/src/agent.py.

## What I Would Improve Next

- A real, live facility-lookup API instead of the current hand-built reference list
- Automatic language detection for the dashboard, so it can break down success rates by language
- A "forget me" tool so callers can ask to have their data wiped, with visible confirmation

## Links

Public repository: https://github.com/subratgouda000/murf-livekit-starter

Built as part of 10 Days of Voice Agents - VoiceForBharat Edition by Murf AI, powered by Murf Falcon.

---

No API keys, phone numbers, or caller data are included in this post or in the linked repository.
