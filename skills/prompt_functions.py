from datetime import datetime

def formatted_date_today() -> str:
    """
    Retorna a data de hoje formatada em inglês.
    
    Exemplo: "Today is monday, january 28, 2026."
    """
    weekdays = ["monday", "tuesday", "wednesday", "thursday",
                "friday", "saturday", "sunday"]
    months = ["january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november", "december"]

    today = datetime.now()
    weekday = weekdays[today.weekday()]
    day = today.day
    month = months[today.month - 1]
    year = today.year

    return f"Today is {weekday}, {month} {day}, {year}."
