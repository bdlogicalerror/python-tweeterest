import secrets

import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/login', methods=['POST', 'DELETE'])
def loginAction():
    conn = mariadb.connect(
        user=dbcreds.user,
        password=dbcreds.password,
        host=dbcreds.host,
        port=dbcreds.port,
        database=dbcreds.database
    )
    cursor = conn.cursor()
    if xApiToken().checkHasToken():
        if request.method == 'POST':
            data = request.json
            if len(data.keys()) == 2:
                if {"email", "password"} <= data.keys():
                    email = data.get("email")
                    password = data.get("password")

                    cursor.execute("SELECT EXISTS(SELECT email FROM user WHERE email=?)", [email])
                    email_valid = cursor.fetchone()[0]

                    if email_valid == 1:
                        cursor.execute("SELECT id as userId,email,username,bio,birthdate,imageUrl,bannerUrl FROM user "
                                       "WHERE email=? AND password=?", [email, password])
                        # serialize results into JSON
                        row_headers = [x[0] for x in cursor.description]
                        rv = cursor.fetchall()
                        if len(rv) > 0:
                            json_data = []
                            for result in rv:
                                json_data.append(dict(zip(row_headers, result)))

                            res = json_data[0]

                            login_token = secrets.token_hex(16)

                            res['loginToken'] = login_token

                            cursor.execute("INSERT INTO user_session(user_id, login_token) VALUES(?,?)",
                                           [res['userId'], login_token])
                            conn.commit()

                            return jsonify(res), 200
                        else:
                            return jsonify({
                                'status': 'error',
                                'message': "email not found"
                            }), 400
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': "email/username not found"
                        }), 400
                elif {"username", "password"} <= data.keys():
                    username = data.get("username")
                    password = data.get("password")
                    cursor.execute("SELECT EXISTS(SELECT email FROM user WHERE username=?)", [username])
                    username_valid = cursor.fetchone()[0]

                    if username_valid == 1:
                        cursor.execute("SELECT id as userId,email,username,bio,birthdate,imageUrl,bannerUrl FROM user "
                                       "WHERE username=? AND password=?", [username, password])
                        # serialize results into JSON
                        row_headers = [x[0] for x in cursor.description]
                        rv = cursor.fetchall()
                        if len(rv) > 0:
                            json_data = []
                            for result in rv:
                                json_data.append(dict(zip(row_headers, result)))

                            res = json_data[0]

                            login_token = secrets.token_hex(16)

                            res['loginToken'] = login_token

                            cursor.execute("INSERT INTO user_session(user_id, login_token) VALUES(?,?)",
                                           [res['userId'], login_token])
                            conn.commit()

                            return jsonify(res), 201
                        else:
                            return jsonify({
                                'status': 'error',
                                'message': "username not found"
                            }), 400
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': "username not found"
                        }), 400
                else:
                    if "username" not in data and "email" not in data:
                        return jsonify({
                            'status': 'error',
                            'message': "email/username required"
                        }), 400
                    elif "password" not in data:
                        return jsonify({
                            'status': 'error',
                            'message': "Password required"
                        }), 400
            else:
                return jsonify({
                    'status': 'error',
                    'message': "Request data invalid"
                })
        elif request.method == "DELETE":
            data = request.json
            if "loginToken" in data:
                cursor.execute("SELECT EXISTS(SELECT id FROM user_session WHERE login_token=?)", [data['loginToken']])
                token_valid = cursor.fetchone()[0]
                print(token_valid)
                if token_valid == 1:
                    cursor.execute("DELETE FROM user_session WHERE login_token=?", [data['loginToken']])
                    conn.commit()
                    return jsonify({}), 204
        else:
            return jsonify({
                "message": request.method + " Method not support"
            })
    else:
        return Response("X-Api-Key not found", mimetype='application/json', status=400)