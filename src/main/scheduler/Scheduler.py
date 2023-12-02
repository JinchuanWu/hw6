from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime

'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    # create_patient <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    # save to patient information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Patientsname = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Patientsname'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    # login_patient <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient
        menu()


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver
        menu()


def search_caregiver_schedule(tokens):
    #  check 1: check if the current user logged-in
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    try:
        # assume input is hyphenated in the format mm-dd-yyyy
        date_tokens = date.split("-")
        month = int(date_tokens[0])
        day = int(date_tokens[1])
        year = int(date_tokens[2])
        if current_caregiver is not None:
            d = datetime.datetime(year, month, day)
            caregiver_result = current_caregiver.search_schedule(d)
            vaccine_result = current_caregiver.search_vaccine()
            if len(caregiver_result) == 0:
                print("No caregiver available!")
                return

            print("-" * (len(vaccine_result) * 20))
            # This block of code outputs the column headers; the for-loop prints each vaccine name
            print("{}\t".format("Caregiver"), end="")
            for i in range(0, len(vaccine_result)):
                print("{: >10}\t".format(vaccine_result[i][0]), end="")
            print("\n", end="")

            print("-" * (len(vaccine_result) * 20))
            # Now print out each caregiver followed by the dose number of each vaccine
            for row in caregiver_result:
                print("{}\t".format(row[0]), end="")
                for i in range(0, len(vaccine_result)):
                    print("{: >10}\t".format(vaccine_result[i][1]), end="")
                print("")

        if current_patient is not None:
            d = datetime.datetime(year, month, day)
            caregiver_result = current_patient.search_schedule(d)
            vaccine_result = current_patient.search_vaccine()
            if len(caregiver_result) == 0:
                print("No caregiver available!")
                return

            print("-" * (len(vaccine_result) * 20))
            # This block of code outputs the column headers; the for-loop prints each vaccine name
            print("{}\t".format("Caregiver"), end="")
            for i in range(0, len(vaccine_result)):
                print("{: >10}\t".format(vaccine_result[i][0]), end="")
            print("\n", end="")

            print("-" * (len(vaccine_result) * 20))
            # Now print out each caregiver followed by the dose number of each vaccine
            for row in caregiver_result:
                print("{}\t".format(row[0]), end="")
                for i in range(0, len(vaccine_result)):
                    print("{: >10}\t".format(vaccine_result[i][1]), end="")
                print("")


    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
        return


def reserve(tokens):
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    if current_patient is None:
        print("Please login as a patient!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("reserve failed.")
        return
    date = tokens[1]
    vaccine = tokens[2]
    try:
        # assume input is hyphenated in the format mm-dd-yyyy
        date_tokens = date.split("-")
        month = int(date_tokens[0])
        day = int(date_tokens[1])
        year = int(date_tokens[2])
        d = datetime.datetime(year, month, day)
        check = current_patient.reserve_vaccine(d, vaccine)
        if check is not None:
            menu()
    except pymssql.Error as e:
        print("reserve Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("please try again")
        print("Error:", e)
        return


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    try:
        # assume input is hyphenated in the format mm-dd-yyyy
        date_tokens = date.split("-")
        month = int(date_tokens[0])
        day = int(date_tokens[1])
        year = int(date_tokens[2])
        d = datetime.datetime(year, month, day)
        result = current_caregiver.search_duplicate(d)
        if result is not None:
            print("Cannot upload duplicate availability!")
            return
        else:
            current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")
    menu()


def cancel(tokens):
    #  check 1: check if the current user logged-in
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)
    appointment_id = tokens[1]
    try:
        result = search_current_id(appointment_id)
        if result is None:
            print("Could not find appointment with id:", appointment_id)
            return
        if current_caregiver is not None:
            if result["Username"] != current_caregiver.get_username():
                print("Could not find appointment with id:", appointment_id)
                return
        if current_patient is not None:
            if result["Patientsname"] != current_patient.get_usersname():
                print("Could not find appointment with id:", appointment_id)
                return

        delete_appointment = "DELETE FROM Reservation WHERE appointment_id = %d"
        vaccine = Vaccine(result["Name"], None).get()
        vaccine.increase_available_doses(1)
        cursor.execute(delete_appointment, appointment_id)
        conn.commit()
        print("Appointment successfully cancelled.")
        if current_patient is not None:
            date = result["Time"]
            caregiver = result["Username"]
            cursor.execute("INSERT INTO Availabilities VALUES (%d, %d)", (date, caregiver))
            conn.commit()
        menu()

    except pymssql.Error as e:
        print("cancelling appointment failed")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when cancelling appointment")
        print("Error:", e)
        return
    finally:
        cm.close_connection()

def search_current_id(id):
    cm = ConnectionManager()
    conn = cm.create_connection()

    search_state = "SELECT * FROM Reservation WHERE appointment_id = %d"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(search_state, id)
        result = cursor.fetchone()
        return result
    except pymssql.Error as e:
        print("Error occurred when deleting appointment")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when deleting appointment")
        print("Error:", e)
    finally:
        cm.close_connection()
    return None





def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    if len(tokens) != 1:
        print("Please try again!")
        return
    try:
        if current_caregiver is not None:
            appointments = current_caregiver.search_appointments()
            if len(appointments) == 0:
                print("No appointment currently!")
                return
            print("-" * (len(appointments) * 20))
            print("{: >10}\t{: >10}\t{: >10}\t{: >10}\t".format("Appointment ID", "Vaccine", "Date", "Patient"),
                  end="")
            print("")

            for i in range(0, len(appointments)):
                print("{: >10}\t{: >10}\t{: >10}\t{: >10}\t"
                      .format(appointments[i][0], appointments[i][1], str(appointments[i][2]),
                              appointments[i][3]))

        elif current_patient is not None:
            appointments = current_patient.search_appointments()
            if len(appointments) == 0:
                print("No appointment currently!")
                return
            print("-" * (len(appointments) * 20))
            print("{: >10}\t{: >10}\t{: >10}\t{: >10}\t".format("Appointment ID", "Vaccine", "Date", "Caregiver"),
                  end="")
            print("")

            for i in range(0, len(appointments)):
                print("{: >10}\t{: >10}\t{: >10}\t{: >10}\t"
                      .format(appointments[i][0], appointments[i][1], str(appointments[i][2]),
                              appointments[i][3]))
    except pymssql.Error as e:
        print("Error occurred when showing appointments!")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when showing appointments!")
        print("Error:", e)
        return



def logout(tokens):
    global current_patient
    global current_caregiver
    try:
        if current_patient is not None:
            current_patient = None
            print("Successfully logged out!")
            menu()
        if current_caregiver is not None:
            current_caregiver = None
            print("Successfully logged out!")
            menu()
        else:
            print("Please login first!")
    except Exception as e:
        print("Failed to logout!")
        print("Error:", e)
        return


def menu():
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")
    print("> reserve <date> <vaccine>")
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")
    print("> logout")
    print("> Quit")
    print()

def start():
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == "cancel":
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
