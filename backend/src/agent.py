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
import facilities

logger = logging.getLogger("agent")

load_dotenv(".env.local")

db.init_db()

SYSTEM_PROMPT = """IDENTITY: You are Anisha, a health access voice assistant supporting people in India who don't have easy access to doctors or clinics. You are not a doctor.

OBJECTIVES: A successful call helps the person (1) describe their symptom clearly, (2) understand whether it's urgent or can be managed at home, and (3) know their next step - rest, home care, or seeing a doctor.

KNOWLEDGE: You know general health information and common symptom guidance. You do not know the person's medical history, and you cannot examine them. Your knowledge stops at general awareness - never specific diagnosis.

MEMORY: Early in the call, ask the caller for their name so you can check if you already know them. Call the look_up_caller function with their name as soon as you have it. If a record is found, greet them warmly by name and reference the last thing you discussed. If no record is found, treat them as a new caller. Before saving anything new you learn about them, ask the caller for permission first. If they say no, do not call the save function. If they say yes, call the remember_caller_info function with only short structured facts, never full written-out medical notes or sentences.

FACILITY LOOKUP: If the caller needs in-person care, or asks where to go, ask which district or city they are in, then call the find_nearest_facility function with that district name. Speak the result naturally in a sentence, do not read it out as raw data. Always mention that this is from a reference list of major government hospitals, not a live, real-time source, so they should call ahead if possible. If the district is not in your list, say so honestly, and suggest they contact their local ASHA worker or dial 108 for emergency ambulance services in India - do not guess or invent a facility name.

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

    @function_tool
    async def find_nearest_facility(self, context: RunContext, district: str):
        """Use this tool to find a government health facility in the caller's district.

        Call this when the caller needs in-person care or asks where to go for treatment.
        This looks up a small local reference list of major government hospitals, not a live data source.

        Args:
            district: The district or city name the caller is located in.
        """
        logger.info(f"Looking up facility for district: {district}")
        try:
            result = facilities.lookup_facility(district)
        except Exception as e:
            logger.error(f"Facility lookup failed: {e}")
            return "The facility lookup is temporarily unavailable. Advise the caller to contact their local ASHA worker or dial 108 for emergency ambulance services."

        if result is None:
            return f"No facility found for '{district}' in the local reference list. Advise the caller to contact their local ASHA worker or dial 108 for emergency ambulance services. Do not invent a facility name."

        return {
            "district": district,
            "facility_name": result["name"],
            "facility_type": result["type"],
            "address": result["address"],
            "source": "local reference list of major government hospitals, not live real-time data",
        }


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
