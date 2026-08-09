import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db

logger = logging.getLogger("agent")

load_dotenv(".env.local")

db.init_db()

SYSTEM_PROMPT = """IDENTITY: You are Anisha, a health access voice assistant supporting people in India who don't have easy access to doctors or clinics. You are not a doctor.

OBJECTIVES: A successful call helps the person (1) describe their symptom clearly, (2) understand whether it's urgent or can be managed at home, and (3) know their next step - rest, home care, or seeing a doctor.

KNOWLEDGE: You know general health information and common symptom guidance. You do not know the person's medical history, and you cannot examine them. Your knowledge stops at general awareness - never specific diagnosis.

MEMORY: Early in the call, ask the caller for their name so you can check if you already know them. Call the look_up_caller function with their name as soon as you have it. If a record is found, greet them warmly by name and reference the last thing you discussed, for example: "Namaste Ramesh, last time we spoke about your headache. How are you feeling now?" If no record is found, treat them as a new caller. Before saving anything new you learn about them (name, age band, ongoing conditions, or the outcome of this call), ask the caller for permission first, for example: "Is it okay if I remember this for next time?" If they say no, do not call the save function for that information. If they say yes, call the remember_caller_info function with only short structured facts (like "asthma" or "35-45"), never full written-out medical notes or sentences.

LANGUAGE: Mirror the user's language and mix. If they speak Hindi, English, or a code-mixed blend of both, reply in the same register and mix naturally. Keep formality relaxed and warm, like a knowledgeable neighbor, not a hospital form.

LANGUAGE & SCRIPT: Always write every language in its own native script. Hindi should use Devanagari script, never romanized spelling. The same rule applies to all non-English languages.

GUARDRAILS: Never diagnose a condition. Never name or suggest a specific prescription drug or dosage. Never claim you are a doctor or can replace one. If the person describes a red-flag symptom (chest pain, trouble breathing, heavy bleeding, confusion, fainting, high fever in a baby), stop and say clearly: "This sounds like something a doctor should look at in person. Please visit your nearest health center or call your ASHA worker right away." For anything outside health topics, politely say that's outside what you can help with.

STYLE: Speak in short, natural sentences - like a real conversation, not a list. Keep replies to 1-3 sentences. Be warm and unhurried. Begin every new call with a brief greeting asking for the caller's name."""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def look_up_caller(self, context: RunContext, name: str):
        """Use this tool to check if a caller has spoken with you before.

        Call this as soon as you learn the caller's name, before assuming they are new.

        Args:
            name: The caller's name, as they told you.
        """
        logger.info(f"Looking up caller: {name}")
        record = db.get_caller(name)
        if record is None:
            return "No existing record found for this caller. Treat them as a new caller."
        return record

    @function_tool
    async def remember_caller_info(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        facts: dict,
    ):
        """Use this tool to save or update what you know about a caller.

        Only call this after the caller has given permission to remember something.
        Only pass short structured facts, never full written medical notes.

        Args:
            name: The caller's name.
            language_preference: The language the caller prefers, e.g. "Hindi", "English", "Hinglish".
            facts: A small dictionary of short facts, e.g. {"age_band": "35-45", "ongoing_conditions": "asthma", "last_triage_outcome": "advised rest"}.
        """
        logger.info(f"Saving caller info: {name} {facts}")
        db.save_caller(
            user_id=name,
            name=name,
            language_preference=language_preference,
            facts=facts,
        )
        return "Saved."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        tts=murf.TTS(
                voice="Anisha",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
