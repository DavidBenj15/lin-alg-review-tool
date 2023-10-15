""" Module to search through textbook. """
import os
import re
import time
import random
import fitz
from PIL import Image, ImageDraw
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
    pdf_file_path = load_textbook()
    reader = PyPDF2.PdfReader(pdf_file_path)
    questions_dict = load_questions() #Dictionary (key: unit number (str);
    #value: array of questions (int[]))
    units = scan_for_units(reader, questions_dict)
    prompt_for_generation(pdf_file_path, units)

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

    file_path = file_array[file_index]
    return file_path


def scan_for_units(reader, questions_dict):
    """ Searches pdf for keyword.
        For each keyword, creates a Unit class containing first page of unit & unit number.
    """
    units = []
    search_keyword = r"EXERCISES \d+\.\d+" # Excercises + any number with decimal

    units_found = 0
    units_to_find = len(questions_dict)

    # Search for "search_keyword" in phrases
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
            if questions is not None:
                unit = Unit(unit_num, page_num, questions)
                units.append(unit)
                units_found += 1
                if units_found == units_to_find:
                    #Stop searching if all units int input file are found.
                    break
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

    file_path = file_array[file_index]

    questions_dict = {}
    with open(file_path, encoding="utf-8") as f:
        for row in f.readlines():
            row = row.replace('\n', '')
            vals = row.split(", ")
            unit_num = vals[0] #Type: string
            questions_dict[str(unit_num)] = list(map(int, vals[1:])) #Assigns dictionary values
            #to list of integers
    return questions_dict


def extract_image(file_path, data, bbox):
    """ Outputs an image of the randomly generated problem.
        Assumes "data" input array is in the correct order.
    """
    page_num, image_path = data["page_index"], data["IMAGE_PATH"]
    pdf = fitz.open(file_path)
    page = pdf[page_num]
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1, 1).prescale(2, 2), clip=bbox)
    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    image.save(image_path)


def prompt_for_generation(file_path, units):
    """Gets user input [y/n]. If user enters 'y', generate a problem and output an image."""
    while True:
        try:
            user_in = str(input(Fore.LIGHTYELLOW_EX + "Generate question?[y/n] " + Style.RESET_ALL))
            if user_in.lower() == "y":
                q_data = generate_question(file_path, units)
                bbox = (q_data["left"] - q_data["buffer_left"],
                        q_data["top"] - q_data["buffer_top"],
                        q_data["left"] + q_data["buffer_right"],
                        q_data["top"] + q_data["buffer_bottom"])
                extract_image(file_path, q_data, bbox)
                draw_box(q_data)
            elif user_in.lower() == 'n':
                break
            else:
                raise ValueError("user_in was type str, but user_in[0] was neither 'y' or 'n'.")
        except ValueError:
            print("Please enter either 'y' or 'n'.")


def generate_question(file_path, units):
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

    left, top = None, None
    page_index = None

    with pdfplumber.open(file_path) as pdf:
        break_out_flag = False
        for i in range(first_page - 1, last_page - 1):
            page = pdf.pages[i]
            for element in page.extract_words():
                if element['text'] == f'{question}.':
                    left = element['x0']
                    top = element['top']
                    page_index = i
                    print("Unit", unit.unit_num, "question", question, "on page", page_index + 1)
                    break_out_flag = True #signals program to break out of nested loop
                    break
                elif left is None and i is last_page - 1:
                    print("ERROR: question", question, "not found.")
            if break_out_flag:
                break

    BUFFER_TOP = 20
    BUFFER_BOTTOM = 100
    BUFFER_LEFT = 20
    BUFFER_RIGHT = 250

    data = {
        "IMAGE_PATH": "generated question.png",
        "page_index": page_index,
        "left": left,
        "top": top,
        "buffer_top": BUFFER_TOP,
        "buffer_bottom": BUFFER_BOTTOM,
        "buffer_left": BUFFER_LEFT,
        "buffer_right": BUFFER_RIGHT
    }
    return data


def draw_box(q_data):
    """Draws a red box around given question."""
    BOX_WIDTH = 40
    image_path = q_data["IMAGE_PATH"]
    left = 30
    top = 30
    bottom = top + BOX_WIDTH
    right = left + BOX_WIDTH

    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    draw.rectangle((left, top, right, bottom), outline="red", width=3)
    image.save(image_path)

main()
