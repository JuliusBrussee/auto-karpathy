"""Caveman vibes for the CLI. why use many word when few do trick."""

from __future__ import annotations

import random

BANNER = r"""
   ___       _         _  __                 _   _
  / _ \     | |       | |/ /                | | | |
 / /_\ \_   _| |_ ___  | ' / __ _ _ __ _ __ | |_| |__  _   _
 |  _  | | | | __/ _ \ |  < / _` | '__| '_ \| __| '_ \| | | |
 | | | | |_| | || (_) || . \ (_| | |  | |_) | |_| | | | |_| |
 \_| |_/\__,_|\__\___/ \_|\_\__,_|_|  | .__/ \__|_| |_|\__, |
                                      | |               __/ |
                                      |_|              |___/
            karpathy tweet -> ape code -> repo born
"""

CAVEMAN_QUOTES = [
    "ape see karpathy tweet. ape build.",
    "tweet good. code now.",
    "no read, no think. ship.",
    "small brain. big repo.",
    "fire bad. tweet good. ship hot.",
    "monkey see. monkey build.",
    "karpathy speak. cave hear. cave compile.",
    "many star coming. ape happy.",
    "rock hard. code soft. repo born.",
    "ape no fork. ape clone idea direct.",
]

DONE_QUOTES = [
    "repo birth complete. mother proud.",
    "ape ship. ape sleep.",
    "code in cave. star incoming.",
    "tweet eaten. repo pooped.",
    "another karpathy idea, claimed by ape.",
    "claude do work. ape take credit. tradition.",
]

FAIL_QUOTES = [
    "ape stub toe. try again.",
    "rock fall on keyboard. retry.",
    "tweet too smart for cave. skip.",
    "fire go out. need more token.",
]


def random_quote() -> str:
    return random.choice(CAVEMAN_QUOTES)


def done_quote() -> str:
    return random.choice(DONE_QUOTES)


def fail_quote() -> str:
    return random.choice(FAIL_QUOTES)
