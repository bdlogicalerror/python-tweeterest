from datetime import datetime

import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/tweet-likes', methods=['GET', 'POST', 'DELETE'])
def tweetLikesAction():
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

            if "tweetId" in data:
                cursor.execute("SELECT EXISTS(SELECT id from tweet WHERE id=?)", [data['tweetId']])
                checkTweet = cursor.fetchone()[0]

                if checkTweet == 1:
                    cursor.execute(
                        "SELECT t.tweet_id, u.id, u.username FROM tweet_like t INNER JOIN user u ON t.user_id = u.id "
                        "where t.tweet_id=?",[data['tweetId']])
                    row_headers = [x[0] for x in cursor.description]
                    rv = cursor.fetchall()
                    json_data = []
                    for result in rv:
                        json_data.append(dict(zip(row_headers, result)))

                    return jsonify(json_data), 200
                else:
                    return jsonify({
                        "message": "tweet not found"
                    }), 404
            else:
                return jsonify({
                    "message": "Invalid requests"
                }), 200
        elif request.method == "POST":
            data = request.json

            if len(data.keys()) == 2 and {"loginToken", "tweetId"} <= data.keys():
                tweet_id = data.get("tweetId")
                token = data.get("loginToken")

                if token is not None:
                    cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                    token_valid = cursor.fetchone()[0]

                    if token_valid == 1:
                        cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                        userId = cursor.fetchone()[0]

                        cursor.execute("SELECT EXISTS(SELECT id from tweet WHERE id=?)", [tweet_id])
                        checkTweet = cursor.fetchone()[0]

                        if checkTweet == 1:

                            cursor.execute("SELECT EXISTS(SELECT id from tweet_like WHERE tweet_id=? AND user_id=?)",
                                           [tweet_id, userId])
                            checkTweetAlreadyLiked = cursor.fetchone()[0]
                            if checkTweetAlreadyLiked == 0:
                                created_date = datetime.now()
                                cursor.execute("SET FOREIGN_KEY_CHECKS=OFF;")
                                cursor.execute("INSERT INTO tweet_like(user_id,tweet_id, created_at) VALUES(?,?,?)",
                                               [userId, tweet_id, created_date])
                                cursor.execute("SET FOREIGN_KEY_CHECKS=ON;")

                                conn.commit()
                                return jsonify({}), 201
                            else:
                                return jsonify({
                                    "message": "you already liked this tweet"
                                }), 400
                        else:
                            return jsonify({
                                "message": "tweet not found"
                            }), 404
                    else:
                        return jsonify({
                            "message": "token invalid"
                        }), 403
                else:
                    return jsonify({
                        "message": "loginToken Required"
                    }), 400
            else:
                return jsonify({
                    "message": "invalid request params"
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
                        cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                        userId = cursor.fetchone()[0]

                        cursor.execute("SELECT EXISTS(SELECT id from tweet WHERE id=?)", [tweet_id])
                        checkTweet = cursor.fetchone()[0]

                        if checkTweet == 1:

                            cursor.execute("SELECT EXISTS(SELECT id from tweet_like WHERE tweet_id=? AND user_id=?)",
                                           [tweet_id, userId])
                            checkTweetAlreadyLiked = cursor.fetchone()[0]
                            if checkTweetAlreadyLiked == 1:
                                cursor.execute("SET FOREIGN_KEY_CHECKS=OFF;")
                                cursor.execute("DELETE FROM tweet_like where user_id=? and tweet_id=?",
                                               [userId, tweet_id])
                                cursor.execute("SET FOREIGN_KEY_CHECKS=ON;")

                                conn.commit()
                                return jsonify({}), 204
                            else:
                                return jsonify({
                                    "message": "you did not liked this tweet"
                                }), 400
                        else:
                            return jsonify({
                                "message": "tweet not found"
                            }), 404
                    else:
                        return jsonify({
                            "message": "token invalid"
                        }), 403
                else:
                    return jsonify({
                        "message": "loginToken Required"
                    }), 400
            else:
                return jsonify({
                    "message": "invalid request params"
                }), 400
    else:
        return Response("X-Api-Key not found", mimetype='application/json', status=400)
