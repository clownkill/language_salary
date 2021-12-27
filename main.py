import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_rub_salary_hh(vacancie):
    salary = vacancie['salary']
    if not salary or salary['currency'] != 'RUR':
        return None
    return predict_salary(salary['from'], salary['to'])


def predict_rub_salary_sj(vacancie):
    if vacancie['currency'] != 'rub':
        return None
    salary_from = vacancie['payment_from']
    salary_to = vacancie['payment_to']
    return predict_salary(salary_from, salary_to)


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from and not salary_to:
        return salary_from * 1.2
    elif not salary_from and salary_to:
        return salary_to * 0.8
    return None


def get_hh_statistics(languages):
    url_hh = 'https://api.hh.ru/vacancies'
    languages_stat = {}
    for language in languages:
        languages_stat[language] = {}
        page = 0
        pages = 1
        vacancies, salaries = [], []
        vacancies_proceed = 0
        while page < pages:
            params_hh = {
                'text': f'программист {language}',
                'area.name': 'Moscow',
                'period': 30,
                'page': page,
            }
            vacancies_data = requests.get(url_hh, params=params_hh).json()
            languages_stat[language]['vacancies_found'] = vacancies_data['found']
            for vacancie_info in vacancies_data['items']:
                vacancies.append(vacancie_info)
            page += 1
            pages = vacancies_data['pages']
        for vacancie in vacancies:
            salary = predict_rub_salary_hh(vacancie)
            if salary:
                salaries.append(salary)
                vacancies_proceed += 1
        languages_stat[language]['vacancies_proceed'] = vacancies_proceed
        languages_stat[language]['average_salary'] = int(sum(salaries) / vacancies_proceed)
    return languages_stat


def get_sj_statistics(apikey, languages):
    url_sj = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {
        'X-Api-App-Id': apikey,
    }
    languages_stat = {}
    for language in languages:
        languages_stat[language] = {}
        page = 0
        vacancies_proceed = 0
        vacancies, salaries = [], []
        more = True
        while more:
            params = {
                'keyword': f'программист {language}',
                'town': 'москва',
                'count': 100,
                'page': page,
                'more': more,
            }
            vacancies_data = requests.get(url_sj, headers=headers, params=params).json()
            languages_stat[language]['vacancies_found'] = vacancies_data['total']
            for vacancie_info in vacancies_data['objects']:
                vacancies.append(vacancie_info)
            page += 1
            more = vacancies_data['more']
        for vacancie in vacancies:
            salary = predict_rub_salary_sj(vacancie)
            if salary:
                salaries.append(salary)
                vacancies_proceed += 1
        languages_stat[language]['vacancies_proceed'] = vacancies_proceed
        languages_stat[language]['average_salary'] = int(sum(salaries) / vacancies_proceed)
    return languages_stat


def print_table(languages_stat, table_name):
    table_data = (
        ('Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'),
    )
    for name, info in languages_stat.items():
        table_data += (name, info['vacancies_found'], info['vacancies_proceed'], info['average_salary']),
    table_instance = AsciiTable(table_data, table_name)
    print('\n', table_instance.table, '\n')



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
    print_table(hh_statistic, 'HeadHunter Moscow')
    print_table(sj_statistic, 'SuperJob Moscow')


if __name__ == '__main__':
    main()
