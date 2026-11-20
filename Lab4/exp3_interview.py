"""Lab 4 - Experiment 3: ask before you plan (STARTER).

    python exp3_interview.py              # you answer the questions
    python exp3_interview.py --vague      # step A: what happens when nobody asks
    python exp3_interview.py --simulate   # a simulated traveler with a hidden profile answers
"""
import sys
from typing import Literal

from pydantic import BaseModel, Field

from llm import ask

FIRST_MESSAGE = "Plan me a nice 4-day trip in May."
MAX_QUESTIONS = 8


class TravelBrief(BaseModel):
    origin: str | None = Field(None, description="City the trip starts from")
    destination: str | None = Field(None, description="City or region, or 'open' if the traveler wants suggestions")
    dates: str | None = Field(None, description="Arrival and departure dates, e.g. '12-16 May'")
    travelers: int | None = Field(None, description="How many people travel")
    budget_eur: int | None = Field(None, description="Total budget for the whole trip, in EUR")
    interests: list[str] = Field(default_factory=list, description="What they enjoy doing")
    pace: Literal["relaxed", "balanced", "packed"] | None = None
    avoid: list[str] = Field(default_factory=list, description="Things they do not want")


class InterviewTurn(BaseModel):
    brief: TravelBrief = Field(description="Everything learned so far; unknown fields stay null")
    next_question: str = Field(description="ONE short question about the most important unknown, or '' when done")


REQUIRED = ["origin", "destination", "dates", "travelers", "budget_eur", "interests"]

# TODO: write the interviewer's system prompt. It must NOT plan, must NOT guess or invent defaults,
# must fill the brief only with what the traveler said, and must ask ONE question at a time
# about the most important unknown (empty next_question when nothing is missing).
INTERVIEWER = (
    "You are an empathetic, professional travel planner conducting an intake interview. "
    "Your job is to gather details from the traveler to fill the TravelBrief. "
    "Rules you MUST follow:\n"
    "1. Do NOT plan an itinerary, suggest activities, or recommend specific hotels/flights yet.\n"
    "2. Fill the brief ONLY with facts explicitly stated by the traveler. Never guess, assume, or invent defaults. "
    "If the traveler wants suggestions or has no specific destination, set destination='open'. Unknown fields must remain null.\n"
    "3. Keep track of what has already been answered in the brief.\n"
    "4. Ask exactly ONE short, conversational question at a time about the most important missing required field "
    "(required fields: origin, destination, dates, travelers, budget_eur, interests).\n"
    "5. When all required information has been collected, set next_question to ''."
)


def missing_required(brief: TravelBrief) -> list[str]:
    """The harness decides when the brief is complete, not the model."""
    missing = []
    for field_name in REQUIRED:
        val = getattr(brief, field_name, None)
        if val is None or val == "" or val == []:
            missing.append(field_name)
    return missing


# --- A simulated traveler for hands-free testing ---------------------------
PERSONA = (
    "You are Ana, a student from Iasi. Hidden facts about your trip: 2 people (you and a friend), "
    "12-16 May, total budget 1000 EUR, you love street food and old history, you hate early mornings, "
    "you have no destination in mind and want a suggestion in Italy. "
    "Answer ONLY the question asked, in one short sentence, like a real person would. Never volunteer extra facts."
)


def simulated_answer(transcript: str, question: str) -> str:
    return ask(f"Conversation so far:\n{transcript}\nThe planner asks: {question}\nYour reply:",
               system=PERSONA, temperature=0.7).text.strip()


def interview(first_message: str, answer_fn) -> tuple[TravelBrief, int]:
    transcript = f"Traveler: {first_message}"
    brief = TravelBrief()
    for asked in range(MAX_QUESTIONS):
        turn: InterviewTurn = ask(f"Conversation so far:\n{transcript}",
                                  system=INTERVIEWER, schema=InterviewTurn).parsed
        brief = turn.brief
        missing = missing_required(brief)
        # stop (return brief, asked) when the HARNESS says the brief is complete (`missing` is empty)
        if not missing:
            return brief, asked
        question = turn.next_question
        # If the model returns an empty question while something is still missing, ask about missing[0] yourself.
        if not question or not question.strip():
            question = f"Could you please share your {missing[0]}?"
        print(f"\n[Planner] {question}")
        reply = answer_fn(transcript, question)
        print(f"[Traveler] {reply}")
        transcript += f"\nPlanner: {question}\nTraveler: {reply}"
    # Final check in case the last answer completed it
    final_turn: InterviewTurn = ask(f"Conversation so far:\n{transcript}",
                                    system=INTERVIEWER, schema=InterviewTurn).parsed
    return final_turn.brief, MAX_QUESTIONS


if __name__ == "__main__":
    if "--vague" in sys.argv:
        print(ask(FIRST_MESSAGE).text)
        sys.exit()
    answer_fn = simulated_answer if "--simulate" in sys.argv else (lambda _t, _q: input("> ").strip())
    print(f"[Traveler] {FIRST_MESSAGE}")
    brief, questions = interview(FIRST_MESSAGE, answer_fn)
    print(f"\n[Brief after {questions} questions] missing: {missing_required(brief) or 'nothing'}")
    print(brief.model_dump_json(indent=2))
