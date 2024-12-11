from dataclasses import dataclass
from typing import List


@dataclass
class Option:
    value: str
    text_content: str


@dataclass
class OptionGroup:
    label: str
    options: List[Option]
