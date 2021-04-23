from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")

db = client.BankAPI

users = db["Users"]

def userExists(username):
    if users.find({"username": username}).count() == 0:
        return False
    return True

def verifyPassword(username, password):
    if not userExists(username):
        False

    hashed_pw = users.find({
        "username": username
    })[0]["password"]

    if bcrypt.checkpw(password.encode("utf8"), hashed_pw) == True:
        return True
    return False    

def countTokens(username):
    num_tokens = users.find({
        "username": username
    })[0]["tokens"]
    return num_tokens

def createJson(status, msg):
    retJson = {
        "status": status,
        "msg": msg
    }
    return jsonify(retJson)

def cashWithUser(username):
    cash = users.find({
        "username": username
    })[0]["own"]
    return cash

def debtWithUser(username):
    debt = users.find({
        "username": username
    })[0]["debt"]
    return debt

def verifyCredentials(username, password):
    if not userExists(username):
        return createJson(301, "username not found"), True

    hashed_pw = users.find({
        "username": username
    })[0]["password"]

    if verifyPassword(username, password) != True:
        return createJson(302, "wrong password"), True
    else:
        return {}, False  

def updateAccount(username, balance):
    users.update({
        "username": username
    }, {
        "$set": {
            "own": balance
        }
    })

def updateDebt(username, balance):
    users.update({
        "username": username
    }, {
        "$set": {
            "debt": balance
        }
    })    

class Register(Resource):
    def post(self):

        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if userExists(username):
            return createJson(301, "username unavailable")

        hashed_pw = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

        users.insert({
            "username": username,
            "password": hashed_pw,
            "own": 0,
            "debt": 0
        })

        return createJson(200, "success")

class Add(Resource):
    def post(self):

        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return retJson

        if amount<=0:
            return createJson(304, "invalid amount")

        cash = cashWithUser(username)

        amount -= 1

        bank_cash = cashWithUser("BANK")
        updateAccount("BANK", bank_cash+1)
        updateAccount(username, cash+amount)

        return createJson(200, "success")

class Transfer(Resource):
    def post(self):

        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        recipient = postedData["recipient"]
        amount = postedData["amount"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return retJson

        cash_from = cashWithUser(username)
        cash_to = cashWithUser(recipient)
        bank_cash = cashWithUser("BANK")

        if cash_from<=amount:
            return createJson(304, "not enough money")

        if not userExists(recipient):
            return createJson(301, "recipent does not exist")

        updateAccount("BANK", bank_cash+1)
        updateAccount(recipient, cash_to+amount)
        updateAccount(username, cash_from-amount-1)

        return createJson(200, "success")

class Balance(Resource):
    def post(self):

        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return retJson

        retJson = users.find({
            "username": username
        }, {
            "password": 0,
            "_id": 0
        })[0]

        return jsonify(retJson)

class TakeLoan(Resource):
    def post(self):

        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return retJson

        cash = cashWithUser(username)
        debt = debtWithUser(username)

        updateAccount(username, cash+amount)
        updateDebt(username, debt+amount)

        return createJson(200, "success")

class PayLoan(Resource):
    def post(self):

        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return retJson

        cash = cashWithUser(username)
        debt = debtWithUser(username)

        if cash<amount:
            return cashWithUser(303, "not enough money")

        updateAccount(username, cash-amount)
        updateDebt(username, debt-amount)

        return createJson(200, "success")

api.add_resource(Register, "/register")
api.add_resource(Add, "/add")
api.add_resource(Transfer, "/transfer")
api.add_resource(Balance, "/balance")
api.add_resource(TakeLoan, "/takeloan")
api.add_resource(PayLoan, "/payloan")

if __name__ == "__main__":
    app.run(host="0.0.0.0")      