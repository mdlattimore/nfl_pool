# pool/context_processors.py
from .utils import get_week_info


def current_week(request):
    week_info = get_week_info()

    return {"current_week": week_info["week"]}
