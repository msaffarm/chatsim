import os
from pathlib import Path
from .common import Annotation, Goal, UserGoal, DiagAct, read_user_profile, get_random_number

CURRENT_DIR = Path(os.path.dirname(__file__))
DATA_DIR = CURRENT_DIR / '../../data'
