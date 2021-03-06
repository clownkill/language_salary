import os
from itertools import count

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_rub_salary_hh(vacancy):
    salary = vacancy['salary']
    if not salary or salary['currency'] != 'RUR':
        return None
    return predict_salary(salary['from'], salary['to'])


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] != 'rub':
        return None
    salary_from = vacancy['payment_from']
    salary_to = vacancy['payment_to']
    return predict_salary(salary_from, salary_to)


def predict_salary(salary_from, salary_to):
    if not salary_from and salary_to:
        return salary_to * 0.8
    elif salary_from and not salary_to:
        return salary_from * 1.2
    elif salary_from and salary_to:
        return (salary_from + salary_to) / 2


def get_salary_statistics(vacancies, predict_rub_salary):
    salaries = []
    processed_vacancies = 0
    for vacancy in vacancies:
        salary = predict_rub_salary(vacancy)
        if salary:
            salaries.append(salary)
            processed_vacancies += 1
    return salaries, processed_vacancies


def get_hh_vacancies(text, area_name='Moscow', period=30):
    url = 'https://api.hh.ru/vacancies'
    vacancies = []
    vacancies_quantity = 0
    params = {
        'text': text,
        'area.name': area_name,
        'period': period,
    }
    for page in count(0, 1):
        params['page'] = page
        response = requests.get(url, params=params)
        response.raise_for_status()
        responsed_vacansies = response.json()
        vacancies_quantity = responsed_vacansies['found']
        vacancies.extend(responsed_vacansies['items'])
        pages = responsed_vacansies['pages']
        if page == pages - 1:
            break
    return vacancies, vacancies_quantity


def get_sj_vacancies(apikey, keyword, town='москва', quantity=100):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    vacancies = []
    vacancies_quantity = 0
    headers = {
        'X-Api-App-Id': apikey,
    }
    params = {
        'keyword': keyword,
        'town': town,
        'count': quantity,
    }
    for page in count(0, 1):
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        responsed_vacansies = response.json()
        vacancies_quantity = responsed_vacansies['total']
        vacancies.extend(responsed_vacansies['objects'])
        more = responsed_vacansies['more']
        if not more:
            break
    return vacancies, vacancies_quantity


def get_hh_statistics(languages):
    language_stats = {}
    for language in languages:
        query_text = f'программист {language}'
        vacancies, vacancies_quantity = get_hh_vacancies(query_text)
        salaries, processed_vacancies = get_salary_statistics(vacancies, predict_rub_salary_hh)
        try:
            average_salary = int(sum(salaries) / processed_vacancies)
        except ZeroDivisionError:
            average_salary = 0
        language_stats[language] = {
            'vacancies_found': vacancies_quantity,
            'processed_vacancies': processed_vacancies,
            'average_salary': average_salary,
        }
    return language_stats


def get_sj_statistics(apikey, languages):
    language_stats = {}
    for language in languages:
        query_text = f'программист {language}'
        vacancies, vacancies_quantity = get_sj_vacancies(apikey, query_text)
        salaries, processed_vacancies = get_salary_statistics(vacancies, predict_rub_salary_sj)
        try:
            average_salary = int(sum(salaries) / processed_vacancies)
        except ZeroDivisionError:
            average_salary = 0
        language_stats[language] = {
            'vacancies_found': vacancies_quantity,
            'processed_vacancies': processed_vacancies,
            'average_salary': average_salary,
        }
    return language_stats


def create_table(languages_stats, table_name):
    table_rows = ((
        'Язык программирования',
        'Вакансий найдено',
        'Вакансий обработано',
        'Средняя зарплата',
    ),)
    for language, language_statistic in languages_stats.items():
        table_rows += (
            language,
            language_statistic['vacancies_found'],
            language_statistic['processed_vacancies'],
            language_statistic['average_salary'],
        ),
    table_instance = AsciiTable(table_rows, table_name)
    return table_instance.table


def main():
    load_dotenv()
    sj_apikey = os.getenv('SJ_KEY')
    languages = [
        'JavaScript',
        'Java',
        'Python',
        'Ruby',
        'PHP',
        'C++',
        'C#',
        'C',
        'Go',
        'Scala',
    ]
    hh_statistic = get_hh_statistics(languages)
    sj_statistic = get_sj_statistics(sj_apikey, languages)
    print(create_table(hh_statistic, 'HeadHunter Moscow'))
    print()
    print(create_table(sj_statistic, 'SuperJob Moscow'))


if __name__ == '__main__':
    main()
