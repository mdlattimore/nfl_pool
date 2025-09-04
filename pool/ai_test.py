from openai import OpenAI
import os
from pool.ai_generated_email import (get_all_weeks_summary,
                                serialize_weeks_summary,
                                build_full_results_package,
                                trim_full_results, trim_full_results_for_llm)
from django.contrib.auth import get_user_model

User = get_user_model()

key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=key)


raw_summaries = get_all_weeks_summary()
serialized = serialize_weeks_summary(raw_summaries)
# pprint(serialized)
full_results_package = build_full_results_package(serialized)
# print(full_results_package)
trimmed_full_results_package = trim_full_results_for_llm(full_results_package)




prompt = f"""
You are the 'commissioner' of an NFL pool made up of family and friends (players).
Every week, the players pick the winner of every NFL game for that week, 
earning points for correct picks. Each week, those results are summarized and 
recorded in json format ("Results"). Write an email summarizing the results 
of the most recent week using that week's results, past week's results, and overall 
standings, highlighting good performances and noting trends (using past 
results for comparison). Don't improvise. Text should flow like a 
narrative, not bullet points. All statements must be supportable by 
"Results". You do not need to mention every player, 
just the top few. Do not invent: e.g. don't describe a team as an "underdog", 
don't speculate as to whether games were close or came down to the last 
minute, or anything else of the sort. You do not have access to adequate 
information. Just use first names (not first name, last initial). Response 
should be formatted in Markdown.

Tone:
Light, witty

Length:
Maximum three short paragraphs

Results:
{trimmed_full_results_package}


"""


response = client.responses.create(
    model="gpt-4o-mini",
    input = prompt,
    temperature=.5
)

print(response.output_text)