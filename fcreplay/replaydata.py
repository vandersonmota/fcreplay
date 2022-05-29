import datetime
from dataclasses import dataclass


@dataclass
class ReplayData:
    id: str
    p1_loc: str
    p2_loc: str
    p1_rank: str
    p2_rank: str
    p1: str
    p2: str
    date_replay: datetime.datetime
    length: int # Length in seconds
    status: str
    game: str
    emulator: str

