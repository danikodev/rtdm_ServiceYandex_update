#===================================================================================================
#===================================================================================================


import sqlite3
# from server_esp_fold.db_esp import Database as Database_esp

#===================================================================================================
#===================================================================================================

# db_e = Database_esp('data/base.db')



class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file, check_same_thread=False) # check_same_thread=False - убрать ошибку подключения из разнах потоков
        self.cursor = self.connection.cursor()
        

    def add_conn(self, client_id, scope, state, cookie):
        with self.connection:
            insert_query = '''
            INSERT INTO yandex_users (client_id, scope, state, cookie)
            VALUES (?, ?, ?, ?); 
            '''
            return self.cursor.execute(insert_query, (client_id, scope, state, cookie))
        
    def update_conn_by_cookie(self, cookie, client_id, scope, state):
        with self.connection:
            update_query = '''
            UPDATE yandex_users
            SET client_id = ?,
                scope = ?,
                state = ?
            WHERE cookie = ?;
            '''
            return self.cursor.execute(update_query, (client_id, scope, state, cookie))
        

    def add_users(self, cookie, code):
        with self.connection:
            update_query = '''
            UPDATE yandex_users
            SET code = ?
            WHERE cookie = ?;
            '''
            return self.cursor.execute(update_query, (code, cookie))
        
    def get_users_data_by_cookie(self, cookie):
        with self.connection:
            select_query = """
            SELECT client_id, scope, state, code
            FROM yandex_users
            WHERE cookie = ?;
            """
            self.cursor.execute(select_query, (cookie,))

            return (self.cursor.fetchone())
        
    def get_users_data_by_token(self, token):
        with self.connection:
            select_query = """
            SELECT client_id, scope, state, code
            FROM yandex_users
            WHERE token = ?;
            """
            self.cursor.execute(select_query, (token,))

            return (self.cursor.fetchone())    
    
    def add_token(self, code, token):
        with self.connection:
            update_query = '''
            UPDATE yandex_users
            SET token = ?
            WHERE code = ?;
            '''
            return self.cursor.execute(update_query, (token, code))

    def can_add_token(self, code):
        with self.connection:

            query = "SELECT EXISTS(SELECT 1 FROM yandex_users WHERE code = ?)"

            self.cursor.execute(query, (code,))
            exists = self.cursor.fetchone()[0]

            if exists:
                select_query = """
                SELECT token
                FROM yandex_users
                WHERE code = ?;
                """
                self.cursor.execute(select_query, (code,))

                if (self.cursor.fetchone())[0] == None:
                    return True
                else:
                    return False
            
            else:
                return False
        
    def is_cookie_in_base(self, cookie):
        with self.connection:
            query = '''
            SELECT * FROM yandex_users 
            WHERE cookie = ?; 
            '''
            self.cursor.execute(query, (cookie,))
            result = self.cursor.fetchone()
            if result:
                return True
            else:
                return False

    def get_users_address_yandex(self, token):
        with self.connection:

            select_query = """
            SELECT client_id
            FROM yandex_users
            WHERE token = ?;
            """
            self.cursor.execute(select_query, (token,))
            
            result = (self.cursor.fetchone())

            if result is not None:
                return result[0]
            else:
                return result
        
    def get_users_address_id(self, token):
        with self.connection:

            users_address_yandex = self.get_users_address_yandex(token)
            
            select_query = """
            SELECT id
            FROM users
            WHERE users_address_yandex = ?;
            """
            self.cursor.execute(select_query, (users_address_yandex,))
            result = self.cursor.fetchone()
            
            if result:
                return True
            else:
                return False    

    def unlink(self, token):
        with self.connection:

            users_address_yandex = self.get_users_address_yandex(token)

            update_query = '''
            UPDATE users
            SET users_address_yandex = NULL
            WHERE users_address_yandex = ?;
            '''
            self.cursor.execute(update_query, (users_address_yandex, ))


            delete_query = '''
            DELETE FROM yandex_users
            WHERE token = ?;
            '''
            return self.cursor.execute(delete_query, (token,))
        
    def is_yandex_link_code_in_base(self, yandex_link_code):
        with self.connection:
            query = '''
            SELECT * FROM users 
            WHERE yandex_link_code = ?; 
            '''
            self.cursor.execute(query, (yandex_link_code,))
            result = self.cursor.fetchone()
            if result:
                return True
            else:
                return False
            
    def get_yandex_link_code(self, yandex_link_code):
        with self.connection:
            query = '''
            SELECT * FROM users 
            WHERE yandex_link_code = ?; 
            '''
            self.cursor.execute(query, (yandex_link_code,))
            result = self.cursor.fetchone()
            return result
        
    def link_yandex_users(self, client_id, yandex_link_code):
        with self.connection:
            update_query = '''
            UPDATE users
            SET users_address_yandex = ?,
            yandex_link_code = NULL
            WHERE yandex_link_code = ?;
            '''
            return self.cursor.execute(update_query, (client_id, yandex_link_code))
        
    def get_number_esp(self, token):
        with self.connection:

            users_address_id = self.get_users_address_id(token=token)

            query = '''
            SELECT COUNT(*) FROM connections 
            WHERE users_address_id = ?; 
            '''

            self.cursor.execute(query, (users_address_id, ))

            return (self.cursor.fetchone())[0]
        
    def get_esp_address_id_by_token(self, token, esp_id=-1):
        with self.connection:

            users_address_id = self.get_users_address_id(token)

            query = '''
            SELECT esp_address_id
            FROM connections
            WHERE users_address_id = ?
            ORDER BY id;
            '''

            self.cursor.execute(query, (users_address_id, ))

            results = self.cursor.fetchall()

            if esp_id == -1:
                return results
            else:
                try:
                    return results[esp_id]
                except IndexError:
                    return results
            
    
    def get_esp_data(self, token, esp_id=0):
        with self.connection:
            esp_address_id = (self.get_esp_address_id_by_token(token, esp_id))[0]

            query = '''
                SELECT temp_1, temp_2, voltage_1, voltage_2, time
                FROM parameters
                WHERE esp_address_id = ?
                ORDER BY id;
                '''
            # print(esp_address_id)
            # print(type(esp_address_id))
            self.cursor.execute(query, (esp_address_id, ))

            results = self.cursor.fetchall()

            if results:
                return results
            else:
                return [[0, 0, 0, 0, False]]
            
    def set_on_off(self, token, esp_id, on_off):
        with self.connection:

            esp_address_id = (self.get_esp_address_id_by_token(token, esp_id))[0]
            print(esp_address_id)
            update_query = '''
            UPDATE parameters
            SET on_off = ?
            WHERE esp_address_id = ?;
            '''

            return self.cursor.execute(update_query, (on_off, esp_address_id))