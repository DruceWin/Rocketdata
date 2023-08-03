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

    def clear_result_list(self):
        self._result_list = []

    @timer
    def get_yapdomik_data(self) -> list[dict]:
        _name = 'Японский Домик'

        def get_data_by_city(url: str):
            session = HTMLSession()
            r = session.get(f'{url}/about')

            # извлечение количества точек в городе через JS
            js = '''
            () => {
                return {
                    len: document.getElementsByClassName("mb-6 mt-6").item(0).getElementsByTagName('li').length
                }
            }
            '''
            length = r.html.render(script=js, reload=False, timeout=30)["len"]

            # Постоянные параметры
            address = r.html.find('a.city-select__current', first=True).text
            phones = [r.html.find('div.contacts__phone', first=True).find('a', first=True).text]

            for i in range(length):
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
        for c in list_of_city:
            url = c.attrs['href']
            get_data_by_city(url)

        return self._result_list

    @timer
    def get_dentalia_data(self) -> list[dict]:
        _name = 'dentalia'

        first_session = HTMLSession()
        # r = first_session.get('https://dentalia.com/clinica/')
        r = first_session.get('https://dentalia.com/clinica/?jsf=jet-engine:clinicas-archive&tax=estados:19')
        print(True if r.html.html else False)
        print(datetime.datetime.now())
        r.html.render(reload=True, sleep=5, timeout=120)
        x = r.html.find('div[data-elementor-type="archive"]',
                        first=True).find('div.jet-listing-grid', first=True)
        print(x.html)
        list_of_clinics = x.find('div.jet-listing-grid__item')
        print(list_of_clinics)
        print('Кол-во адресов', len(list_of_clinics))

        counter = 0
        for i in list_of_clinics:
            print(f"{counter} - ", end="")
            counter += 1
            name = f"{_name} {i.find('h3.elementor-heading-title', first=True).text}"
            address_phones_worktime = i.find('div.jet-listing-dynamic-field__content')
            address = address_phones_worktime[0].text
            # latlon = 1
            phones1 = address_phones_worktime[1].text.split()
            phones2 = [i.find('a[href^="tel"]').attrs['href'][3:]]
            phones = phones1 + phones2
            worktime = address_phones_worktime[2].text
            print(
                name, address, phones, worktime
            )
            break
            # self.append_result_list(
            #     f"{_name} {}",
            #     f"{address}, {active.find('span', first=True).text}",
            #     [float(active.attrs["data-latitude"]), float(active.attrs["data-longitude"])],
            #     phones,
            #     [i.text.replace("\n", " ") for i in worktime]
            # )

        return self._result_list

    @timer
    def get_santaelena_data(self) -> list[dict]:
        _name = 'Pastelería Santa Elena'

        def get_data_by_city(url: str, city_name: str):
            session = HTMLSession()
            r = session.get(url)
            cards = r.html.find(
                'div[data-elementor-type="wp-page"]', first=True
            ).find('div.elementor-column-wrap.elementor-element-populated')
            cards = [i for i in cards if i.find('a[href^="https://www.google.com/maps"]')]

            map_session = HTMLSession()
            r_map = map_session.get(cards[0].find(
                'a[href^="https://www.google.com/maps"]', first=True).attrs['href'])

            js_for_map = '''
            () => {
                elem = document.querySelectorAll('div[index]');
                filtElem = Array.from(elem).filter(el => {return !el.attributes.subindex});
                
                function clickElement(element, callback) {
                  element.click();
                    console.log('click')
                  setTimeout(callback, 1000);
                };
                
                function processElements() {
                  myDict = {};
                  let i = 0;
                  function iterate() {
                    if (i < filtElem.length) {
                      clickElement(filtElem[i], function() {
                        console.log(filtElem[i].querySelector('div[aria-label]').innerText);
                        console.log(document.querySelectorAll('a[dir]')[1].href);
                          myDict[filtElem[i].querySelector('div[aria-label]').innerText] = document.querySelectorAll('a[dir]')[1].href;
                        i++;
                        setTimeout(iterate, 500);
                      });
                    }
                  }
                
                  iterate();
                  return myDict
                };
                
                function returnMyNewD(element, callback) {
                  element.click();
                    console.log('click')
                  setTimeout(callback, 1000);
                };
                
                return {
                    data: processElements(),
                }
            }
            '''
            raw_coordinates = r_map.html.render(script=js_for_map, reload=True, sleep=10, timeout=30)
            print(raw_coordinates)
            print('Нашёл как вытащить координаты, но не хватило времени и знаний в JavaScript на реализацию :(')
            print(r_map.html.find('a[dir]')[1].attrs['href'])

            for i in cards:
                text_part = i.find('div.elementor-text-editor', first=True).text
                kw = ('Dirección:', 'Teléfono:', 'Horario de atención:')

                address = text_part[text_part.find(kw[0])+len(kw[0]):text_part.find(kw[1])].strip().replace("\n", " ")
                phone = text_part[text_part.find(kw[1])+len(kw[1]):text_part.find(kw[2])].strip()
                worktime = text_part[text_part.find(kw[2])+len(kw[2]):].strip()
                self.append_result_list(
                    f"{_name} {i.find('h3.elementor-heading-title', first=True).text}".replace("\n", " "),
                    f"{city_name}, {address}",
                    [float(0), float(0)],
                    phone.split('\n'),
                    worktime.split('\n')
                )

        first_session = HTMLSession()
        base_page = first_session.get('https://www.santaelena.com.co/')
        url_for_shops = 'https://www.santaelena.com.co/tiendas-pasteleria/'
        list_of_city = base_page.html.find(
            'nav.elementor-nav-menu--main', first=True
        ).find(f'a[href^="{url_for_shops}"]')
        list_of_city = [i for i in list_of_city if i.attrs['href'] != url_for_shops]
        for c in list_of_city:
            url = c.attrs['href']
            name_of_city = c.text[c.text.find(' en ')+4:]
            get_data_by_city(url, name_of_city)

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

    print('Сбор информации по santaelena.com.co')
    collector.get_santaelena_data()
    collector.save_json("santaelena")
    print('Файл сохранён в - santaelena.json')

    print('Сбор информации по yapdomik.ru')
    collector.get_yapdomik_data()
    collector.save_json("yapdomik")
    print('Файл сохранён в - yapdomik.json')

    print('Сбор информации по dentalia.com оказался проблемны и на него уже не хватило времени...')
    # collector.get_dentalia_data()
    # collector.save_json("dentalia")
    # print('Файл сохранён в - dentalia.json')
