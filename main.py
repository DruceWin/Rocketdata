import datetime
import json

from requests_html import HTMLSession


def timer(fn):
    def wrapper(*args, **kwargs):
        start_time = datetime.datetime.now()
        print(f"\nНачало выполнения!\n{start_time}\n")
        fn(*args, **kwargs)
        finish_time = datetime.datetime.now()
        print(f"\nЗавершено!\n{finish_time}, (затраченное время - {finish_time - start_time})")
    return wrapper


class DataCollector:
    def __init__(self):
        self._result_list = []

    def append_result_list(self, name: str, address: str, latlon: list[float],
                           phones: list[str], working_hours: list[str]):
        self._result_list.append({
            "name": name,
            "address": address,
            "latlon": latlon,
            "phones": phones,
            "working_hours": working_hours
        })
        print(self._result_list[-1])

    def clear_result_list(self):
        self._result_list = []

    @timer
    def get_yapdomik_data(self) -> list[dict]:
        _name = 'Японский Домик'

        def get_data_by_city(url: str):
            session = HTMLSession()
            r = session.get(f'{url}/about')
            print(f'{url}/about')
            # извлечение количества точек в городе через JS
            js = '''
            () => {
                return {
                    len: document.getElementsByClassName("mb-6 mt-6").item(0).getElementsByTagName('li').length
                }
            }
            '''
            length = r.html.render(script=js, reload=False, timeout=30)["len"]
            print('Кол-во адресов', length)

            # Постоянные параметры
            address = r.html.find('a.city-select__current', first=True).text
            phones = [r.html.find('div.contacts__phone', first=True).find('a', first=True).text]

            for i in range(length):
                print(f"{i} - ", end="")
                # прокликивание каждой точки для извлечения времени работы и заодно адреса с координатами
                click_point = f"""
                () => {{
                    setTimeout(function(){{
                        document.getElementsByClassName('mb-6 mt-6').item(0).getElementsByTagName('li').item({i}).click();
                    }}, 800);
                }}
                """
                r.html.render(script=click_point, sleep=1, reload=True, timeout=length*10)
                active = r.html.find('.active', first=True)
                print(True if active else False)
                worktime = r.html.find('.work-time')
                self.append_result_list(
                    _name,
                    f"{address}, {active.find('span', first=True).text}",
                    [float(active.attrs["data-latitude"]), float(active.attrs["data-longitude"])],
                    phones,
                    [i.text.replace("\n", " ") for i in worktime]
                )

            session.close()

        first_session = HTMLSession()
        base_page = first_session.get('https://yapdomik.ru')
        list_of_city = base_page.html.find('a.city-list-item')
        print(f"Список городов компании '{_name}': {' '.join([c.text for c in list_of_city])}")
        for c in list_of_city:
            url = c.attrs['href']
            get_data_by_city(url)

        return self._result_list

    def save_json(self, file_name: str, data: list[dict] | dict = None):
        if not data:
            data = self._result_list
        with open(f"{file_name}.json", "w", encoding='utf-8') as f:
            text = json.dumps(data, ensure_ascii=False)
            f.write(text)
        self.clear_result_list()


if __name__ == '__main__':
    collector = DataCollector()

    print('Сбор информации по yapdomik.ru')
    collector.get_yapdomik_data()
    collector.save_json("yapdomik")
    print('Файл сохранён в - yapdomik.json')


# Первоначальная попытка, пока не упёрся в отсутствие актуальных данных по времени работы в yapdomik.ru  :)
# x = requests.get('https://dentalia.com/clinica/?jsf=jet-engine:clinicas-archive&tax=estados:19')
# page = requests.get('https://omsk.yapdomik.ru/about')
# soup = BeautifulSoup(page.text, 'html.parser')
#
# # initial_state = re.search("window.initialState = ", page.text)
# scripts = soup.findAll('script')
#
# name = 'Японский Домик'
# address = soup.find('div', class_='city-select').find('a').text
# phones = [soup.find('div', class_='contacts__phone').find('a').text]
#
# initial_state = ''
#
# result_list = []
# for s in scripts:
#     if 'window.initialState' in s.text:
#         initial_state = json.loads(s.text[s.text.find("= ")+2:])
#         for shop in initial_state["shops"]:
#             result_list.append({
#                 "name": name,
#                 "address": f"{address}, {shop['address']}",
#                 "latlon": list(shop["coord"].values()),
#                 "phones": phones,
#                 # "working_hours": [shop["schedule"]]
#             })
#         break
#
# print(result_list)
