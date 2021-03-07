import sqlite3
import operator
import subprocess
import os
import csv
import apsw
import time
import threading

DB_NAME = "example.db"

# A class to store flight information.
class Flight:
    def __init__(self, fid = -1, dayOfMonth=0, carrierId=0, flightNum=0, originCity="", destCity="", time=0, capacity=0, price=0):
        self.fid = fid
        self.dayOfMonth = dayOfMonth
        self.carrierId = carrierId
        self.flightNum = flightNum
        self.originCity = originCity
        self.destCity = destCity
        self.time = time
        self.capacity = capacity
        self.price = price
    def toString(self):
        return "ID: {} Day: {} Carrier: {} Number: {} Origin: {} Dest: {} Duration: {} Capacity: {} Price: {}\n".format(
                self.fid, self.dayOfMonth, self.carrierId, self.flightNum, self.originCity, self.destCity,self.time, self.capacity, self.price)


class Itinerary:
    #one-hop flight
    def __init__(self,  time ,flight1, flight2=Flight()):# the second one could be empty flight
        self.flights=[]
        self.flights.append(flight1)
        self.flights.append(flight2)
        self.time = time

    
    def itineraryPrice(self):
        price = 0
        for f in self.flights:
            price += f.price
        return price

    def numFlights(self):
        if(self.flights[1].fid == -1):
            return 1
        else:
            return 2
    

class Query:
    CREATE_CUSTOMER_SQL = "INSERT INTO Customers VALUES('{}', '{}', {})"


    CHECK_FLIGHT_DAY = "SELECT * FROM Reservations r, Flights f WHERE r.username = '{}' AND f.day_of_month = {} AND r.fid1 = f.fid"
    CHECK_FLIGHT_CAPACITY = "SELECT capacity FROM Flights WHERE fid = {}"
    CHECK_BOOKED_SEATS = "SELECT COUNT(*) AS cnt FROM Reservations WHERE fid1 = {} or fid2 = {}"
    CLEAR_DB_SQL1 = "DELETE FROM Reservations;"
    CLEAR_DB_SQL2 = "DELETE FROM Customers;"
    CLEAR_DB_SQL3 = "UPDATE ReservationsId SET rid = 1;"


    username = None
    lastItineraries = []

    def __init__(self):
        self.db_name = DB_NAME
        self.conn = apsw.Connection(self.db_name, statementcachesize=0)
        self.conn.setbusytimeout(5000)

    def startConnection(self):
        self.conn = apsw.Connection(self.db_name, statementcachesize=0)


    def closeConnection(self):
        self.conn.close()


    '''
    * Clear the data in any custom tables created. and reload the Carriers, Flights, Weekdays and Months tables.
    * 
    * WARNING! Do not drop any tables and do not clear the flights table.
    '''
    def clearTables(self):
        try:
            os.remove(DB_NAME)
            open(DB_NAME, 'w').close()
            os.system("chmod 777 {}".format(DB_NAME))
            #remove old db file
            # TODO use sqlite3 example.db < create_tables.sql to reconstruct the db file. This can save many lines of code.
            # I have to reconstruct the db before each test
            self.conn = apsw.Connection(self.db_name, statementcachesize=0)

            self.conn.cursor().execute("PRAGMA foreign_keys=ON;")
            self.conn.cursor().execute(" PRAGMA serializable = true;")
            self.conn.cursor().execute("CREATE TABLE Carriers (cid VARCHAR(7) PRIMARY KEY, name VARCHAR(83))")
            self.conn.cursor().execute("""   
                    CREATE TABLE Months (
                        mid INT PRIMARY KEY,
                        month VARCHAR(9)
                    );""")

            self.conn.cursor().execute("""       
                    CREATE TABLE Weekdays(
                        did INT PRIMARY KEY,
                        day_of_week VARCHAR(9)
                    );""")
            self.conn.cursor().execute("""      
                    CREATE TABLE Flights (
                        fid INT PRIMARY KEY, 
                        month_id INT,        -- 1-12
                        day_of_month INT,    -- 1-31 
                        day_of_week_id INT,  -- 1-7, 1 = Monday, 2 = Tuesday, etc
                        carrier_id VARCHAR(7), 
                        flight_num INT,
                        origin_city VARCHAR(34), 
                        origin_state VARCHAR(47), 
                        dest_city VARCHAR(34), 
                        dest_state VARCHAR(46), 
                        departure_delay INT, -- in mins
                        taxi_out INT,        -- in mins
                        arrival_delay INT,   -- in mins
                        canceled INT,        -- 1 means canceled
                        actual_time INT,     -- in mins
                        distance INT,        -- in miles
                        capacity INT, 
                        price INT,           -- in $
                        FOREIGN KEY (carrier_id) REFERENCES Carriers(cid),
                        FOREIGN KEY (month_id) REFERENCES Months(mid),
                        FOREIGN KEY (day_of_week_id) REFERENCES Weekdays(did)
                    );""")
            self.conn.cursor().execute("""        
                    CREATE TABLE Customers(
                        username VARCHAR(256),
                        password VARCHAR(256),
                        balance INT,
                        PRIMARY KEY (username)
                    );""")
            self.conn.cursor().execute("""      
                    CREATE TABLE Itineraries(
                        direct INT, -- 1 or 0 stands for direct or one-hop flights
                        fid1 INT,
                        fid2 INT -- -1 means that this is a direct flight and has no second flight
                    );""")
            self.conn.cursor().execute("""      
                    CREATE TABLE Reservations(
                        rid INT,
                        price INT,
                        fid1 INT,
                        fid2 INT,
                        paid INT,
                        canceled INT,
                        username VARCHAR(256),
                        day_of_month INT,
                        PRIMARY KEY (rid)
                    );""")
            self.conn.cursor().execute("""      
                    CREATE TABLE ReservationsId(
                        rid INT
                    );""")

            self.conn.cursor().execute("INSERT INTO ReservationsId VALUES (1);")

            # reload db file for next tests

            with open("carriers.csv") as carriers:
                carriers_data = csv.reader(carriers)
                self.conn.cursor().executemany("INSERT INTO Carriers VALUES (?, ?)", carriers_data)

            with open("months.csv") as months:
                months_data = csv.reader(months)
                self.conn.cursor().executemany("INSERT INTO Months VALUES (?, ?)", months_data)

            with open("weekdays.csv") as weekdays:
                weekdays_data = csv.reader(weekdays)
                self.conn.cursor().executemany("INSERT INTO Weekdays VALUES (?, ?)", weekdays_data)
            
            #conn.cursor().executemany() is too slow to load largecsv files... so i use the command line instead for flights.csv
            subprocess.run(['sqlite3',
                         "example.db",
                         '-cmd',
                         '.mode csv',
                         '.import flights-small.csv Flights'])
            
        except sqlite3.Error:
            print("clear table SQL execution meets Error")


    '''
   * Implement the create user function.
   *
   * @param username   new user's username. User names are unique the system.
   * @param password   new user's password.
   * @param initAmount initial amount to deposit into the user's account, should be >= 0 (failure
   *                   otherwise).
   *
   * @return either "Created user `username`\n" or "Failed to create user\n" if failed.
    '''

    def transactionCreateCustomer(self, username, password, initAmount):
        #this is an example function.
        response = ""
        try:
            if(initAmount >= 0):
                self.conn.cursor().execute(self.CREATE_CUSTOMER_SQL.format(username, password, initAmount))
                response = "Created user {}\n".format(username)
            else:
                response = "Failed to create user\n"
        except apsw.ConstraintError:
            #we already have this customer. we can not create it again
            #print("create user meets apsw.ConstraintError")
            response = "Failed to create user\n"
        return response

    '''
   * Takes a user's username and password and attempts to log the user in.
   *
   * @param username user's username
   * @param password user's password
   *
   * @return If someone has already logged in, then return "User already logged in\n" For all other
   *         errors, return "Login failed\n". Otherwise, return "Logged in as [username]\n".
    '''

    def transactionLogin(self, username, password):
        #TODO your code here
        response = ""
        
        return response 





    '''
   * Implement the search function.
   *
   * Searches for flights from the given origin city to the given destination city, on the given day
   * of the month. If {@code directFlight} is true, it only searches for direct flights, otherwise
   * is searches for direct flights and flights with two "hops." Only searches for up to the number
   * of itineraries given by {@code numberOfItineraries}.
   *
   * The results are sorted based on total flight time.
   *
   * @param originCity
   * @param destinationCity
   * @param directFlight        if true, then only search for direct flights, otherwise include
   *                            indirect flights as well
   * @param dayOfMonth
   * @param numberOfItineraries number of itineraries to return
   *
   * @return If no itineraries were found, return "No flights match your selection\n". If an error
   *         occurs, then return "Failed to search\n".
   *
   *         Otherwise, the sorted itineraries printed in the following format:
   *
   *         Itinerary [itinerary number]: [number of flights] flight(s), [total flight time]
   *         minutes\n [first flight in itinerary]\n ... [last flight in itinerary]\n
   *
   *         Each flight should be printed using the same format as in the {@code Flight} class.
   *         Itinerary numbers in each search should always start from 0 and increase by 1.
   *
   * @see Flight#toString()
   '''

    def transactionSearch(self, originCity, destCity, directFlight, dayOfMonth, numberOfItineraries):
        #TODO your code here
        response = ""

        return response
                    



    '''
   * Implements the book itinerary function.
   *
   * @param itineraryId ID of the itinerary to book. This must be one that is returned by search in
   *                    the current session.
   *
   * @return If the user is not logged in, then return "Cannot book reservations, not logged in\n".
   *         If the user is trying to book an itinerary with an invalid ID or without having done a
   *         search, then return "No such itinerary {@code itineraryId}\n". If the user already has
   *         a reservation on the same day as the one that they are trying to book now, then return
   *         "You cannot book two flights in the same day\n". For all other errors, return "Booking
   *         failed\n".
   *
   *         And if booking succeeded, return "Booked flight(s), reservation ID: [reservationId]\n"
   *         where reservationId is a unique number in the reservation system that starts from 1 and
   *         increments by 1 each time a successful reservation is made by any user in the system.
    '''
    def transactionBook(self, itineraryId):
        # TODO your code here
        response = ""
        return response




    '''
   * Implements the pay function.
   *
   * @param reservationId the reservation to pay for.
   *
   * @return If no user has logged in, then return "Cannot pay, not logged in\n" If the reservation
   *         is not found / not under the logged in user's name, then return "Cannot find unpaid
   *         reservation [reservationId] under user: [username]\n" If the user does not have enough
   *         money in their account, then return "User has only [balance] in account but itinerary
   *         costs [cost]\n" For all other errors, return "Failed to pay for reservation
   *         [reservationId]\n"
   *
   *         If successful, return "Paid reservation: [reservationId] remaining balance:
   *         [balance]\n" where [balance] is the remaining balance in the user's account.
    '''
    def transactionPay(self, reservationId):
        #TODO your code here
        response = ""
        return response
                
    '''
   * Implements the reservations function.
   *
   * @return If no user has logged in, then return "Cannot view reservations, not logged in\n" If
   *         the user has no reservations, then return "No reservations found\n" For all other
   *         errors, return "Failed to retrieve reservations\n"
   *
   *         Otherwise return the reservations in the following format:
   *
   *         Reservation [reservation ID] paid: [true or false]:\n [flight 1 under the
   *         reservation]\n [flight 2 under the reservation]\n Reservation [reservation ID] paid:
   *         [true or false]:\n [flight 1 under the reservation]\n [flight 2 under the
   *         reservation]\n ...
   *
   *         Each flight should be printed using the same format as in the {@code Flight} class.
   *
   * @see Flight#toString()
    '''
    def transactionReservation(self):
        #TODO your code here
        response = ""
        
        return response

    '''
   * Implements the cancel operation.
   *
   * @param reservationId the reservation ID to cancel
   *
   * @return If no user has logged in, then return "Cannot cancel reservations, not logged in\n" For
   *         all other errors, return "Failed to cancel reservation [reservationId]\n"
   *
   *         If successful, return "Canceled reservation [reservationId]\n"
   *
   *         Even though a reservation has been canceled, its ID should not be reused by the system.
    '''
    def transactionCancel(self, reservationId):
        #TODO your code here
        response = ""
        
        return response


    '''
    Example utility function that uses prepared statements
    '''
    def checkFlightCapacity(self, fid):
        #a helper function that you will use to implement previous functions
        result = self.conn.cursor().execute(self.CHECK_FLIGHT_CAPACITY.format(fid)).fetchone()
        if(result != None):
            return result[0]
        else:
            return 0

    def checkFlightIsFull(self, fid):
        #a helper function that you will use to implement previous functions
        
        capacity = self.conn.cursor().execute(self.CHECK_FLIGHT_CAPACITY.format(fid)).fetchone()[0]
        booked_seats = self.conn.cursor().execute(self.CHECK_BOOKED_SEATS.format(fid, fid)).fetchone()[0]
        #print("Checking booked/capacity {}/{}".format(booked_seats, capacity))
        return booked_seats >= capacity


    def checkFlightSameDay(self, username, dayOfMonth):
        result = self.conn.cursor().execute(self.CHECK_FLIGHT_DAY.format(username, dayOfMonth)).fetchall()
        if(len(result) == 0):
            #have not found there are multiple flights on the specific day by current user.
            return False
        else:
            return True


