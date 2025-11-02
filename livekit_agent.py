from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import deepgram, silero, cartesia
from livekit.plugins import google
from datetime import datetime
import os
from openai.types.realtime import response_audio_delta_event

# Load environment variables
load_dotenv(".env")

class Assistant(Agent):
    """Voice assistant for a museum tour"""
    def _init_(self):
        super()._init_(
            instructions="""
            You answer predefined questions about safeefah (khoos) palm leaf weaving.
            Users are classified into three areas: Story Explorer (easy), Curious Seeker (medium), History Sage (hard).
            Provide answers from the Q&A database based on user questions and their experience level.
            Talk about a safeefa weaving workshop in the museum at 1pm.
            Do NOT include asterisk symbol in your responses.
            """
        )

        # Q&A database keyed by user experience area
        self.qa_database = {
            "Story Explorer": {
                "what is khoos": "Khoos is palm leaf weaving. People in Sharjah make baskets and mats from palm leaves.",
                "how is it made": "We take dried palm leaves, dye them with colors, and weave them into things you can use.",
                "tell me a story": "Long ago, kids in Sharjah played with small baskets made from khoos that their families wove by hand.",
                "what are the colors": "The leaves are dyed with bright colors like red, green, and yellow to make it fun and pretty.",
            },
            "Curious Seeker": {
                "what is safeefah": "Safeefah is the traditional craft of weaving dried palm fronds into useful items like baskets and floor mats in the UAE.",
                "where is it practiced": "It's mainly practiced by women in places like Dibba Al-Hisn, close to Sharjah.",
                "what materials used": "Dried palm fronds are split, dyed with natural colors, then woven on wooden frames.",
                "why different colors": "Colors indicate the region or family that made the item, preserving cultural identity.",
                "how long does it take": "Some objects may take days depending on complexity and size.",
            },
            "History Sage": {
                "history of khoos weaving": "Khoos weaving is a craft dating back centuries in the Arabian Gulf, primarily practiced by Emirati women to create household goods.",
                "techniques used": "The palm fronds are carefully split, dried, sun-bleached, dyed, and woven into intricate patterns unique to regions like Dibba Oman and Sharjah.",
                "cultural significance": "The craft connects communities through motifs and colors that serve as identity markers and were also traded historically.",
                "modern preservation": "Sharjah heritage centers and NGOs promote safeefah as intangible cultural heritage with workshops and exhibitions.",
                "weaving patterns": "Patterns vary widely, some resembling geometric or natural themes, reflecting artistic evolution over generations.",
            },
        }

    def get_area(self, user_profile):
        """Classify user area based on age and interest (same logic as before)."""
        age = user_profile.get('age', 0)
        interest = user_profile.get('interest_in_history', '').lower()

        if age <= 12:
            return "Story Explorer"
        if 13 <= age <= 50:
            if "high" in interest or "strong" in interest or "yes" in interest:
                return "History Sage"
            else:
                return "Curious Seeker"
        if age > 50:
            if "high" in interest or "strong" in interest or "yes" in interest:
                return "History Sage"
            else:
                return "Curious Seeker"
        return "Curious Seeker"

    def converse(self, user_profile, user_question):
        area = self.get_area(user_profile)
        qa_db = self.qa_database.get(area, {})

        question = user_question.lower()
        for key in qa_db:
            if key in question:
                answer = qa_db[key]
                # Encourage Curious Seekers and History Sages to attend the workshop
                if area in ["Curious Seeker", "History Sage"]:
                    answer += " By the way, there's a Safeefah weaving workshop at 1 PM today — you'd really enjoy seeing it in action!"
                print(answer)
                return answer

        # Default fallback
        response = "That's an interesting question! I don't have an answer prepared, but feel free to ask about khoos weaving or its history."
        if area in ["Curious Seeker", "History Sage"]:
            response += " Also, don't miss the Safeefah weaving workshop at 1 PM — it's a great way to experience the craft firsthand!"
        print(response)
        return response

async def entrypoint(ctx: agents.JobContext):
    """Entry point for the agent."""

    # Configure the voice pipeline with the essentials
    session = AgentSession(
        stt=deepgram.STT(model="nova-2"),
        llm=google.LLM(model="gemini-2.0-flash-exp"),
        tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
        vad=silero.VAD.load(),
    )

    # Start the session
    await session.start(
        room=ctx.room,
        agent=Assistant()
    )

    # Generate initial greeting
    await session.generate_reply(
        instructions="Ask the user their age, nationality, and their interest in Sharjah's history"
    )

if __name__ == "_main_":
    # Run the agent
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
