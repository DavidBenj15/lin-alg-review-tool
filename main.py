""" Module to search through textbook. """
import os
import re
import time
import PyPDF2
import pandas as pd
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
    # all_questions = load_questions()
    units = scan_for_units(reader)

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


def scan_for_units(reader):
    """ Searches pdf for keyword.
        For each keyword, creates a Unit class containing first page of unit & unit number.
    """
    # TODO: Pass in "all_questions" as a parameter once "load_questions()" functionality
    # is implemented.
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
                unit_num = float(unit_num)
            except ValueError:
                print("VALUE ERROR: converting unit num to float for Unit", unit_num)
            questions = ...
            print("UNIT NUMBER:", unit_num)
            print("PAGE:", page_num)
            print()
            unit = Unit(unit_num, page_num, questions)
            units.append(unit)
    print("Scan complete.")
    return units


def load_questions():
    """ Prompts user to select CSV file containing the questions for each unit.
        Parses the questions.
        Returnsa list containing lists of questions for each unit.
    """
    df = pd.read_csv


main()
