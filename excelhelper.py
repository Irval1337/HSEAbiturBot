import datetime

import pandas as pd
import re
from settings import courses
import math

class ExamResult:
    def __init__(self, exam: str, result: int):
        self.exam = exam
        self.result = result


class Applicant:
    def __init__(self, rating: int, SNILS: str, BVI: bool, special_quota: bool, target_quota: bool, separate_quota: bool,
                 target_prior: int, other_prior: int, highest_prior: int, paid_prior: int, exam_results: list[ExamResult],
                 additional_result: int, sum_result: int, place_type: int, given_docs: bool, approval: bool, preemptive: bool,
                 dormitory: bool, docs_return: bool):
        self.rating = rating
        self.SNILS = SNILS
        self.BVI = BVI
        self.special_quota = special_quota
        self.separate_quota = separate_quota
        self.target_quota = target_quota
        self.target_prior = target_prior
        self.other_prior = other_prior
        self.highest_prior = highest_prior
        self.paid_prior = paid_prior
        self.exam_results = exam_results
        self.additional_result = additional_result
        self.sum_result = sum_result
        self.place_type = place_type
        self.given_docs = given_docs
        self.approval = approval
        self.preemptive = preemptive
        self.dormitory = dormitory
        self.docs_return = docs_return

    def make_message(self, bvi: int) -> str:
        return f"Текущее место в рейтинге: {self.rating}\nВсего людей с БВИ: {bvi}"

class PlacesData:
    def __init__(self, budget: int, target: int, special: int, separate: int, paid: int):
        self.budget = budget
        self.target = target
        self.special = special
        self.separate = separate
        self.paid = paid

class Report:
    def __init__(self):
        self.table = pd.read_excel(courses.stats_url)
        self.courses = []
        time_str = self.table.iat[2, 0]
        time_str = time_str[time_str.find("отчета ") + len("отчета "):]
        self.update_time = datetime.datetime.strptime(time_str, '%d.%m.%Y %H:%M:%S')
        for i in range(len(courses.course_ord)):
            self.courses.append(CourseTable(courses.course_ord[i], i + 1, self))
        self.report_time = datetime.datetime.now()

class CourseTable:
    def __init__(self, course_title: str, id: int, report: Report):
        is_code = re.fullmatch(r'\d\d\.\d\d\.\d\d', course_title)
        found = []
        for course in courses.course_list:
            if (course.code if is_code else course.title) == course_title:
                found.append(course)
        if len(found) == 0:
            raise Exception("Курс не найден")
        if len(found) > 1:
            raise Exception("Имя курса не является однозначным")

        self.course_data = found[0]
        self.table = pd.read_excel(self.course_data.table_url)
        self.id = id
        self.applicants = dict()
        count = len(self.table) - 14
        self.places_separate_bvi = 0

        for i in range(14, 14 + count):
            end_exams = 11
            exams = []
            while not self.table.iat[13, end_exams].startswith("Итоговая"):
                exams.append(ExamResult(self.table.iat[14, end_exams], self.parse_int(self.table.iat[i, end_exams])))
                end_exams += 1
            applicant = Applicant(self.table.iat[i, 0], self.parse_snils(self.table.iat[i, 1]), self.parse_flag(self.table.iat[i, 3]),
                                  self.parse_flag(self.table.iat[i, 4]), self.parse_flag(self.table.iat[i, 5]), self.parse_flag(self.table.iat[i, 6]),
                                  self.parse_int(self.table.iat[i, 7]), self.parse_int(self.table.iat[i, 8]), self.parse_int(self.table.iat[i, 9]),
                                  self.parse_int(self.table.iat[i, 10]), exams, self.parse_int(self.table.iat[i, end_exams]), self.parse_int(self.table.iat[i, end_exams + 1]),
                                  self.parse_place(self.table.iat[i, end_exams + 2]), self.parse_flag(self.table.iat[i, end_exams + 3]), self.parse_flag(self.table.iat[i, end_exams + 4]),
                                  self.parse_flag(self.table.iat[i, end_exams + 5]), self.parse_flag(self.table.iat[i, end_exams + 6]), self.parse_flag(self.table.iat[i, end_exams + 7]))
            if applicant.BVI and applicant.separate_quota:
                self.places_separate_bvi += 1
            self.applicants[applicant.SNILS] = applicant

        self.places_all = PlacesData(self.parse_int(report.table.iat[6 + self.id, 6]), self.parse_int(report.table.iat[6 + self.id, 7]), self.parse_int(report.table.iat[6 + self.id, 8]),
                                     self.parse_int(report.table.iat[6 + self.id, 9]), self.parse_int(report.table.iat[6 + self.id, 15]))
        self.places_got = PlacesData(self.parse_int(report.table.iat[6 + self.id, 10]), self.parse_int(report.table.iat[6 + self.id, 11]), self.parse_int(report.table.iat[6 + self.id, 12]),
                                     self.parse_int(report.table.iat[6 + self.id, 13]), self.parse_int(report.table.iat[6 + self.id, 16]))
        self.places_bvi = self.parse_int(report.table.iat[6 + self.id, 14])

    @staticmethod
    def parse_snils(val: str):
        res = ""
        for c in val:
            if '0' <= c <= '9':
                res += c
        return res

    @staticmethod
    def parse_flag(val: str):
        return val.strip() == "Да"

    @staticmethod
    def parse_int(val: str):
        val = str(val).replace(" ", "")
        if math.isnan(float(val)):
            return 0
        return int(val)

    @staticmethod
    def parse_place(val: str):
        return 0b10 * ("Б" in val) + 0b01 * ("К" in val)


report = Report()