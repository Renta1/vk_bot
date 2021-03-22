from vk_api import VkApi, VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from random import randint
from bs4 import BeautifulSoup 
import requests

VK_TOKEN = '4b77bebecbe2310d8bf76c52b1c733a5a44a8768164e386249a04ab65ad8f32195404ba7365eee2f25fa5'
API_KEY = 'e769f0fe046f901526994f29b5bc6f8e'
WEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'

vk_session = VkApi(token=VK_TOKEN)
longpoll = VkLongPoll(vk_session)
upload = VkUpload(vk_session) 

def get_current_temperature(town):
    params = {'q':town, 'appid':API_KEY, 'units':'metric', 'mode':'json'}
    r = requests.get(WEATHER_URL, params)
    if r.status_code == 404:
        return 'Такого города не существует'
    data = r.json()
    return data['main']['temp']

def send_msg(user_id, text):  # https://vk.com/dev/messages.send
    vk_session.method('messages.send', {'user_id': user_id, 'message': text, 
                                'random_id':randint(1e16, 1e18)})
    
def get_user_name(user_id): # https://vk.com/dev/users.get
    r = vk_session.method('users.get', {'v':'5.71', 'access_token' : VK_TOKEN, 'user_ids' : user_id})
    return r[0]['first_name']

def extract_image_url(town): 
    url = 'https://ru.wikipedia.org/wiki/'
    r = requests.get(url + town)
    soup = BeautifulSoup(r.text, 'lxml')
    body = soup.find(id='bodyContent')
    img = body.find('img')
    path = 'https:' + img['src']
    return path

def send_image(user_id, town): 
    attachments = []
    image_url = extract_image_url(town)
    image = requests.get(image_url, stream=True)
    photo = upload.photo_messages(photos=image.raw)[0]
    print(image.raw)
    attachments.append(
        'photo{}_{}'.format(photo['owner_id'], photo['id'])
    )
    vk_session.method('messages.send',{ 
        'user_id':user_id,
        'attachment':','.join(attachments),'random_id':randint(1e16, 1e18)
    })
    
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me: # Получили новое сообщение
        request = event.text.lower()
        if request == 'привет':
            name = get_user_name(event.user_id)
            send_msg(event.user_id, f'Привет, {name}!')
        
        elif request == 'пока':
            send_msg(event.user_id, 'Пока!')
            
        elif 'погода' in request: # погода город
            if len(request.split())==2:
                town = request.split()[1]
                temperature = get_current_temperature(town)
                if temperature == 'Такого города не существует':
                    message = f'Такого города не существует. Попробуй ввести другой город'
                    send_msg(event.user_id, message)
                else:
                    sign = 1 if temperature > 0 else 0
                    message = f'Погода в городе {town.title()}:\n {"+"*sign}{temperature}\N{DEGREE SIGN}C'
                    send_msg(event.user_id, message)
                    send_image(event.user_id, town)
            else:
                send_msg(event.user_id, f'город не введён')
        else:
            send_msg(event.user_id, 'Я тебя не понял. Повтори еще') 