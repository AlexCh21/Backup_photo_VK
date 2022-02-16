import os
import requests
import datetime


def get_token_id(name_foto):
    with open(os.path.join(os.getcwd(), name_foto), 'r') as token_file:
        token = token_file.readline().strip()
        id = token_file.readline().strip()
    return [token, id]


def find_max_dpi(dict_in_search):
    max_dpi = 0
    for j in range(len(dict_in_search)):
        file_dpi = dict_in_search[j].get('width') * dict_in_search[j].get('height')
        if file_dpi > max_dpi:
            max_dpi = file_dpi
            need_elem = j
    return dict_in_search[need_elem].get('url'), dict_in_search[need_elem].get('type')


def time_convert(time_unix):
    time_bc = datetime.datetime.fromtimestamp(time_unix)
    str_time = time_bc.strftime('%Y-%m-%d time %H-%M-%S')
    return str_time


class User_VK:
    '''Получать фотографии с профиля. Для этого нужно использовать метод [photos.get](https://vk.com/dev/photos.get).'''
    def __init__(self, token_list, version='5.131'):
        self.token = token_list[0]
        self.id = token_list[1]
        self.version = version
        self.start_params = {'access_token': self.token, 'v': self.version}
        self.json, self.export_dict = self._sort_info()

    def _get_photo_info(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id,
                  'album_id': 'profile',
                  'photo_sizes': 1,
                  'extended': 1}
        photo_info = requests.get(url, params={**self.start_params, **params}).json()['response']
        return photo_info['count'], photo_info['items']

    def _get_logs_only(self):
        photo_count, photo_items = self._get_photo_info()
        result = {}
        for i in range(photo_count):
            likes_count = photo_items[i]['likes']['count']
            url_download, picture_size = find_max_dpi(photo_items[i]['sizes'])
            time_warp = time_convert(photo_items[i]['date'])

            new_value = result.get(likes_count, [])
            new_value.append({'add_name': time_warp,
                              'url_picture': url_download,
                              'size': picture_size})
            result[likes_count] = new_value
        return result

    def _sort_info(self):
        files_list = []
        sorted_dict = {}
        picture_dict = self._get_logs_only()
        for elem in picture_dict.keys():
            for value in picture_dict[elem]:
                if len(picture_dict[elem]) == 1:
                    name_foto = f'{elem}.jpeg'
                else:
                    name_foto = f'{elem} {value["add_name"]}.jpeg'
                files_list.append({'file name': name_foto, 'size': value["size"]})
                sorted_dict[name_foto] = picture_dict[elem][0]['url_picture']
        return files_list, sorted_dict


class YaDisk:
    '''Сохранять фотографии максимального размера(ширина/высота в пикселях) на Я.Диске.'''
    def __init__(self, folder_name, token_list):
        self.token = token_list[0]
        self.url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        self.headers = {'Authorization': self.token}
        self.folder = self._create_folder(folder_name)

    def _create_folder(self, folder_name):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': folder_name}
        if requests.get(url, headers=self.headers, params=params).status_code != 200:
            requests.put(url, headers=self.headers, params=params)
            print(f'\nПапка {folder_name} создана на Яндекс диске\n')
        else:
            print(f'\nПапка {folder_name} существует.\n')
        return folder_name

    def _in_folder(self, folder_name):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': folder_name}
        resource = requests.get(url, headers=self.headers, params=params).json()['_embedded']['items']
        in_folder_list = []
        for elem in resource:
            in_folder_list.append(elem['name'])
        return in_folder_list

    def create_copy(self, dict_files):
        files_in_folder = self._in_folder(self.folder)
        number_files = 0
        for key in dict_files.keys():
            if key not in files_in_folder:
                params = {'path': f'{self.folder}/{key}',
                          'url': dict_files[key],
                          'overwrite': 'false'}
                requests.post(self.url, headers=self.headers, params=params)
                print(f'Файл {key} добавлен')
                number_files += 1
            else:
                print(f'отменено:файл {key} существует')
        print(f'\nДобавлено {number_files} файлов')


token_VK = 'tokenVK.json' # id пользователя vk
token_YD = 'tokenYD.json' # токен с [Полигона Яндекс.Диска](https://yandex.ru/dev/disk/poligon/)

VK_id = User_VK(get_token_id(token_VK))
print('javascript', VK_id.json) # json-файл с информацией по файлу:

yandex_id = YaDisk('Backup_photo_VK', get_token_id(token_YD))
yandex_id.create_copy(VK_id.export_dict)

