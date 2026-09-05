import json

from app.integrations.llm.base import LLMProvider

GROUNDED_SYSTEM = (
    "You are WeatherGPT. Answer only using the provided weather data. "
    "Never invent weather values. If required data is unavailable, clearly say so."
)


class DemoLLMProvider(LLMProvider):
    """Template-based grounded answers when no LLM key is present."""

    name = "demo_llm"

    async def complete(self, system: str, user: str) -> str:
        data = {}
        if "DATA_JSON:" in user:
            raw = user.split("DATA_JSON:", 1)[1].split("USER_QUESTION:", 1)[0].strip()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {}
        question = user
        if "USER_QUESTION:" in user:
            question = user.split("USER_QUESTION:", 1)[1].strip()
        loc = data.get("location_name") or data.get("location") or "the selected location"
        facts = data.get("facts") or data
        lang = data.get("language") or "en"

        def n(key, suffix=""):
            v = facts.get(key)
            if v is None and isinstance(facts.get("current"), dict):
                v = facts["current"].get(key)
            if v is None and isinstance(facts.get("tomorrow"), dict):
                v = facts["tomorrow"].get(key)
            return f"{v}{suffix}" if v is not None else "unavailable"

        intent = data.get("intent") or ""
        if "rain" in intent or "rain" in question.lower() or "వర్షం" in question or "बारिश" in question:
            p = n("rain_probability", "%")
            t = n("temperature", "°C")
            r = n("rainfall", " mm")
            if lang == "te":
                text = f"{loc}లో వర్షపు సంభావ్యత {p}, ఉష్ణోగ్రత సుమారు {t}, వర్షపాతం {r}. బయటకు వెళ్తే గొడుగు తీసుకెళ్లండి."
            elif lang == "hi":
                text = f"{loc} में वर्षा की संभावना {p} है, तापमान लगभग {t} और वर्षा {r}। बाहर जाते समय छाता रखें।"
            else:
                text = (
                    f"In {loc}, rain probability is {p} with temperatures around {t} "
                    f"and rainfall {r}. Carry an umbrella if you go outside."
                )
        else:
            t = n("temperature", "°C")
            h = n("humidity", "%")
            w = n("wind_speed", " km/h")
            if lang == "te":
                text = f"{loc}లో ప్రస్తుత ఉష్ణోగ్రత {t}, తేమ {h}, గాలి వేగం {w}."
            elif lang == "hi":
                text = f"{loc} में वर्तमान तापमान {t}, आर्द्रता {h}, हवा की गति {w} है।"
            else:
                text = f"In {loc}, temperature is {t}, humidity {h}, wind speed {w}."

        if data.get("advisory_disclaimer"):
            text += " " + data["advisory_disclaimer"]
        if data.get("is_demo"):
            prefix = {"te": "[డెమో డేటా] ", "hi": "[डेमो डेटा] ", "en": "[DEMO DATA] "}
            text = prefix.get(lang, "[DEMO DATA] ") + text
        text += " Facts above come only from retrieved weather data."
        return text
