""" Module to search through textbook. """
import os
import re
import time
import PyPDF2
from colorama import Fore, Back, Style

class Unit:
    """ Class representing a unit in the textbook. """

    def __init__(self, unit_num, page, questions) -> None:
        self.unit_num = unit_num
        self.page = page
        self.questions = questions


def main():
    """ Main function. Calls helper functions. """
    reader = load_textbook()
    questions_dict = load_questions("questions.txt") #Dictionary (key: unit number (str);
    #value: array of questions (int[]))
    units = scan_for_units(reader, questions_dict)


def load_textbook():
    """Prompts user to select textbook. Returns reader."""
    file_array = os.listdir()
    while True:
        for index, file in enumerate(file_array):
            if file.endswith(".pdf"):
                print(f'[{index}]: {file}')
        try:
            file_index = int(input(Fore.LIGHTYELLOW_EX + "Enter file index: " + Style.RESET_ALL))
            break
        except ValueError:
            print(Back.RED + "Please enter valid integer (Ex: 0). " + Style.RESET_ALL)
            time.sleep(1)

    file_name = file_array[file_index]
    return PyPDF2.PdfReader(file_name)
    # open selected pdf


def scan_for_units(reader, questions_dict):
    """ Searches pdf for keyword.
        For each keyword, creates a Unit class containing first page of unit & unit number.
    """
    units = []
    search_keyword = r"EXERCISES \d+\.\d+" # Excercises + any number with decimal

    # search for string in pages
    for index, page in enumerate(reader.pages):
        text = page.extract_text()
        res_search = re.search(search_keyword, text)
        if res_search is not None:
            page_num = index + 1
            unit_num = res_search.group()[10:]
            try:
                unit_num = str(unit_num)
            except ValueError:
                print("VALUE ERROR: converting unit num to str for Unit", unit_num)
            questions = questions_dict.get(unit_num, None) #If no questions for unit, questions=None
            if questions is None:
                break
            unit = Unit(unit_num, page_num, questions)
            print(unit.unit_num, unit.page, unit.questions)
            units.append(unit)
    print("Scan complete.")
    return units


def load_questions(questions):
    """ Prompts user to select CSV file containing the questions for each unit.
        Parses the questions.
        Returns a dictionary (key: unit number (as string); value: array of unit numbers)
    """
    questions_dict = {}
    with open(questions, encoding="utf-8") as f:
        for row in f.readlines():
            row = row.replace('\n', '')
            vals = row.split(", ")
            unit_num = vals[0] #Type: string
            questions_dict[str(unit_num)] = list(map(int, vals[1:])) #Assigns dictionary values 
            #to list of integers
            # print("UNIT NUM:", unit_num)
            # print("Qs:", questions_dict[unit_num])        
    return questions_dict

main()
