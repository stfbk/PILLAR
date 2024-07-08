def match_color(threat_type):
    if "L" in threat_type:
        return "#4570b3"
    elif "I" in threat_type:
        return "#a1bf37"
    elif "Nr" in threat_type:
        return "#4d8b3f"
    elif "D " in threat_type:
        return "#f0b81f"
    elif "Dd" in threat_type:
        return "#4a3b97"
    elif "U" in threat_type:
        return "#e07736"
    elif "Nc" in threat_type:
        return "#cc2e50"
    else:
        return "#000000"

def match_letter(threat_type_number):
    if threat_type_number == 1:
        return "L"
    elif threat_type_number == 2:
        return "I"
    elif threat_type_number == 3:
        return "Nr"
    elif threat_type_number == 4:
        return "D "
    elif threat_type_number == 5:
        return "Dd"
    elif threat_type_number == 6:
        return "U"
    elif threat_type_number == 7:
        return "Nc"

def match_number_color(threat_type_number):
    letter = match_letter(threat_type_number)
    return match_color(letter)