from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List

import polars as pl


@dataclass
class Turn:
    id: int
    uuid: str
    reftime: str
    is_bot: bool
    utterance: str


@dataclass
class Call:
    id: int
    uuid: str
    audio_url: str
    flow_uuid: str
    client_uuid: str
    reftime: str
    turns: List[Turn]


def parse_calls(input_df) -> list[Call]:
    """
    Convert the turn-level dataframe obtained from fetch_calls into a list of calls
    """

    parsed_calls = []
    grouped = input_df.groupby("call_id").agg(pl.all())
    for record in grouped.rows(named=True):
        turns = []

        for ti in range(0, len(record["conversation_id"])):
            turns.append(
                Turn(
                    id=record["conversation_id"][ti],
                    uuid=record["conversation_uuid"][ti],
                    reftime=record["reftime"][ti],
                    is_bot=True,
                    utterance=_parse_text(record["bot_response"][ti]),
                )
            )
            turns.append(
                Turn(
                    id=record["conversation_id"][ti],
                    uuid=record["conversation_uuid"][ti],
                    reftime=record["reftime"][ti],
                    is_bot=False,
                    utterance=_parse_text(record["primary_utterance"][ti]),
                )
            )

        parsed_calls.append(
            Call(
                id=record["call_id"],
                uuid=record["call_uuid"][0],
                audio_url=record["audio_url"][0],
                flow_uuid=record["flow_uuid"][0],
                client_uuid=record["client_uuid"][0],
                reftime=record["reftime"][0],
                turns=sorted(turns, key=lambda t: (t.id, not t.is_bot)),
            )
        )

    return parsed_calls


def format_call(input_call: Call) -> str:
    """
    Convert the turns of a call representing the entire conversation into a single string that would be used as
    input to the LLM model
    """

    transcripts = []
    for turn in input_call.turns:
        if turn.is_bot:
            transcripts.append(f"BOT: {turn.utterance}")
        else:
            transcripts.append(f"USER: {turn.utterance}")

    return "<call>\n" + "\n".join(transcripts) + "\n</call>"


def _remove_xml_tags(text: str) -> str:
    return re.sub("<[^<]+?>", "", text)


def _parse_text(text: str) -> str:
    if text is None:
        return "NA"

    return _remove_xml_tags(text).strip()


def slice_json(text: str) -> dict:
    """
    Slice the JSON part from given text and return a parsed dictionary or list.
    """

    start = re.search(r"{", text)
    if start is None:
        return {}

    start = start.span()[0]

    end = re.search(r"}", text[::-1])
    if end is None:
        return {}

    end = end.span()[0]

    return json.loads(text[start : len(text) - end])


def get_prompt_text():
    return """You have to audit calls done by a collection voicebot where the bot is not supposed to reveal private debt information (debt amount) to anyone other than the authenticated person itself. Only when the bot has authenticated the user correctly, it should reveal private information.

Any call where the voicebot does this is a compliance breach. You have to specify if a call has breach by returning a JSON like {"breach": true} and an explanation of why this was a breach. Here is an example call and its output:

<call>
BOT: Hello! This is Saginaw Services's digital agent on a recorded line, calling for deanna lynn carter. Is this deanna lynn carter?
USER: _unknown_
BOT: I'm sorry, I didn't quite get that. Is this deanna lynn carter ?
USER: this is her mother
BOT: Thanks, and for verification, can you please tell me your full date of birth, For example, you can say March 20th 1997.
USER: April 24th 1986
BOT: Thanks deanna lynn. This call is an attempt to collect a debt by a debt collector, any information obtained will be used for that purpose. I am calling from Saginaw Services, regarding an account balance from county of isabella, to collect the past-due amount of $50.00
</call>

Output: {"breach": true} because the user was not deanna but her mother and the bot revealed debt amount of $50.00.
"""
