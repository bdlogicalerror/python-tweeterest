import secrets
from datetime import datetime

import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/tweets', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def tweetsAction():
    conn = mariadb.connect(
        user=dbcreds.user,
        password=dbcreds.password,
        host=dbcreds.host,
        port=dbcreds.port,
        database=dbcreds.database
    )
    cursor = conn.cursor()
    if xApiToken().checkHasToken():
        if request.method == "GET":
            data = request.json
            if "userId" in data:
                userID = data.get("userId")
                cursor.execute("SELECT EXISTS(SELECT * FROM user WHERE id=?)", [userID])
                checkUser = cursor.fetchone()[0]
                if checkUser == 1:
                    cursor.execute("SELECT t.id, user_id, username, content, created_at, u.imageurl, t.imageurl FROM tweet t \
                                                    INNER JOIN user u ON t.user_id = u.id")
                    row_headers = [x[0] for x in cursor.description]
                    rv = cursor.fetchall()
                    json_data = []
                    for result in rv:
                        json_data.append(dict(zip(row_headers, result)))
                    return jsonify(json_data), 200
                else:
                    return jsonify({
                        'message': "User not found"
                    }), 404
            else:
                return jsonify({
                    'message': "Invalid Request"
                }), 400
        elif request.method == "POST":
            data = request.json

            if len(data.keys()) == 2:
                if {"loginToken", "content"} <= data.keys():
                    tweet = data
                else:
                    return jsonify({
                        'message': "Incorrect keys submitted.",
                    }), 400
            elif len(data.keys()) == 3:
                if {"loginToken", "content", "imageUrl"} <= data.keys():
                    tweet = data
                else:
                    return jsonify({
                        'message': "Incorrect keys submitted.",
                    }), 400
            else:
                return jsonify({
                    'message': "Incorrect keys submitted.",
                }), 400

            token = tweet["loginToken"]
            if token is not None:
                cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                checkToken = cursor.fetchone()[0]

                if checkToken == 0:
                    return jsonify({
                        'message': "Not a valid login token",
                    }), 400
            else:
                return jsonify({
                    'message': "Invalid login token",
                }), 400

            created_date = datetime.now()

            cursor.execute("SELECT user_id from user_session WHERE login_token=?", [tweet["loginToken"]])
            user_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO tweet(user_id, content, created_at) VALUES(?,?,?)", \
                           [user_id, tweet["content"], created_date])
            conn.commit()

            if "imageUrl" in tweet:
                cursor.execute("UPDATE tweet SET imageurl=? WHERE user_id=?", [tweet["imageUrl"], user_id])
                conn.commit()

            cursor.execute("SELECT t.id, u.id, username, u.imageUrl, content, created_at, t.imageurl FROM tweet t \
                                        INNER JOIN user u ON t.user_id = u.id WHERE t.user_id=? ORDER BY t.id DESC LIMIT 1",
                           [user_id])
            ret_data = cursor.fetchone()
            print(ret_data)

            # create response data obj
            resp = {
                "tweetId": ret_data[0],
                "userId": ret_data[1],
                "username": ret_data[2],
                "userImageUrl": ret_data[3],
                "content": ret_data[4],
                "createdAt": ret_data[5],
                "imageUrl": ret_data[6]
            }
            return jsonify(resp), 200
        elif request.method == "PATCH":
            data = request.json
            if len(data.keys()) == 3 or len(data.keys()) == 4:
                if {"loginToken", "tweetId", "content"} <= data.keys() or {"loginToken", "tweetId", "content",
                                                                           "imageUrl"} <= data.keys():

                    token = data.get("loginToken")
                    tweet_id = data.get("tweetId")
                    if token is not None:
                        cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                        token_valid = cursor.fetchone()[0]

                        if token_valid == 1:
                            cursor.execute("SELECT EXISTS(SELECT id FROM tweet WHERE id=?)", [tweet_id])
                            tweetvalid = cursor.fetchone()[0]

                            if tweetvalid == 1:
                                cursor.execute("SELECT EXISTS (SELECT t.id FROM user_session u INNER JOIN \
                                                                       tweet t ON u.user_id = t.user_id WHERE login_token=? AND t.id=?)",
                                               [token, tweet_id])
                                userHasPermission = cursor.fetchone()[0]

                                if userHasPermission == 0:
                                    return jsonify({
                                        "message": "Unauthorized to update this tweet"
                                    }), 401

                                cursor.execute("UPDATE tweet SET content=? WHERE id=?", [data["content"], tweet_id])
                                conn.commit()

                                if "imageUrl" in data:
                                    cursor.execute("UPDATE tweet SET tweet_image_url=? WHERE id=?",
                                                   [data["imageUrl"], tweet_id])
                                    conn.commit()

                                cursor.execute("SELECT id, content, imageurl FROM tweet WHERE id=?", [tweet_id])
                                updated_t = cursor.fetchone()

                                resp = {
                                    "tweetId": updated_t[0],
                                    "content": updated_t[1],
                                    "imageUrl": updated_t[2]
                                }
                                return jsonify(resp), 200
                            else:
                                return jsonify({
                                    'message': "Invalid tweet id"
                                }), 403
                        else:
                            return jsonify({
                                'message': "Invalid login token"
                            }), 403
                    return jsonify({
                        'method': request.method
                    })
                else:
                    return jsonify({
                        'message': "Invalid Request Key"
                    }), 400
            else:
                return jsonify({
                    'message': "Invalid Request"
                }), 400
        elif request.method == "DELETE":
            data = request.json

            if len(data.keys()) == 2 and {"loginToken", "tweetId"} <= data.keys():
                tweet_id = data.get("tweetId")
                token = data.get("loginToken")

                if token is not None:
                    cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                    token_valid = cursor.fetchone()[0]

                    if token_valid == 1:
                        cursor.execute("SELECT EXISTS(SELECT id from tweet WHERE id=?)", [tweet_id])
                        checkTweet = cursor.fetchone()[0]

                        if checkTweet == 1:
                            cursor.execute("SELECT EXISTS (SELECT t.id FROM user_session u INNER JOIN \
                                                       tweet t ON u.user_id = t.user_id WHERE login_token=? AND t.id=?)",
                                           [token, tweet_id])
                            userHasTweet = cursor.fetchone()[0]

                            if userHasTweet == 1:
                                cursor.execute("DELETE FROM tweet WHERE id=?", [tweet_id])
                                conn.commit()
                                return jsonify({}), 204

                            else:
                                return jsonify({
                                    "message": "you are not permitted to delete this tweet"
                                }), 403
                        else:
                            return jsonify({
                                "message": "Invalid tweet id"
                            }), 400
                    else:
                        return jsonify({
                            "message": "Invalid login token"
                        }), 400
                else:
                    return jsonify({
                        "message": "login token required"
                    }), 400
            else:
                return jsonify({
                    "message": "invalid request"
                }), 400
    else:
        return Response("X-Api-Key not found", mimetype='application/json', status=400)
