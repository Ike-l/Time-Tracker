# data format
import datetime
# store and retrieve data
import sqlite3
# testing purposes
from time import sleep
# to speed up calculations
from functools import lru_cache
# to separate the while True
from threading import Thread
# https://stackoverflow.com/questions/51464455/how-to-disable-welcome-message-when-importing-pygame
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

def setupThreads():
    global main_thread, reminder_thread
    # connects main and background functions to individual threads
    main_thread = Thread(target=main)
    reminder_thread = Thread(target=reminder)


def setupSQL():
    # connect to the SQLite database
    connection = sqlite3.connect('productivity.db')
    cursor = connection.cursor()
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
    connection.commit()
    connection.close()

def setupPyGameSound():
    pygame.mixer.init()

def setupGlobalVars():
    global session_times, command_list
    session_times = {"research": {"started": [], "ended": [], "total": 0},
                     "coding": {"started": [], "ended": [], "total": 0},
                     "break": {"started": [], "ended": [], "total": 0}}
    command_list = ["help", "apd", "apw", "apm", "total", "cs", "cad", "ca", "change", "stop"]


def main():
    while True:
        command = input("Listening for commands: ")
        if command.lower() == "help":
            print(f"Commands are: {' '.join(command_list)}")
        if command.lower() == "apd":
            print("average per day is:", averagePerDay())
        if command.lower() == "apw":
            print("average per week is:", averagePerWeek())
        if command.lower() == "apm":
            print("average per month is:", averagePerMonth())
        if command.lower() == "total":
            print("total duration:", total())
        if command.lower() == "cs":
            print("current session length:", datetime.datetime.now() - startTime)
        if command.lower() == "cad":
            print("current activity length:", datetime.datetime.now() - startTimeMode)
        if command.lower() == "ca":
            print("current activity is:", activity)
        if command.lower() == "change":
            # out of function so sound can auto change it
            newActivity = input("Change: What are you doing? research/coding: ")
            changeMode(newActivity)
        if command.lower() == "stop":
            print("stopping:")
            endTimer()


def startTimer():
    print("Starting Timer...")
    global startTime, activity, startTimeMode
    activity = input("Setup: What are you doing? research/coding: ")
    startTime = datetime.datetime.now()
    startTimeMode = datetime.datetime.now()
    session_times[activity]["started"].append(startTimeMode)


def exit_handler():
    endTimer()


def endTimer():
    currentTime = datetime.datetime.now()
    session_times[activity]["ended"].append(currentTime)
    session_times[activity]["total"] += (currentTime.timestamp() - startTimeMode.timestamp())
    print("\nconnecting to db")
    # connect to the SQLite database
    connection = sqlite3.connect('productivity.db')
    cursor = connection.cursor()

    # calculate session duration in hours
    session_duration = (datetime.datetime.now() - startTime).total_seconds() / 3600
    print("inserting into Sessions")
    # insert into Sessions table and get the inserted session_id
    cursor.execute("INSERT INTO Sessions (duration_hours, date) VALUES (?, ?)",
                   (session_duration, str(startTime.date())))
    session_id = cursor.lastrowid
    print("inserting to Session_Information and Time_spent")
    # loop through session_times and insert data into Session_Information and Time_Spent tables
    for activity_type, activity_times in session_times.items():
        # insert into Session_Information table
        cursor.execute("""
            INSERT INTO Session_Information (session_id, activity_type, activity_duration)
            VALUES (?, ?, ?)
            """, (session_id, activity_type, activity_times['total'] / 3600))

        # insert into Time_Spent table
        for start_time, end_time in zip(activity_times['started'], activity_times['ended']):
            cursor.execute("""
                INSERT INTO Time_Spent (session_id, activity_type, start_time, end_time)
                VALUES (?, ?, ?, ?)
                """, (session_id, activity_type, str(start_time), str(end_time)))
    print("commiting and closing")
    connection.commit()
    connection.close()
    print("done...\n")


# to help make the db i wrote it down like this, ignore this if u want.

# Data to store: Session Duration, Time spent: [coding, research, break], Current Date.
# how long spent on each thing in chronology

# table for sessions: ID, date, duration
# table for timespent: ID, sessions.ID coding total time, research total time, break total time.
# table for time information: ID, timespent.ID, start times, end times

@lru_cache
def averagePerDay():
    # not done yet
    print("running code")
    average_per_day = "average_per_day"
    return average_per_day


@lru_cache
def averagePerWeek():
    # not done yet
    print("running code")
    average_per_week = "average_per_week"
    return average_per_week


@lru_cache
def averagePerMonth():
    # not done yet
    print("running code")
    average_per_month = "average_per_month"
    return average_per_month


@lru_cache
def total():
    # not done yet
    print("running code")
    total = "total"
    return total


def play_reminder():
    global activity
    # for future version when it has sound to tell to get back to work
    #activity = changeMode("break") if activity != "break" else activity
    #print("\nChanged activity to 'break'\nRemember to switch it back (change)\nStill listening...")
    pygame.mixer.music.load("BellSound.mp3") # copyright free https://www.youtube.com/watch?v=YEf7_fPMbr4&pp=ygUZYmVsbCBzb3VuZCBjb3B5cmlnaHQgZnJlZQ%3D%3D
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy() == True:
        continue


def reminder():
    while True:
        sleep(3600)
        play_reminder()


def changeMode(newActivity):
    global startTimeMode, activity
    currentTime = datetime.datetime.now()
    session_times[activity]["ended"].append(currentTime)
    session_times[activity]["total"] += (currentTime.timestamp() - startTimeMode.timestamp())
    session_times[newActivity]["started"].append(currentTime)
    startTimeMode = currentTime
    activity = newActivity


if __name__ == "__main__":
    setupThreads()
    setupSQL()
    setupPyGameSound()
    # global scope setup
    session = {}
    setupGlobalVars()

    # starts program
    startTimer()
    main_thread.start()
    reminder_thread.start()
