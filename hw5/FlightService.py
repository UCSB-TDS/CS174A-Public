import Query
import re

def filter_empty(tokens):
    results = []
    for token in tokens:
        results.append(list(filter(None, token))[0])
    return results

def execute(q, command):
    response = ""
    regex = "\"([^\"]*)\"|(\\S+)"
    tokens = filter_empty(re.findall(regex, command))
    if(len(tokens) == 0):
        response = "Please enter a command"
    elif(tokens[0] == "login"):
        if(len(tokens) == 3):
            username = tokens[1]
            password = tokens[2]
            response = q.transactionLogin(username, password)
        else:
            response = "Error: Please provide a username and password"
    elif(tokens[0] == "create"):
        if(len(tokens) == 4):
            username = tokens[1]
            password = tokens[2]
            initAmount = int(tokens[3])
            response = q.transactionCreateCustomer(username, password, initAmount)
        else:
            response = "Error: Please provide a username, password, and initial amount in the account"
    elif(tokens[0] == "search"):
        if(len(tokens) == 6):
            originCity = tokens[1]
            destCity = tokens[2]
            direct = tokens[3] == "1"
            try:
                day = int(tokens[4])
                count = int(tokens[5])
                response = q.transactionSearch(originCity, destCity, direct, day, count)
            except ValueError:
                response = "Failed to parse integer"
        else:
            response = "Error: Please provide all search parameters <origin_city> <destination_city> <direct> <date> <nb itineraries>"
    elif(tokens[0] == "book"):
        if(len(tokens) == 2):
            itinerarayId = int(tokens[1])
            response = q.transactionBook(itinerarayId)
        else:
            response = "Error: Please provide an itinerary_id"
    elif(tokens[0] == "reservations"):
        response = q.transactionReservation()

    elif(tokens[0] == "pay"):
        if(len(tokens) == 2):
            reservationId = int(tokens[1])
            response = q.transactionPay(reservationId)
        else:
            response = "Error: Please provide a reservation_id"

    elif(tokens[0] == "cancel"):
        if(len(tokens) == 2):
            reservationId = int(tokens[1])
            response = q.transactionCancel(reservationId)
        else:
            response = "Error: Please provide a reservation_id"
    elif(tokens[0] == "quit"):
        q.conn.close()
        response = "Goodbye\n"
    elif(tokens[0] == "SQL"):
        print(q.conn.cursor().execute(tokens[1]).fetchall())
    else:
        response = "Error: unrecognized command '{}'".format(tokens[0])

    return response


def menu(q):
    while(True):
        print(" *** Please enter one of the following commands *** ")
        print("> create|<username>|<password>|<initial amount>")
        print("> login|<username>|<password>")
        print("> search|<origin city>|<destination city>|<direct>|<day of the month>|<num itineraries>")
        print("> book|<itinerary id>")
        print("> pay|<reservation id>")
        print("> reservations")
        print("> cancel|<reservation id>")
        print("> quit")
        command = input("> enter your command here : ")
        response = execute(q, command)
        print(response)
        if(response == "Goodbye\n"):
            break


def main():
    q = Query.Query()
    menu(q)
    q.closeConnection()


if __name__ == "__main__":
    main()