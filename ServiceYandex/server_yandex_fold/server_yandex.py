#=============================================================================================================
#=============================================================================================================

from flask import Flask, Response, request, session, jsonify, render_template, redirect, make_response
import logging
import os
import json
import random
import string
import copy
from server_yandex_fold.db_yandex import Database
from urllib.parse import parse_qs

# from werkzeug.wrappers import Request

#=============================================================================================================
#=============================================================================================================


logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
app.config['SECRET_KEY'] = '153844a6a0d77c497ad2e3a74fdfe54cdf3a055c'
db_y = Database('data/base.db')


#=============================================================================================================
#=============================================================================================================

def gen_auth_code(stringLength=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for i in range(stringLength))

def gen_cookie(str_len = 20):
    cookie = os.urandom(str_len).hex()
    return cookie

def gen_token(str_len = 19):
    cookie = os.urandom(str_len).hex()
    return cookie

# Генерирует json ответ для запроса query
def set_json_query_sensor(id, temp_1, voltage_1, on_off):
    
    with open(f'ServiceYandex/server_yandex_fold/jsons/query.json', 'r') as file:
            js = json.load(file)
    
    j_code_1 = json.loads('''[
        {
            "type": "devices.properties.float",
            "state": {
                "instance": "temperature",
                "value": "---"
            }
        },
        {
                "type": "devices.properties.float",
                "state": {
                    "instance": "voltage",
                    "value": "---"
                }
        }
    ]''')




    js['payload']['devices'][0]['id'] = id
    js['payload']['devices'][0]['properties'] = j_code_1
    js['payload']['devices'][0]['properties'][0]['state']['value'] = temp_1
    js['payload']['devices'][0]['properties'][1]['state']['value'] = voltage_1
    # js['payload']['devices'][0]['properties'][2]['state']['value'] = instance


    print(js)
    return js

# Генерирует json ответ для запроса devices
def set_json_devices(token):

    score = db_y.get_number_esp(token=token)
    user_id = db_y.get_users_data_by_token(token=token)[0]

    with open(f'ServiceYandex/server_yandex_fold/jsons/esp.json', 'r') as file:
            js_esp = json.load(file)

    with open(f'ServiceYandex/server_yandex_fold/jsons/devices.json', 'r') as file:
            js_devices = json.load(file)


    js_devices['payload']['user_id'] = user_id

    for i in range(score):
        js = copy.deepcopy(js_esp)
        js['id'] = f'1_{i}'
        

        js_devices['payload']['devices'].append(js)

    # print(js_devices)
       

    return js_devices


def set_json_action(token, id, on_off, action_type):
    
    # Если действие включить и выключить
    if action_type == "devices.capabilities.on_off":

        esp_id = int(id.split('_')[-1])

        js_capabilities_on_off = json.loads('''[{
        "type": "devices.capabilities.on_off",
        "state": {
            "instance": "on",
            "action_result": {
                "status": "DONE"
                    } 
                } 
            }]''')
        

        
        with open(f'ServiceYandex/server_yandex_fold/jsons/action.json', 'r') as file:
            js = json.load(file)

        js['payload']['devices'][0]['id'] = id
        js['payload']['devices'][0]['capabilities'] = js_capabilities_on_off
        
        db_y.set_on_off(token=token, esp_id=esp_id, on_off=on_off)

        return js
        
#=============================================================================================================
#================================================== Дикораторы ===============================================

# HEAD /v1.0/ - работает ли провайдер
@app.route('/v1.0/', methods=['HEAD'])
def handle_head():
    logging.info('HEAD request received')
    return Response(status=200)



# POST /v1.0/user/unlink
@app.route('/v1.0/user/unlink', methods=['POST'])
def unlink_user():
    data_headers = request.headers
    # logging.info(f"Unlink request received: {data}")
    
    with open(f'ServiceYandex/server_yandex_fold/jsons/unlink.json', 'r') as file:
            js_unlink = json.load(file)

    token = data_headers.get('Authorization').split()[1]
    request_id = data_headers.get('X-Request-Id')
    db_y.unlink(token=token)


    js_unlink['request_id'] = str(request_id)

    # print(js_unlink)


    return js_unlink, 200



# GET /v1.0/user/devices
@app.route('/v1.0/user/devices', methods=['GET'])
def get_devices():
    data_headers = request.headers
    # print(data_headers)
    # logging.info("GET request received at /v1.0/user/devices")
    token = data_headers.get('Authorization').split()[1]

    data_devices = set_json_devices(token)

    return jsonify(data_devices), 200



# POST /v1.0/user/devices/query
@app.route('/v1.0/user/devices/query', methods=['POST'])
def query_user_devices():
    headers_data = request.headers
    js_data = request.json
    # print("\n\n\n",request.data,"\n\n\n", request.form.get('client_id'),"\n\n\n",request.get_json(),"\n\n\n", request.form,"\n\n\n", request.get_data(as_text=True),"\n\n\n")
    print(headers_data)
    token = headers_data.get('Authorization').split()[1]
    id = js_data['devices'][0]['id']
    esp_id = int(id.split('_')[-1])

    

    
    esp_data = db_y.get_esp_data(token=token, esp_id=esp_id)[0]
    temp_1 = esp_data[0]
    temp_2 = esp_data[1]
    voltage_1 = esp_data[2]
    voltage_2 = esp_data[3]
    on_off = esp_data[4] 


    print('esp_id -', esp_id)
    print('esp_data -', esp_data)

    

    device_status = set_json_query_sensor(id = id, temp_1=temp_1, voltage_1=voltage_1, on_off=on_off)

    return jsonify(device_status), 200




# POST /v1.0/user/devices/action
@app.route('/v1.0/user/devices/action', methods=['POST'])
def action_user_devices():
    headers_data = request.headers
    js_data = request.json
    
    token = headers_data.get('Authorization').split()[1]
    id = js_data['payload']['devices'][0]['id']
    action_type = js_data['payload']['devices'][0]['capabilities'][0]['type']
    on_off = js_data['payload']['devices'][0]['capabilities'][0]['state']['value']

    device_action = set_json_action(id=id, action_type=action_type, on_off=on_off, token=token)

    # print("data -",data)
    print("device_action -", device_action)
    if on_off:
        print("\n\n\nДaтчик on!\nДaтчик on!\nДaтчик on!\n\n\n")
    else:
        print("\n\n\nДaтчик off!\nДaтчик off!\nДaтчик off!\n\n\n")


    return device_action, 200



#=============================================================================================================
#================================================= Авторизация ===============================================

@app.route('/authorize', methods=['GET', 'POST'])
def authorize():
    if request.method == 'GET':
        
        
        res = make_response(render_template('login_form.html'))
        redirect_uri = request.args.get('redirect_uri')

        cookie = gen_cookie()
        res.set_cookie("ck", cookie)

        
        client_id = request.args.get('client_id')
        scope = request.args.get('scope')
        state = request.args.get('state')

        # Если у пользователя нет cookie, или его нет в базе данных - добавить 
        if request.cookies.get("ck") == None or not db_y.is_cookie_in_base(request.cookies.get("ck")):
            print(1)
            cookie = gen_cookie()
            res.set_cookie("ck", cookie)
            db_y.add_conn(client_id, scope, state, cookie)

        else:
            db_y.update_conn_by_cookie(request.cookies.get("ck"), client_id, scope, state)

        # res.delete_cookie("ck")
        # print('ck - ')
        return res
    
    if request.method == 'POST':

        pincode = str(request.form.get('pincode'))

        # print(request.cookies.get("ck"), end="\n\n")
            
        if db_y.is_yandex_link_code_in_base(str(pincode)):
            

            auth_code = gen_auth_code(8)
            db_y.add_users(request.cookies.get("ck"), str(auth_code))
            data = db_y.get_users_data_by_cookie(request.cookies.get("ck"))
            print(data)
            client_id = data[0]
            scope = data[1]
            state = data[2]
            code = data[3]

            db_y.link_yandex_users(client_id, pincode)

            #print("data -", data, "\ncookie -", request.cookies.get("ck"))

            # unlink доделай users отвязку!!!



            target_url = f'https://social.yandex.net/broker/redirect?code={code}&client_id={client_id}&scope={scope}&state={state}'

            # # Перенаправляем на другой сервер
            return redirect(target_url)

        else:
            # Авторизация не удалась
            return render_template('login_form.html', error="Неверный пинкод")       
        
@app.route('/token', methods=['GET', 'POST'])
def token():
    # code = request.args.get('code')
    # print(code)
    data = parse_qs(request.get_data(as_text=True))
    code = data.get('code', [None])[0]

    if db_y.can_add_token(code):
        print(1)

        token = gen_token(19)

        # print(code, token)

        db_y.add_token(code, token)

        return jsonify({'access_token' : token, 'expires_in' : 4294967296})
    return("пп")

#=============================================================================================================
#=============================================================================================================

def server_yandex_process():
    context=('/etc/letsencrypt/live/daniko.ddns.net/fullchain.pem','/etc/letsencrypt/live/daniko.ddns.net/privkey.pem')
    app.run(host='0.0.0.0', port=5010, ssl_context=context) # ssl_context=context