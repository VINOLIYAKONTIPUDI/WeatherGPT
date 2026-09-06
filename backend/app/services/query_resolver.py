import re
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class WeatherQueryObject:
    intent: str  # "current", "historical", "forecast", "comparison", "location_required"
    location_name: Optional[str] = None
    target_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d")) # YYYY-MM-DD
    end_date: Optional[str] = None # For date ranges like "next week"
    target_time_slot: Optional[str] = None # "morning", "afternoon", "evening", "night", or "HH:00"
    target_hour: Optional[int] = None # 0-23
    metric: str = "weather_summary" # "temperature", "precipitation", "humidity", "wind", "uv_index", "weather_summary", "umbrella", "travel_advisory", "outdoor_activity"
    is_comparison: bool = False
    comparison_date1: Optional[str] = None # YYYY-MM-DD
    comparison_date2: Optional[str] = None # YYYY-MM-DD
    comparison_label1: Optional[str] = None
    comparison_label2: Optional[str] = None
    raw_query: str = ""
    resolved_date_label: str = "Today"

class QueryResolver:
    DAYS_MAP = {
        "monday": 0, "mon": 0, "సోమవారం": 0, "సోమ": 0, "सोमवार": 0,
        "tuesday": 1, "tue": 1, "మంగళవారం": 1, "మంగళ": 1, "मंगलवार": 1,
        "wednesday": 2, "wed": 2, "బుధవారం": 2, "బుధ": 2, "बुधवार": 2,
        "thursday": 3, "thu": 3, "గురువారం": 3, "గురు": 3, "गुरुवार": 3,
        "friday": 4, "fri": 4, "శుక్రవారం": 4, "శుక్ర": 4, "शुक्रवार": 4,
        "saturday": 5, "sat": 5, "శనివారం": 5, "శని": 5, "शनिवार": 5,
        "sunday": 6, "sun": 6, "ఆదివారం": 6, "ఆది": 6, "रविवार": 6,
    }

    @classmethod
    def resolve_query(cls, query_text: str, reference_date: Optional[date] = None) -> WeatherQueryObject:
        if reference_date is None:
            reference_date = datetime.now().date()
        
        q = query_text.lower().strip()
        
        # 1. Detect metric
        metric = cls._detect_metric(q)

        # 2. Check for comparison
        is_comp, date1, date2, label1, label2 = cls._detect_comparison(q, reference_date)
        if is_comp:
            return WeatherQueryObject(
                intent="comparison",
                target_date=date1,
                end_date=date2,
                metric=metric,
                is_comparison=True,
                comparison_date1=date1,
                comparison_date2=date2,
                comparison_label1=label1,
                comparison_label2=label2,
                raw_query=query_text,
                resolved_date_label=f"{label1} vs {label2}"
            )

        # 3. Detect time slot / specific hour
        time_slot, target_hour = cls._detect_time_slot(q)

        # 4. Resolve date
        target_date_str, end_date_str, intent, date_label = cls._resolve_date(q, reference_date)

        return WeatherQueryObject(
            intent=intent,
            target_date=target_date_str,
            end_date=end_date_str,
            target_time_slot=time_slot,
            target_hour=target_hour,
            metric=metric,
            raw_query=query_text,
            resolved_date_label=date_label
        )

    @classmethod
    def _detect_metric(cls, q: str) -> str:
        if any(w in q for w in ["umbrella", "raincoat", "rain coat", "గొడుగు", "రెయిన్‌కోట్", "छाता"]):
            return "umbrella"
        if any(w in q for w in ["rain", "raining", "rainfall", "drizzle", "shower", "precipitation", "వర్షం", "వర్షపాతం", "बारिश", "बरसात"]):
            return "precipitation"
        if any(w in q for w in ["cold", "hot", "temperature", "degree", "temp", "warm", "cool", "heat", "ఉష్ణోగ్రత", "వేడి", "చలి", "तापमान", "गर्मी", "ठंड"]):
            return "temperature"
        if any(w in q for w in ["humidity", "humid", "moisture", "తేమ", "नमी"]):
            return "humidity"
        if any(w in q for w in ["wind", "storm", "breeze", "windy", "గాలి", "हवा"]):
            return "wind"
        if any(w in q for w in ["uv", "sun", "sunscreen", "ultraviolet", "ఎండ", "धूप"]):
            return "uv_index"
        if any(w in q for w in ["travel", "drive", "trip", "going to", "outside", "safe to", "పయనం", "ప్రయాణం", "यात्रा"]):
            return "travel_advisory"
        if any(w in q for w in ["outdoor", "walk", "jog", "picnic", "cricket", " match", "ఆరుబయట", "सैर"]):
            return "outdoor_activity"
        return "weather_summary"

    @classmethod
    def _detect_time_slot(cls, q: str) -> Tuple[Optional[str], Optional[int]]:
        # Specific hour matching (e.g. 6 PM, 10 AM, 18:00, 6 గంటలకు, 6 बजे)
        hour_match = re.search(r'\b(\d{1,2})\s*(am|pm|o\'clock)\b', q)
        if hour_match:
            hr = int(hour_match.group(1))
            ampm = hour_match.group(2).lower()
            if ampm == "pm" and hr < 12:
                hr += 12
            elif ampm == "am" and hr == 12:
                hr = 0
            return (f"{hr:02d}:00", hr)

        # 24h format (e.g. 18:00)
        match_24 = re.search(r'\b([01]?\d|2[0-3]):00\b', q)
        if match_24:
            hr = int(match_24.group(1))
            return (f"{hr:02d}:00", hr)

        if any(w in q for w in ["morning", "ఉదయం", "మొదలు", "सुबह"]):
            return ("morning", 9)
        if any(w in q for w in ["afternoon", "మధ్యాహ్నం", "दोपहर"]):
            return ("afternoon", 14)
        if any(w in q for w in ["evening", "సాయంత్రం", "शाम"]):
            return ("evening", 18)
        if any(w in q for w in ["night", "రాత్రి", "रात"]):
            return ("night", 22)

        return (None, None)

    @classmethod
    def _resolve_date(cls, q: str, ref: date) -> Tuple[str, Optional[str], str, str]:
        # 1. Day before yesterday / మొన్న / परसों
        if any(w in q for w in ["day before yesterday", "మొన్న", "परसों"]):
            d = ref - timedelta(days=2)
            return (d.strftime("%Y-%m-%d"), None, "historical", "Day Before Yesterday")

        # 2. Yesterday / నిన్న / कल (past check)
        if any(w in q for w in ["yesterday", "নিన్న", "నిన్న", "बीता हुआ कल"]):
            d = ref - timedelta(days=1)
            return (d.strftime("%Y-%m-%d"), None, "historical", "Yesterday")

        # Hindi 'कल' handling (check if past or future based on verb tense)
        if "कल" in q:
            if any(w in q for w in ["था", "थी", "थे", "हुआ"]):
                d = ref - timedelta(days=1)
                return (d.strftime("%Y-%m-%d"), None, "historical", "Yesterday")
            else:
                d = ref + timedelta(days=1)
                return (d.strftime("%Y-%m-%d"), None, "forecast", "Tomorrow")

        # 3. X days ago / X రోజుల క్రితం / X दिन पहले
        ago_match = re.search(r'(\d+)\s*(days?|రోజుల|दिन)\s*(ago|క్రితం|पहले)', q)
        if ago_match:
            days_num = int(ago_match.group(1))
            d = ref - timedelta(days=days_num)
            return (d.strftime("%Y-%m-%d"), None, "historical", f"{days_num} Days Ago")

        # 4. Day after tomorrow / ఎల్లుండి / नरसों / अतरसों
        if any(w in q for w in ["day after tomorrow", "ఎల్లుండి", "नरसों"]):
            d = ref + timedelta(days=2)
            return (d.strftime("%Y-%m-%d"), None, "forecast", "Day After Tomorrow")

        # 5. Tomorrow / రేపు / कल
        if any(w in q for w in ["tomorrow", "రేపు"]):
            d = ref + timedelta(days=1)
            return (d.strftime("%Y-%m-%d"), None, "forecast", "Tomorrow")

        # 6. In X days / X రోజుల్లో / X दिनों में
        in_match = re.search(r'(in|మరియు)\s*(\d+)\s*(days?|రోజుల|दिन)', q) or re.search(r'(\d+)\s*(రోజుల్లో|दिनों में)', q)
        if in_match:
            # extract number
            nums = re.findall(r'\d+', in_match.group(0))
            if nums:
                days_num = int(nums[0])
                d = ref + timedelta(days=days_num)
                return (d.strftime("%Y-%m-%d"), None, "forecast", f"In {days_num} Days")

        # 7. Next / Last / This + Day of Week (e.g. next Sunday, next Monday, last Sunday)
        for day_name, target_weekday in cls.DAYS_MAP.items():
            if day_name in q:
                cur_weekday = ref.weekday() # Monday=0 ... Sunday=6
                
                if "last" in q or "పోయిన" in q or "పాస్ట్" in q or "पिछले" in q:
                    # Previous occurrence
                    days_back = (cur_weekday - target_weekday) % 7
                    if days_back == 0:
                        days_back = 7
                    d = ref - timedelta(days=days_back)
                    return (d.strftime("%Y-%m-%d"), None, "historical", f"Last {day_name.capitalize()}")
                
                elif "next" in q or "వచ్చే" in q or "తరువాతి" in q or "अगले" in q:
                    # Next occurrence (always upcoming day)
                    days_ahead = (target_weekday - cur_weekday) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    d = ref + timedelta(days=days_ahead)
                    return (d.strftime("%Y-%m-%d"), None, "forecast", f"Next {day_name.capitalize()}")
                
                else:
                    # Just day name (e.g. "Sunday")
                    days_ahead = (target_weekday - cur_weekday) % 7
                    if days_ahead == 0 and ("was" in q or "ఉండింది" in q):
                        days_ahead = -7
                    d = ref + timedelta(days=days_ahead)
                    intent = "historical" if days_ahead < 0 else ("current" if days_ahead == 0 else "forecast")
                    return (d.strftime("%Y-%m-%d"), None, intent, day_name.capitalize())

        # 8. Next week / వచ్చే వారం / अगले हफ्ते
        if any(w in q for w in ["next week", "వచ్చే వారం", "अगले हफ्ते", "अगले सप्ताह"]):
            start_d = ref + timedelta(days=1)
            end_d = ref + timedelta(days=7)
            return (start_d.strftime("%Y-%m-%d"), end_d.strftime("%Y-%m-%d"), "forecast", "Next Week")

        # 9. Weekend / వారాంతం / वीकेंड
        if any(w in q for w in ["weekend", "వారాంతం", "వీకెండ్", "वीकेंड"]):
            # Find coming Saturday
            days_to_sat = (5 - ref.weekday()) % 7
            sat_d = ref + timedelta(days=days_to_sat)
            sun_d = sat_d + timedelta(days=1)
            return (sat_d.strftime("%Y-%m-%d"), sun_d.strftime("%Y-%m-%d"), "forecast", "This Weekend")

        # Default: Today
        return (ref.strftime("%Y-%m-%d"), None, "current", "Today")

    @classmethod
    def _detect_comparison(cls, q: str, ref: date) -> Tuple[bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        # Detect comparison terms: "hotter than", "colder than", "more humid than", "కంటే", "से ज्यादा", "तुलना"
        comp_keywords = ["than", "versus", "vs", "compare", "కంటే", "పోలిస్తే", "से ज्यादा", "तुलना"]
        if not any(k in q for k in comp_keywords):
            return (False, None, None, None, None)

        # Check for two relative dates
        # E.g. "yesterday" vs "today", "next Monday" vs "tomorrow"
        date1_str, date2_str = None, None
        label1, label2 = None, None

        if "yesterday" in q or "నిన్న" in q or "कल" in q:
            d1 = ref - timedelta(days=1)
            date1_str = d1.strftime("%Y-%m-%d")
            label1 = "Yesterday"
        elif "tomorrow" in q or "రేపు" in q:
            d1 = ref + timedelta(days=1)
            date1_str = d1.strftime("%Y-%m-%d")
            label1 = "Tomorrow"

        if "today" in q or "ఈరోజు" in q or "आज" in q:
            d2 = ref.strftime("%Y-%m-%d")
            label2 = "Today"
        elif "tomorrow" in q or "రేపు" in q:
            if label1 != "Tomorrow":
                d2 = (ref + timedelta(days=1)).strftime("%Y-%m-%d")
                label2 = "Tomorrow"

        if date1_str and date2_str:
            return (True, date1_str, date2_str, label1, label2)

        # Default comparison: Yesterday vs Today
        d_yest = (ref - timedelta(days=1)).strftime("%Y-%m-%d")
        d_today = ref.strftime("%Y-%m-%d")
        return (True, d_yest, d_today, "Yesterday", "Today")
