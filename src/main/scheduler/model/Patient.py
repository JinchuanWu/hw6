import sys

from model.Vaccine import Vaccine

sys.path.append("../util/*")
sys.path.append("../db/*")
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql


class Patient:
    def __init__(self, usersname, password=None, salt=None, hash=None):
        self.usersname = usersname
        self.password = password
        self.salt = salt
        self.hash = hash

        # getters

    def get(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        get_patient_details = "SELECT Salt, Hash FROM Patients WHERE Patientsname = %s"
        try:
            cursor.execute(get_patient_details, self.usersname)
            for row in cursor:
                curr_salt = row['Salt']
                curr_hash = row['Hash']
                calculated_hash = Util.generate_hash(self.password, curr_salt)
                if not curr_hash == calculated_hash:
                    # print("Incorrect password")
                    cm.close_connection()
                    return None
                else:
                    self.salt = curr_salt
                    self.hash = calculated_hash
                    cm.close_connection()
                    return self
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()
        return None

    def get_usersname(self):
        return self.usersname

    def get_salt(self):
        return self.salt

    def get_hash(self):
        return self.hash

    def save_to_db(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        add_patients = "INSERT INTO Patients VALUES (%s, %s, %s)"
        try:
            cursor.execute(add_patients, (self.usersname, self.salt, self.hash))
            # you must call commit() to persist your data if you don't set autocommit to True
            conn.commit()
        except pymssql.Error:
            raise
        finally:
            cm.close_connection()

    def search_schedule(self, d):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        search_ava_schedule = "SELECT Username FROM Availabilities WHERE Time = %s ORDER BY Username"
        try:
            cursor.execute(search_ava_schedule, d)
            result = cursor.fetchall()
            cm.close_connection()
            return result
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()

    def search_vaccine(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        search_ava_vaccine = "SELECT Name, Doses FROM Vaccines"
        try:
            cursor.execute(search_ava_vaccine)
            result = cursor.fetchall()
            cm.close_connection()
            return result
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()

    def reserve_vaccine(self, d, vaccine_name):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        try:
            result = self.search_schedule(d)
            if len(result) == 0:
                print("No Caregiver is available!")
                return
            else:
                vaccine = Vaccine(vaccine_name, None).get()
                if vaccine is None:
                    print("We do not have this vaccine! please choose vaccine from this list:")
                    cursor.execute("SELECT Name FROM Vaccines")
                    for row in cursor:
                        print(row[0])
                    return
                elif vaccine.get_available_doses() == 0:
                    print("Not enough available doses!")
                    return
            vaccine.decrease_available_doses(1)

            caregiver_name = result[0][0]
            add_appointment = "INSERT INTO Reservation VALUES (%d, %s, %s, %s, %s)"
            find_max_id = "SELECT Max(appointment_id) FROM Reservation"
            temp_cursor = conn.cursor()
            temp_cursor.execute(find_max_id)
            max_id = temp_cursor.fetchone()[0]
            if max_id is None:
                cursor.execute(add_appointment, (self.get_usersname(), caregiver_name, 1, d, vaccine_name))
                max_id = 1
            else:
                cursor.execute(add_appointment, (self.get_usersname(), caregiver_name, max_id + 1, d, vaccine_name))
                max_id = max_id + 1

            drop_availability = "DELETE FROM Availabilities WHERE Time = %s AND Username = %s"
            cursor.execute(drop_availability, (d, caregiver_name))

            conn.commit()

            print("Appointment ID: %d" % max_id + "," + "Caregiver username: " + caregiver_name)
            return 1

        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()


    def search_appointments(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        search_all_app = "SELECT appointment_id, Name, Time, Username FROM Reservation WHERE Patientsname = %s ORDER BY appointment_id"
        try:
            cursor.execute(search_all_app, self.get_usersname())
            result = cursor.fetchall()
            return result
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()
