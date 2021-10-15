import secrets

import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/follows', methods=['GET', 'POST', 'DELETE'])
def followAction():
    conn = mariadb.connect(
        user=dbcreds.user,
        password=dbcreds.password,
        host=dbcreds.host,
        port=dbcreds.port,
        database=dbcreds.database
    )
    cursor = conn.cursor()
    if xApiToken().checkHasToken():
        if request.method == 'GET':
            data = request.args
            print(data['userId'])

            if "userId" in data:
                cursor.execute("SELECT EXISTS(SELECT * FROM user WHERE id=?)", [data['userId']])
                checkUser = cursor.fetchone()[0]

                # handles bool response
                if checkUser == 1:
                    cursor.execute("SELECT id as userId, email, username, bio, birthdate, imageurl, bannerurl \
                                                            FROM user u INNER JOIN follow f ON u.id = f.followed WHERE f.follower=?",
                                   [data['userId']])

                    row_headers = [x[0] for x in cursor.description]
                    rv = cursor.fetchall()
                    json_data = []
                    for result in rv:
                        json_data.append(dict(zip(row_headers, result)))

                    return jsonify(json_data)
                else:
                    return jsonify({
                        'status': "error",
                        "message": "user not found"
                    }), 404
            else:
                return jsonify({
                    'status': "error",
                    "message": "userId not found"
                }), 400
        elif request.method == 'POST':
            data = request.json
            if len(data.keys()) == 2:
                if {"loginToken", "followId"} <= data.keys():
                    loginToken = data.get("loginToken")
                    followId = data.get("followId")

                    if loginToken is not None:
                        cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)",
                                       [loginToken])
                        checkToken = cursor.fetchone()[0]

                        if checkToken == 1:
                            cursor.execute("SELECT EXISTS(SELECT id from user WHERE id=?)", [followId])
                            check_follow_id = cursor.fetchone()[0]

                            if check_follow_id == 1:
                                cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [loginToken])
                                user_id = cursor.fetchone()[0]

                                if user_id == int(followId):
                                    return jsonify({
                                        "message": "User cannot follow themselves"
                                    }), 400

                                cursor.execute(
                                    "SELECT EXISTS(SELECT followed FROM follow WHERE followed=? AND follower=?)",
                                    [followId, user_id])
                                check_follow_exists = cursor.fetchone()[0]

                                if check_follow_exists == 0:
                                    cursor.execute("INSERT INTO follow(follower, followed) VALUES(?,?)",
                                                   [user_id, followId])
                                    conn.commit()
                                    return jsonify({}), 204

                                else:
                                    return jsonify({"message": "This user is already being followed"}), 400
                            else:
                                return jsonify({"message": "No user with that id"}), 400

                        else:
                            return jsonify({"message": "Invalid login token"}), 400
                    else:
                        return jsonify({"message": "Invalid login token"}), 400
                else:
                    return jsonify({
                        'message': "invalid request parameter"
                    })
        elif request.method == 'DELETE':
            data = request.json
            if len(data.keys()) == 2:
                if {"loginToken", "followId"} <= data.keys():
                    loginToken = data.get("loginToken")
                    followId = data.get("followId")

                    if loginToken is not None:
                        cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)",
                                       [loginToken])
                        checkToken = cursor.fetchone()[0]

                        if checkToken == 1:
                            cursor.execute("SELECT EXISTS(SELECT id from user WHERE id=?)", [followId])
                            check_follow_id = cursor.fetchone()[0]

                            if check_follow_id == 1:
                                cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [loginToken])
                                user_id = cursor.fetchone()[0]

                                if user_id == int(followId):
                                    return jsonify({
                                        "message": "User cannot unfollow themselves"
                                    }), 400

                                cursor.execute(
                                    "SELECT EXISTS(SELECT followed FROM follow WHERE followed=? AND follower=?)",
                                    [followId, user_id])
                                check_follow_exists = cursor.fetchone()[0]

                                if check_follow_exists == 1:
                                    cursor.execute("DELETE FROM follow WHERE follower=? AND followed=?",
                                                   [user_id, followId])
                                    conn.commit()
                                    return jsonify({}), 204

                                else:
                                    return jsonify({"message": "This user is not followed"}), 400
                            else:
                                return jsonify({"message": "No user with that id"}), 400

                        else:
                            return jsonify({"message": "Invalid login token"}), 400
                    else:
                        return jsonify({"message": "Invalid login token"}), 400
                else:
                    return jsonify({
                        'message': "invalid request parameter"
                    })
        else:
            return jsonify({
                'message': "invalid request"
            }), 500
    else:
        return Response("X-Api-Key not found", mimetype='application/json', status=400)
