# CS174A Homework : Database Application and Transaction Management

**Objectives:**
To gain experience with database application development and transaction management.
To learn how to use SQLite from within python.

**Assignment tools:**
* [SQLite](https://www.sqlite.org/index.html) through [Python apsw library](https://rogerbinns.github.io/apsw/index.html)
* starter code files

Instructions assume you are on the Linux or MacOS platform.

**Assigned date:** Feb 25th, 2021

** Due date:**

Thursday, March 9, 2021, at 11pm PDT. Turn in your solution to GradeScope



**WARNING:**
This homework requires writing a non-trivial amount of python code (our solution is about 500 lines) and test cases. It should take SIGNIFICANTLY more time than your previous CS174A assignments.
START EARLY!!!


## Assignment Details

**Read through this whole section before starting this project.** There is a lot of valuable information here, and some implementation details depend on others.

Congratulations, you are opening your own flight booking service!

In this homework, you have two main tasks:
* Design a database of your customers and the flights they book
* Complete a working prototype of your flight booking application that connects to the SQLite database then allows customers to use a CLI to search, book, cancel, etc. flights

You will also be writing a few test cases and explaining your design in a short writeup.
We have already provided code for a UI (`FlightService.py`) and partial backend (`Query.py`).
For this homework, your task is to implement the rest of the backend.
In real life, you would develop a web-based interface instead of a CLI, but we use a CLI to simplify this homework.


*** Please enter one of the following commands ***
> create <username> <password> <initial amount>
> login <username> <password>
> search <origin city> <destination city> <direct> <day> <num itineraries>
> book <itinerary id>
> pay <reservation id>
> reservations
> cancel <reservation id>
> quit
```

#### Data Model

The flight service system consists of the following logical entities.
These entities are *not necessarily database tables*.
We have provided a database scheme for you which is available in `create_tables.sql`. You can check the schema design.

- **Flights / Carriers / Months / Weekdays**: modeled the same way as previous homework. For this application, we have very limited functionality so you shouldn't need to modify the schema from HW2 nor add any new table to reason about the data.

- **Users**: A user has a username (`varchar`), password (`varbinary`), and balance (`int`) in their account.
  All usernames should be unique in the system. Each user can have any number of reservations.
  Usernames are case insensitive (this is the default for SQLite).
  You can assume that all usernames and passwords have at most 20 characters.
  For implementation simplicity, we do not encrypt the password, which is quite `dangerous` in real-world applications.

- **Itineraries**: An itinerary is either a direct flight (consisting of one flight: origin --> destination) or
  a one-hop flight (consisting of two flights: origin --> stopover city, stopover city --> destination). Itineraries are returned by the search command.

- **Reservations**: A booking for an itinerary, which may consist of one (direct) or two (one-hop) flights.
  Each reservation can either be paid or unpaid, cancelled or not, and has a unique ID.

- **ReservationsId**: Used for obtaining atomically increasing reservation ID.


#### Requirements
The following are the functional specifications for the flight service system, to be implemented in `Query.py`
(see the method stubs in the starter code for full specification as to what error message to return, etc):

- **create** takes in a new username, password, and initial account balance as input. It creates a new user account with the initial balance.
  It should return an error if negative, or if the username already exists. Usernames are checked case-insensitively.
  You can assume that all usernames and passwords have at most 20 characters.
  For implementations simplicity, you do not need to encrypt and salt the password, but remember that in real world applications, you should always consider about protecting the secret data of your customers.


- **login** takes in a username and password, and checks that the user exists in the database and that the password matches. To compute the hash, adapt the above code.
  Within a single session (that is, a single instance of your program), only one user should be logged in. You can track this via a local variable in your program.
  If a second login attempt is made, please return "User already logged in".
  Across multiple sessions (that is, if you run your program multiple times), the same user is allowed to be logged in.
  This means that you do not need to track a user's login status inside the database.

- **search** takes as input an origin city (string), a destination city (string), a flag for only direct flights or not (0 or 1), the date (int), and the maximum number of itineraries to be returned (int).
  For the date, we only need the day of the month, since our dataset comes from July 2015. Return only flights that are not canceled, ignoring the capacity and number of seats available.
  If the user requests n itineraries to be returned, there are a number of possibilities:
    * direct=1: return up to n direct itineraries
    * direct=0: return up to n direct itineraries. If there are only k direct itineraries (where k < n), then return the k direct itineraries and up to (n-k) of the shortest indirect itineraries with the flight times. For one-hop flights, different carriers can be used for the flights. For the purpose of this assignment, an indirect itinerary means the first and second flight only must be on the same date (i.e., if flight 1 runs on the 3rd day of July, flight 2 runs on the 4th day of July, then you can't put these two flights in the same itinerary as they are not on the same day).

  <br />Sort your results. In all cases, the returned results should be primarily sorted on total actual_time (ascending). If a tie occurs, break that tie by the fid value. Use the first then the second fid for tie-breaking.

    Below is an example of a single direct flight from Seattle to Boston. Actual itinerary numbers might differ, notice that only the day is printed out since we assume all flights happen in July 2015:

    ```
    Itinerary 0: 1 flight(s), 297 minutes
    ID: 60454 Day: 1 Carrier: AS Number: 24 Origin: Seattle WA Dest: Boston MA Duration: 297 Capacity: 14 Price: 140
    ```

    Below is an example of two indirect flights from Seattle to Boston:

    ```
    Itinerary 0: 2 flight(s), 317 minutes
    ID: 704749 Day: 10 Carrier: AS Number: 16 Origin: Seattle WA Dest: Orlando FL Duration: 159 Capacity: 10 Price: 494
    ID: 726309 Day: 10 Carrier: B6 Number: 152 Origin: Orlando FL Dest: Boston MA Duration: 158 Capacity: 0 Price: 104
    Itinerary 1: 2 flight(s), 317 minutes
    ID: 704749 Day: 10 Carrier: AS Number: 16 Origin: Seattle WA Dest: Orlando FL Duration: 159 Capacity: 10 Price: 494
    ID: 726464 Day: 10 Carrier: B6 Number: 452 Origin: Orlando FL Dest: Boston MA Duration: 158 Capacity: 7 Price: 760
    ```

    Note that for one-hop flights, the results are printed in the order of the itinerary, starting from the flight leaving the origin and ending with the flight arriving at the destination.

    The returned itineraries should start from 0 and increase by 1 up to n as shown above. If no itineraries match the search query, the system should return an informative error message. See `Query.py` for the actual text.

    The user need not be logged in to search for flights.

    All flights in an indirect itinerary should be under the same itinerary ID. In other words, the user should only need to book once with the itinerary ID for direct or indirect trips.


- **book** lets a user book an itinerary by providing the itinerary number as returned by a previous search.
  The user must be logged in to book an itinerary, and must enter a valid itinerary id that was returned in the last search that was performed *within the same login session*.
  Make sure you make the corresponding changes to the tables in case of a successful booking. Once the user logs out (by quitting the application),
  logs in (if they previously were not logged in), or performs another search within the same login session,
  then all previously returned itineraries are invalidated and cannot be booked.

  A user cannot book a flight if the flight's maximum capacity would be exceeded. Each flight’s capacity is stored in the Flights table as in HW3, and you should have records as to how many seats remain on each flight based on the reservations.

  If booking is successful, then assign a new reservation ID to the booked itinerary.
  Note that 1) each reservation can contain up to 2 flights (in the case of indirect flights),
  and 2) each reservation should have a unique ID that incrementally increases by 1 for each successful booking.


- **pay** allows a user to pay for an existing unpaid reservation.
  It first checks whether the user has enough money to pay for all the flights in the given reservation. If successful, it updates the reservation to be paid.


- **reservations** lists all reservations for the currently logged-in user.
  Each reservation must have ***a unique identifier (which is different for each itinerary) in the entire system***, starting from 1 and increasing by 1 after each reservation is made.

  There are many ways to implement this. One possibility is to define a "ID" table that stores the next ID to use, and update it each time when a new reservation is made successfully.

  The user must be logged in to view reservations. The itineraries should be displayed using similar format as that used to display the search results, and they should be shown in increasing order of reservation ID under that username.
  Cancelled reservations should not be displayed.


- **cancel** lets a user to cancel an existing uncanceled reservation. The user must be logged in to cancel reservations and must provide a valid reservation ID.
  Make sure you make the corresponding changes to the tables in case of a successful cancellation (e.g., if a reservation is already paid, then the customer should be refunded).


- **quit** leaves the interactive system and logs out the current user (if logged in).


Refer to the documentation in `Query.py` for full specification and the expected responses of the commands above.

***CAUTION:*** Make sure your code produces outputs in the same formats as prescribed! (see test cases for what to expect)

#### Testing:

To test that your application works correctly, we have provided a grading script `grading.py`. Our test harness will run all the test cases in the provided `testcases/` folder. To run the harness, execute `python3 grading.py`.


For every test case it will either print pass or fail, and for all failed cases it will dump out what the implementation returned, and you can compare it with the expected output in the corresponding case file. For concurrent testcases, we will test each one for multiple times to check if all of them pass or fail. For concurrent testcases, there could be multiple combinations of output from user1 and user2, your output should be match one of the combinations to pass the test.

Each test case file is of the following format:

```sh
[command 1]
[command 2]
...
*
[expected output line 1]
[expected output line 2]
...
*
# everything following ‘#’ is a comment on the same line
```

While we've provided test cases for most of the methods, the testing we provide is partial (although significant).
It is **up to you** to implement your solutions so that they completely follow the provided specification.


#### Python customer application

Your task is to start writing the python application that your customers will use.
To make your life easier, we have provided your `create_table.sql` and you only need to modify `Query.py`. Do not modify `FlightService.py`.

Please use unqualified table names in all of your SQL queries  (e.g. say `SELECT * FROM Flights` rather than `SELECT * FROM [dbo].[Flights]`) Otherwise, the continuous integration and grading scripts won't be able to run using your code.


Please make your code reasonably easy to read. To keep things neat we have provided you with the `Flight` inner class that acts as a container for your flight data.
The `toString` method in the Flight class matches what is needed in methods like `search`.
We have also provided a sample helper method `checkFlightCapacity` that uses a prepared statement.
`checkFlightCapacity` outlines the way we think forming prepared statements should go for this assignment (creating a constant SQL string, preparing it in the prepareStatements method, and then finally using it).

### Step 0: Install dependencies
1. pip3 install -r requirements.txt
2. install sqlite3 on your machine
3. tar -zxvf flights-small.tar.gz
4. git clone the repository
5. run `python3 grading.py`

#### Step 1: Implement create, login, and search

Implement the `create`, `login` and `search` commands in `Query.py`. Using ```python3 grading.py```, you should now pass our provided test cases that only involve these three commands.

#### Step 2: Implement book, pay, reservations, cancel, and add transactions!

Implement the `book`, `pay` , `reservations` and `cancel` commands in `Query.py`.

While implementing & trying out these commands, you'll notice that there are problems when multiple users try to use your service concurrently.
To resolve this challenge, you will need to implement transactions that ensure concurrent commands do not conflict.

Think carefully as to *which* commands need transaction handling. Do the `create`, `login` and `search` commands need transaction handling? Why or why not?


#### Step 3: Transaction management

You must use SQL transactions to guarantee ACID properties: we have set the isolation level for your `Connection`, and you may need to check the documentation of APSW on transaction management and add some additional code in appropriate places in `Query.py`.
In particular, you must ensure that the following constraints are always satisfied, even if multiple instances of your application talk to the database at the same time:

*C1:* Each flight should have a maximum capacity that must not be exceeded. Each flight’s capacity is stored in the Flights table as in HW3, and you should have records as to how many seats remain on each flight based on the reservations.

*C2:* A customer may have at most one reservation on any given day, but they can be on more than 1 flight on the same day. (i.e., a customer can have one reservation on a given day that includes two flights, because the reservation is for a one-hop itinerary).

You must use transactions correctly such that race conditions introduced by concurrent execution cannot lead to an inconsistent state of the database.
For example, multiple customers may try to book the same flight at the same time. Your properly designed transactions should prevent that.

Design transactions correctly. Avoid including user interaction inside a SQL transaction: that is, don't begin a transaction then wait for the user to decide what she wants to do (why?).
The rule of thumb is that transactions need to be *as short as possible, but not shorter*.

When one uses a DBMS, recall that by default **each statement executes in its own transaction**.


This is the same when executing transactions from Python: by default, each SQL statement will be executed as its own transaction.
To group multiple statements into one transaction in Python, please refer to the documentation of APSW.



Your `executeQuery` calls will throw a `SQLException` when an error occurs (e.g., multiple customers try to book the same flight concurrently).
Make sure you handle the `SQLException` appropriately. Again, please check the exception section in APSW documentations.
For instance, if a seat is still available but the execution failed due a temporary issue such as deadlock, the booking should eventually go through (even though you might need to retry due to `SQLException`s being thrown).
If no seat is available, the booking should be rolled back, etc.

The total amount of code to add transaction handling is in fact small, but getting everything to work harmoniously may take some time.
Debugging transactions can be a pain, but print statements are your friend!

Now you should pass all the provided concurrent testcases.

Remember that each test case file is in the following format:

```sh
[command 1]
[command 2]
...
*
[expected output line 1]
[expected output line 2]
...
*
# everything following ‘#’ is a comment on the same line
```

The `*` separates between commands and the expected output. To test with multiple concurrent users, simply add more `[command...] * [expected output...]` pairs to the file, for instance:

 ```sh
 [command 1 for user1]
 [command 2 for user1]
 ...
 *
 [expected output line 1 for user1]
 [expected output line 2 for user1]
 ...
 *
 [command 1 for user2]
 [command 2 for user2]
 ...
 *
 [expected output line 1 for user2]
 [expected output line 2 for user2]
  ...
 *
 ```

Each user is expected to start concurrently in the beginning. If there are multiple output possibilities due to transactional behavior, then separate each group of expected output with `|`. See `book_2UsersSameFlight.txt` for an example. If you fail to pass any testcase, please compare the expected output for user1 and user2 against your output.


*Congratulations!* You now finish the entire flight booking application and is ready to launch your flight booking business :)


#### What to turn in:
* Your fully-completed version of the `Query.py`


#### Grading:

We will be testing your implementations under Linux with `python3 grading.py` automatically. But remember that we only provide a partial set of testcases for you. 

## Submission Instructions

Please submit `Query.py` file to GradeScope