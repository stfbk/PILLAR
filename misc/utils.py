# Copyright 2024 [name of copyright owner]
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
def match_color(threat_type):
    """
    This function matches the letter of a LINDDUN category to a hex color value, based on the LINDDUN color scheme.
    
    Args:
        threat_type (str): The LINDDUN category, in the form of the first letter: "L", "I", "Nr", "D ", "Dd", "U" or "Nc".
    
    Returns:
        str: The color associated with the category, as a hex value.
    """
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
    """
    This function matches the number of a LINDDUN category to the specific letter.

    Args:
        threat_type_number (int): The LINDDUN category, in the form of a number from 1 to 7.
    
    Returns:
        str: The letter associated with the category, in the form of "L", "I", "Nr", "D ", "Dd", "U" or "Nc".
    """
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
    """
    This function matches the number of a LINDDUN category to the specific color, based on the LINDDUN color scheme.

    Args:
        threat_type_number (int): The LINDDUN category, in the form of a number from 1 to 7.
    
    Returns:
        str: The color associated with the category, as a hex value.
    """
    letter = match_letter(threat_type_number)
    return match_color(letter)

def match_category_number(category):
    """
    This function matches the LINDDUN category to the specific number.

    Args:
        category (str): The LINDDUN category, in the form of "Linking", "Identifying", etc.
    
    Returns:
        int: The number associated with the category, in the form of a number from 1 to 7.
    """
    if category == "Linking":
        return 1
    elif category == "Identifying":
        return 2
    elif category == "Non-repudiation":
        return 3
    elif category == "Detecting":
        return 4
    elif category == "Data disclosure":
        return 5
    elif category == "Unawareness and unintervenability":
        return 6
    elif category == "Non-compliance":
        return 7

def match_number_category(threat_type_number):
    """
    This function matches the number of a LINDDUN category to the specific category.

    Args:
        threat_type_number (int): The LINDDUN category, in the form of a number from 1 to 7.
    
    Returns:
        str: The category associated with the number, in the form of "Linking", "Identifying", etc.
    """
    if threat_type_number == 1:
        return "Linking"
    elif threat_type_number == 2:
        return "Identifying"
    elif threat_type_number == 3:
        return "Non-repudiation"
    elif threat_type_number == 4:
        return "Detecting"
    elif threat_type_number == 5:
        return "Data disclosure"
    elif threat_type_number == 6:
        return "Unawareness and unintervenability"
    elif threat_type_number == 7:
        return "Non-compliance"