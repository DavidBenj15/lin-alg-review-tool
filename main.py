""" Module to search through textbook. """
import os
import re
import time
import fitz
from PIL import Image
import PyPDF2
import random
from colorama import Fore, Back, Style
import pdfplumber

class Unit:
    """ Class representing a unit in the textbook. """

    def __init__(self, unit_num, page, questions) -> None:
        self.unit_num = unit_num
        self.page = page
        self.questions = questions

    def randomQuestion(self):
        i = random.randint(0, len(self.questions) - 1)
        return self.questions[i]


def main():
    """ Main function. Calls helper functions. """
    file_name = load_textbook()
    reader = PyPDF2.PdfReader(file_name)
    questions_dict = load_questions("questions.txt") #Dictionary (key: unit number (str);
    #value: array of questions (int[]))
    units = scan_for_units(reader, questions_dict)
    generate_images(file_name, units, reader)  

def load_textbook():
    """Prompts user to select textbook. Returns file name."""
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
    return questions_dict


def extract_image(file, page_num, bbox, image_path):
    """Outputs an image of the randomly generated problem"""
    pdf = fitz.open(file)
    page = pdf[page_num]
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1, 1).prescale(2, 2), clip=bbox)
    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    image.save(image_path)


def generate_images(file_name, units, reader):
    """While user wants to keep generating problems:
        function will loop search through the pages to find the page/coordinates of the
        given question, then call extract_image() will the required parameters.
    """
    #TODO: put this into a loop.
    PAGE_RANGE = 15 #Maximum number of pages the function will search for a problem
    randindex = random.randint(0, len(units) - 1)
    unit = units[randindex]
    first_page = unit.page
    last_page = first_page + PAGE_RANGE
    question = unit.randomQuestion()
    print(unit.unit_num, first_page, question)
    page_index = None #Page number - 1

    #Gets exact page number of problem
    for i in range(first_page - 1, last_page - 1):
        page = reader.pages[i]
        text = page.extract_text()
        search_keyword = f'{question}.'
        res_search = re.search(search_keyword, text)
        if res_search is not None:
            page_index = i
            print("Question", question, "found on page", page_index + 1)
            break
        elif i is last_page - 1:
            print("ERROR: question", question, "not found.")

    left, top = None, None

    if page_index is not None:
        with pdfplumber.open(file_name) as pdf:
            page = pdf.pages[page_index]
            text_elements = page.extract_text

            for element in page.extract_words():
                if element['text'] == f'{question}.':
                    left = element['x0']
                    top = element['top']

    BUFFER_TOP = 20
    BUFFER_BOTTOM = 500
    BUFFER_LEFT = 10
    BUFFER_RIGHT = 250
    extract_image(file_name, page_index, (left - BUFFER_LEFT, top - BUFFER_TOP, left + BUFFER_RIGHT, top + BUFFER_BOTTOM), "generated question.png")

main()
