import sys
sys.path.append(r"C:\Users\thefa\AppData\Roaming\Python\Python313\site-packages")
from gedcom.parser import Parser
import pandas as pd
import re
import os

import gedcom
from datetime import datetime

parser = gedcom.parser.Parser()

# File paths
gedcom_file = "py/Falkman-2020-663-208-10811-12-226.ged"
output_file = "parsed_genealogy.xlsx"
bio_directory = "bio"

# Ensure the bio directory exists
os.makedirs(bio_directory, exist_ok=True)

# Initialize GEDCOM parser
gedcom_parser = Parser()
gedcom_parser.parse_file(gedcom_file)

def clean_name(member):
    given, mi, surname, suffix= "", "", "", ""
    if member.get_tag() == "INDI":	# if member == individual
        element = member
    else:	# else if member == [PARENTS, SPPOUSE, CHILDREN, SIBLINGS]
        id = member.get_value()
        element = gedcom_parser.get_element_dictionary().get(id)
    if element:
        given = element.get_name()[0] if element.get_name() else ""
        
        # Remove nickname enclosed in double quotes
        if(given):
            given = re.sub(r'\s*\".*?\"\s*', '', given).strip()

            # Extract middle initial (last field of given_name if multiple fields exist)
            given_name_parts = given.split()
            given = given_name_parts[0]
            if member.get_pointer() == "@I113@":
                given = "William"
            mi = given_name_parts.pop() if len(given_name_parts) > 1 else ""

            # Remove trailing period if it exists
            mi = mi.rstrip(".")

        surname = element.get_name()[1] if len(element.get_name()) > 1 else ""
        suffix = ""
        for sub_element in element.get_child_elements():
            if sub_element.get_tag() == "NAME":
                name_parts = sub_element.get_value().split("/")
                if len(name_parts) > 1:
                    suffix = name_parts[-1].strip()
        given = re.sub(r'\s*\".*?\"\s*', '', given).strip()
        given = given.rstrip(".") # Remove trailing period
        full_name = f"{given} {surname} {suffix}".strip()
    return given, mi, surname, suffix # return given name, mi, surname and suffix

def strip_id(identifier):
    return identifier[2:-1]  # Removes first 2 characters and last character


def parse_gedcom_date(date_str):
    """Convert various GEDCOM date formats into a datetime object or approximate year."""
    if not date_str.strip():  # Handle empty date
        return None
    
    try:
        return datetime.strptime(date_str, "%d %b %Y")  # Standard format (16 AUG 1944)
    except ValueError:
        pass
    
    # Handle approximate year format ("ABT YYYY")
    match = re.match(r"^ABT (\d{4})$", date_str)
    if match:
        year = match.group(1)
        return datetime(int(year), 1, 1)  # Approximate using Jan 1

    # Handle year-only format ("1898")
    if re.match(r"^\d{4}$", date_str):
        return datetime(int(date_str), 1, 1)  # Assume Jan 1 for estimation
    
    # Handle month & year format ("FEB 1909")
    match = re.match(r"^([A-Z]{3}) (\d{4})$", date_str)
    if match:
        month, year = match.groups()
        try:
            month_num = datetime.strptime(month, "%b").month
            return datetime(int(year), month_num, 1)  # Assume 1st of month
        except ValueError:
            return None  # Invalid month format

    return None  # Unrecognized format

def compute_age(birth_date_str, death_date_str):
    """Compute approximate age based on birth and death dates."""
    birth_date = parse_gedcom_date(birth_date_str)
    death_date = parse_gedcom_date(death_date_str) or datetime.today()  # Assume still alive if no death date

    if not birth_date:
        return "Unknown"  # Birth date missing

    return death_date.year - birth_date.year - ((death_date.month, death_date.day) < (birth_date.month, birth_date.day))

# Prepare data storage
data = []
identifier = ""
# Extract individuals and their details
for element in gedcom_parser.get_root_child_elements():
    if element.get_tag() == "INDI":  # Only process individuals
        info_id = strip_id(element.get_pointer()) # Extract ID without '@' characters

        indi_given_name, indi_mi, indi_surname, indi_suffix  = clean_name(element)

        # Construct full name
        name = " ".join(filter(None, [indi_given_name.strip(), indi_mi.strip(), indi_surname.strip(), indi_suffix.strip()]))

        sex = element.get_gender()
        individual_id = element.get_pointer()


        # Birth details
        birth_date, birth_place, _ = element.get_birth_data()

        # Death details
        death_date, death_place, _ = element.get_death_data()
        born_died = birth_date + " - " + death_date 
        age = compute_age(birth_date, death_date)
        if individual_id == "@I16@":  # individual with ID @I16@
            age = compute_age(birth_date, death_date)

        biography = []
        for note_element in element.get_child_elements():
            if note_element.get_tag() == "NOTE":
                current_note = note_element.get_value()

                # Capture all nested CONT elements inside this NOTE block
                for sub_element in note_element.get_child_elements():
                    if sub_element.get_tag() == "CONT":
                        current_note += "\n" + sub_element.get_value()

                biography.append(current_note.strip())  # Store full note block

        # Write biography to a text file
        if biography:
            bio_text = "\n".join(biography).strip()
        else:
            bio_text = f"The biography for {name} is not yet available."

        bio_filename = os.path.join(bio_directory, f"{name}.txt")
        with open(bio_filename, "w", encoding="utf-8") as bio_file:
            bio_file.write(bio_text)
        bio_filename = bio_filename.replace("bio\\", "")


        father_name = ""
        mother_name = ""
        sibling_names = []
        family_id = next((fam.get_value() for fam in element.get_child_elements() if fam.get_tag() == "FAMC"), None)
        if family_id:
            family_element = gedcom_parser.get_element_dictionary().get(family_id)
            if family_element:
                for member in family_element.get_child_elements():
                    # Extract father and mother details using `FAMC`
                    if member.get_tag() == "HUSB":
                        given_name, mi, surname, suffix  = clean_name(member)
                        father_name = " ".join(filter(None, [given_name.strip(), mi.strip(), surname.strip(), suffix.strip()]))
                    elif member.get_tag() == "WIFE":
                        given_name, mi, surname, suffix  = clean_name(member)
                        mother_name = " ".join(filter(None, [given_name.strip(), mi.strip(), surname.strip(), suffix.strip()]))
                    # Extract sibling details using `FAMC`
                    if member.get_tag() == "CHIL" and member.get_value() != individual_id:  # Exclude self
                        given_name, mi, surname, suffix = clean_name(member)
                        sibling_name = " ".join(filter(None, [given_name.strip(), mi.strip(), surname.strip(), suffix.strip()]))
                        sibling_names.append(sibling_name)

        spouse_name = ""
        children_names = []
        family_ids = [fam.get_value() for fam in element.get_child_elements() if fam.get_tag() == "FAMS"]
        for family_id in family_ids:
            family_element = gedcom_parser.get_element_dictionary().get(family_id)
            if family_element:
                for member in family_element.get_child_elements():
                    # Extract spouse details using family IDs (`FAMS`)
                    if member.get_tag() in ["HUSB", "WIFE"] and member.get_value() != individual_id:  # Exclude self
                        given_name, mi, surname, suffix  = clean_name(member)
                        spouse_name = " ".join(filter(None, [given_name.strip(), mi.strip(), surname.strip(), suffix.strip()]))
                    # Extract children details using family IDs (`FAMS`)
                    if member.get_tag() == "CHIL":
                        given_name, mi, surname, suffix  = clean_name(member)
                        child_name = " ".join(filter(None, [given_name.strip(), mi.strip(), surname.strip(), suffix.strip()]))
                        children_names.append(child_name)

        sibling_names = sibling_names[:6] + [""] * (6 - len(sibling_names))
        children_names = children_names[:6] + [""] * (6 - len(children_names))

        # Store extracted information
        data.append([indi_given_name, indi_mi, indi_surname, indi_suffix, name, sex, birth_date, birth_place, death_date, death_place, born_died, age, father_name, mother_name, spouse_name] + children_names + sibling_names + [bio_filename, info_id])

# Create DataFrame and save to Excel
columns = ["GIVEN NAME", "MI", "SURNAME", "SUFFIX", "NAME", "SEX", "BIRTH DATE", "BIRTH PLACE", "DEATH DATE", "DEATH PLACE", "born_died", "AGE", "FATHER", "MOTHER", "SPOUSE", "CHILD1", "CHILD2", "CHILD3", "CHILD4", "CHILD5", "CHILD6", "SIB1", "SIB2", "SIB3", "SIB4", "SIB5", "SIB6", "BIO", "info_id"]
df = pd.DataFrame(data, columns=columns)
df.to_excel(output_file, index=False)

print(f"Genealogy data successfully saved to {output_file}")