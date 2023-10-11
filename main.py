""" Module to search through textbook. """
import os
import re
import time
import random
import fitz
from PIL import Image
import PyPDF2
from colorama import Fore, Back, Style
import pdfplumber

class Unit:
    """ Class representing a unit in the textbook. """

    def __init__(self, unit_num, page, questions) -> None:
        self.unit_num = unit_num
        self.page = page
        self.questions = questions

    def random_question(self):
        """Returns a random question from object's unit."""
        i = random.randint(0, len(self.questions) - 1)
        return self.questions[i]


def main():
    """ Main function. Calls helper functions. """
    pdf_file_name = load_textbook()
    reader = PyPDF2.PdfReader(pdf_file_name)
    questions_dict = load_questions() #Dictionary (key: unit number (str);
    #value: array of questions (int[]))
    units = scan_for_units(reader, questions_dict)
    prompt_for_generation(pdf_file_name, units)

def load_textbook():
    """Prompts user to select textbook. Returns file name."""
    file_array = os.listdir()
    while True:
        for index, file in enumerate(file_array):
            if file.endswith(".pdf"):
                print(f'[{index}]: {file}')
        try:
            file_index = int(input(Fore.LIGHTYELLOW_EX + "Enter PDF file index: " + Style.RESET_ALL))
            break
        except ValueError:
            print(Back.RED + "Please enter valid integer (Ex: 0). " + Style.RESET_ALL)
            time.sleep(1)

    file_name = file_array[file_index]
    return file_name


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
            units.append(unit)
    print("Scan complete.")
    return units


def load_questions():
    """ Prompts user to select TXT file containing the questions for each unit.
        Parses the questions.
        Returns a dictionary (key: unit number (as string); value: array of unit numbers)
    """
    file_array = os.listdir()
    while True:
        for index, file in enumerate(file_array):
            if file.endswith(".txt"):
                print(f'[{index}]: {file}')
        try:
            file_index = int(input(Fore.LIGHTYELLOW_EX + "Enter questions file index: " + Style.RESET_ALL))
            break
        except ValueError:
            print(Back.RED + "Please enter valid integer (Ex: 0). " + Style.RESET_ALL)
            time.sleep(1)

    file_name = file_array[file_index]

    questions_dict = {}
    with open(file_name, encoding="utf-8") as f:
        for row in f.readlines():
            row = row.replace('\n', '')
            vals = row.split(", ")
            unit_num = vals[0] #Type: string
            questions_dict[str(unit_num)] = list(map(int, vals[1:])) #Assigns dictionary values 
            #to list of integers  
    return questions_dict


def extract_image(data):
    """ Outputs an image of the randomly generated problem.
        Assumes "data" input array is in the correct order.
    """
    file, page_num, bbox, image_path = data[0], data[1], data[2], data[3]
    pdf = fitz.open(file)
    page = pdf[page_num]
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1, 1).prescale(2, 2), clip=bbox)
    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    image.save(image_path)


def prompt_for_generation(file_name, units):
    """Gets user input [y/n]. If user enters 'y', generate a problem and output an image."""
    while True:
        try:
            user_in = str(input(Fore.LIGHTYELLOW_EX + "Generate question?[y/n] " + Style.RESET_ALL))
            if user_in.lower() == "y":
                question_data = generate_question(file_name, units)
                extract_image(question_data)
            elif user_in.lower() == 'n':
                break
            else:
                raise ValueError("user_in was type str, but user_in[0] was neither 'y' or 'n'.")
        except ValueError:
            print("Please enter either 'y' or 'n'.")


def generate_question(file_name, units):
    """ Chooses a random question from a random unit.
        Returns an array containing the file name,
        page index (page # - 1), bbox encapsulating the question,
        and output path for the generated image.
    """
    PAGE_RANGE = 15 #Maximum number of pages the function will search for a problem
    randindex = random.randint(0, len(units) - 1)
    unit = units[randindex]
    first_page = unit.page
    last_page = first_page + PAGE_RANGE
    question = unit.random_question()
    print(unit.unit_num, first_page, question)

    left, top = None, None
    page_index = None

    with pdfplumber.open(file_name) as pdf:
        break_out_flag = False
        for i in range(first_page - 1, last_page - 1):
            page = pdf.pages[i]
            for element in page.extract_words():
                if element['text'] == f'{question}.':
                    left = element['x0']
                    top = element['top']
                    page_index = i
                    print("Question", question, "found on page", page_index)
                    break_out_flag = True #signals program to break out of nested loop
                    break
                elif left is None and i is last_page - 1:
                    print("ERROR: question", question, "not found.")
            if break_out_flag:
                break

    BUFFER_TOP = 20
    BUFFER_BOTTOM = 500
    BUFFER_LEFT = 10
    BUFFER_RIGHT = 250
    data = [file_name,
            page_index,
            (left - BUFFER_LEFT, top - BUFFER_TOP,
                    left + BUFFER_RIGHT, top + BUFFER_BOTTOM),
            "generated question.png"
            ]
    return data

main()
