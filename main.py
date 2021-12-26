import requests

# LANGUAGES = [
#     'JavaScript',
#     'Java',
#     'Python',
#     'Ruby',
#     'PHP',
#     'C++',
#     'C#',
#     'C',
#     'Go',
#     'Scala'
# ]
LANGUAGES = ['Python']

url_hh = 'https://api.hh.ru/vacancies'
page = 0
pages = 1
languages_stat = {}
for language in LANGUAGES:
    # languages_stat[language] = 0
    params_hh = {
        'text': f'программист {language}',
        'area.name': 'Moscow',
        'period': 1
    }

    vacancies_data = requests.get(url_hh, params=params_hh).json()

    languages_stat[language] = vacancies_data['found']

    for vacancie in vacancies_data['items']:
        print(vacancie['salary'])


print(languages_stat)
