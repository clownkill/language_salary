import requests
import os
from dotenv import load_dotenv
from itertools import count
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


def get_hh_vacancies(url, text, area_name, period):
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


def get_sj_vacancies(url, apikey, keyword, town, quantity):
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
    url = 'https://api.hh.ru/vacancies'
    language_stat = {}
    for language in languages:
        params = {
            'text': f'программист {language}',
            'area_name': 'Moscow',
            'period': 30,
        }
        vacancies, vacancies_quantity = get_hh_vacancies(url, **params)
        salaries, processed_vacancies = get_salary_statistics(vacancies, predict_rub_salary_hh)
        try:
            average_salary = int(sum(salaries) / processed_vacancies)
        except ZeroDivisionError:
            average_salary = 0
        language_stat[language] = {
            'vacancies_found': vacancies_quantity,
            'processed_vacancies': processed_vacancies,
            'average_salary': average_salary,
        }
    return language_stat


def get_sj_statistics(apikey, languages):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    language_stat = {}
    for language in languages:
        params = {
            'keyword': f'программист {language}',
            'town': 'москва',
            'quantity': 100,
        }
        vacancies, vacancies_quantity = get_sj_vacancies(url, apikey, **params)
        salaries, processed_vacancies = get_salary_statistics(vacancies, predict_rub_salary_sj)
        try:
            average_salary = int(sum(salaries) / processed_vacancies)
        except ZeroDivisionError:
            average_salary = 0
        language_stat[language] = {
            'vacancies_found': vacancies_quantity,
            'processed_vacancies': processed_vacancies,
            'average_salary': average_salary,
        }
    return language_stat


def create_table(languages_stat, table_name):
    table_data = (
        (
            'Язык программирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата'
        ),
    )
    for name, info in languages_stat.items():
        table_data += (
                          name,
                          info['vacancies_found'],
                          info['processed_vacancies'],
                          info['average_salary']
                      ),
    table_instance = AsciiTable(table_data, table_name)
    return f'\n {table_instance.table} \n'


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
        'Scala'
    ]
    hh_statistic = get_hh_statistics(languages)
    sj_statistic = get_sj_statistics(sj_apikey, languages)
    print(create_table(hh_statistic, 'HeadHunter Moscow'))
    print(create_table(sj_statistic, 'SuperJob Moscow'))


if __name__ == '__main__':
    main()
