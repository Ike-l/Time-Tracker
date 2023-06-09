import datetime  # Handles data
import sqlite3  # stores data
from time import sleep  # testing purposes
from functools import lru_cache  # for averages to speed up function times
from threading import Thread  # for reminders and inputs
from playsound import playsound  # uses copyright free


def main():
    while (True):
        command = input("Listening for commands... ")
        if command.lower() == "apd":
            print(averagePerDay())
        if command.lower() == "apw":
            print(averagePerWeek())
        if command.lower() == "apm":
            print(averagePerMonth())
        if command.lower() == "total":
            print(total())
        if command.lower() == "cs":
            print(datetime.datetime.now()-startTime)
        if command.lower() == "cm":
            print(datetime.datetime.now()-startTimeMode)
        if command.lower() == "change":
            tempMode = input("Change: What are you doing? research/coding ")
            changeMode(tempMode)
        if command.lower() == "stop":
            endTimer()

def startTimer():
    print("Starting Timer...")
    global startTime  # can use this everywhere in code
    global mode
    global startTimeMode
    mode = input("Setup: What are you doing? research/coding ")
    startTime = datetime.datetime.now()  # object formatted such year-month-day hour:minute:seconds.milliseconds  i.e 2023-06-09 11:35:00.394642
    startTimeMode = datetime.datetime.now()
    session_times[mode]["started"].append(startTimeMode)

def exit_handler():  # runs when program closes
    endTimer()

def endTimer():  # shoves data into a file
    currentTime = datetime.datetime.now()
    session_times[mode]["ended"].append(currentTime)
    session_times[mode]["total"] += (currentTime.timestamp() - startTimeMode.timestamp())
    conn = sqlite3.connect('productivity.db')
    cursor = conn.cursor()
    session_duration = (datetime.datetime.now() - startTime).total_seconds() / 3600
    cursor.execute("INSERT INTO Sessions (duration_hours, date) VALUES (?, ?)", (session_duration, str(startTime.date())))
    session_id = cursor.lastrowid
    for activity_type, activity_times in session_times.items():
        cursor.execute("""
            INSERT INTO Session_Information (session_id, activity_type, activity_duration)
            VALUES (?, ?, ?)
            """, (session_id, activity_type, activity_times['total'] / 3600))
        for start_time, end_time in zip(activity_times['started'], activity_times['ended']):
            cursor.execute("""
                INSERT INTO Time_Spent (session_id, activity_type, start_time, end_time)
                VALUES (?, ?, ?, ?)
                """, (session_id, activity_type, str(start_time), str(end_time)))
    conn.commit()
    conn.close()


# Data to store: Session Duration, Time spent: [coding, research, break], Current Date.
# how long spent on each thing in chronology

# table for sessions: ID, date, duration
# table for timespent: ID, sessions.ID coding total time, research total time, break total time.
# table for time information: ID, timespent.ID, start times, end times


# will need to use SQL to get these running properly
@lru_cache
def averagePerDay():
    print("running code")
    average_per_day = "average_per_day"
    return average_per_day


@lru_cache
def averagePerWeek():
    print("running code")
    average_per_week = "average_per_week"
    return average_per_week


@lru_cache
def averagePerMonth():
    print("running code")
    average_per_month = "average_per_month"
    return average_per_month


@lru_cache
def total():
    print("running code")
    total = "total"
    return total


def play_reminder():
    playsound('BellSound.mp3')  # copyright free


def reminder():
    while (True):
        sleep(3600)
        # have to make sure this is longer than the audio cause jank - tried just having flags for when it is playing
        # and stopping the while then but still didnt work
        play_reminder()


def changeMode(newMode):
    global startTimeMode
    global mode
    currentTime = datetime.datetime.now()
    session_times[mode]["ended"].append(currentTime)
    session_times[mode]["total"] += (currentTime.timestamp() - startTimeMode.timestamp())
    session_times[newMode]["started"].append(currentTime)
    startTimeMode = currentTime
    mode = newMode


if __name__ == "__main__":
    # Threads
    main_thread = Thread(target=main)
    reminder_thread = Thread(target=reminder)

    # SQLite3
    conn = sqlite3.connect('productivity.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Sessions (
        session_id INTEGER PRIMARY KEY,
        duration_hours REAL,
        date TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Session_Information (
        activity_id INTEGER PRIMARY KEY,
        session_id INTEGER,
        activity_type TEXT,
        activity_duration REAL,
        FOREIGN KEY(session_id) REFERENCES Sessions(session_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Time_Spent (
        chronology_id INTEGER PRIMARY KEY,
        session_id INTEGER,
        activity_type TEXT,
        start_time TEXT,
        end_time TEXT,
        FOREIGN KEY(session_id) REFERENCES Sessions(session_id)
    )
    """)
    conn.commit()
    conn.close()

    # Global Scope Setup
    session = {}
    session_times = {"research": {"started": [], "ended": [], "total": 0},
                     "coding": {"started": [], "ended": [], "total": 0},
                     "break": {"started": [], "ended": [], "total": 0}}
    startTimer()
    main_thread.start()
    reminder_thread.start()
