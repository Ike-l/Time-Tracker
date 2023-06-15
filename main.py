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

import os
# calculations
import pandas as pd
# plotting
import matplotlib.pyplot as plt

os.environ[
    'PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"  # https://stackoverflow.com/questions/51464455/how-to-disable-welcome-message-when-importing-pygame
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
    CREATE TABLE IF NOT EXISTS Time_Calender (
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
    global session_times, commands
    session_times = {"research": {"started": [], "ended": [], "total": 0},
                     "coding": {"started": [], "ended": [], "total": 0},
                     "break": {"started": [], "ended": [], "total": 0}}
    commands = {
        "help": lambda: help_command(),
        "test": lambda: test_command(),
        "mins": lambda: print(minSession()),
        "mina": lambda: print(minActivity()),
        "maxs": lambda: print(maxSession()),
        "maxa": lambda: print(maxActivity()),
        "apd": lambda: print("average per day is:", averagePerDay()),
        "apw": lambda: print("average per week is:", averagePerWeek()),
        "apm": lambda: print("average per month is:", averagePerMonth()),
        "total": lambda: print(f"total duration: {total()} hours"),
        "piplot": piPlot,
        "cs": lambda: print("current session length:", datetime.datetime.now() - startTime),
        "cad": lambda: print("current activity length:", datetime.datetime.now() - startTimeActivity),
        "ca": lambda: print("current activity is:", activity),
        "change": change_activity_command,
        # Assuming you will define this function to include the required functionality
        "stop": lambda: print("stopping:", endTimer()),
        "exit": exit_command  # Assuming you will define this function to include the required functionality
    }


# @lru_cache
def getDataFrame(table_name):
    connection = sqlite3.connect("productivity.db")
    query = f"SELECT * FROM {table_name}"  # Use your table name and required SQL command
    df = pd.read_sql_query(query, connection)
    connection.close()
    return df


def help_command():
    print(f"Commands are: {' '.join(commands.keys())}")


def test_command():
    print(getDataFrame("Sessions"))


def stop_command():
    print("Stopping:")
    endTimer()


def exit_command():
    check = input("This will exit without saving\nAre you sure you wish to proceed? ")
    if check.lower() == "yes":
        print("Exiting without saving")
        raise SystemExit
    print("Continuing")


def change_activity_command():
    newActivity = input("Change: What are you doing? research/coding/break: ").lower()
    while newActivity not in session_times.keys():
        newActivity = input("Change: What are you doing? research/coding/break: ").lower()
    changeActivity(newActivity)


def main():
    while True:
        command = input("Listening for commands: ").lower()
        if command in commands:
            commands[command]()
        else:
            print("Unknown command. Type 'help' to see a list of available commands.")


def startTimer():
    print("Starting Timer...")
    global startTime, activity, startTimeActivity
    activity = input("Setup: What are you doing? research/coding: ").lower()
    while activity not in session_times.keys():
        activity = input("Setup: What are you doing? research/coding: ").lower()
    startTime = datetime.datetime.now()
    startTimeActivity = datetime.datetime.now()
    session_times[activity]["started"].append(startTimeActivity)
    print(f"Started timer on {activity}")


def exit_handler():
    endTimer()


def endTimer():
    currentTime = datetime.datetime.now()
    session_times[activity]["ended"].append(currentTime)
    session_times[activity]["total"] += (currentTime.timestamp() - startTimeActivity.timestamp())
    print("\nconnecting to db")
    # connect to the SQLite database
    connection = sqlite3.connect("productivity.db")
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
                INSERT INTO Time_Calender (session_id, activity_type, start_time, end_time)
                VALUES (?, ?, ?, ?)
                """, (session_id, activity_type, str(start_time), str(end_time)))
    print("committing and closing")
    connection.commit()
    connection.close()
    print("done...\n")
    # raise SystemExit


# to help make the db i wrote it down like this, ignore this if u want.

# Data to store: Session Duration, Time spent: [coding, research, break], Current Date.
# how long spent on each thing in chronology

# table for sessions: ID, date, duration
# table for timespent: ID, sessions.ID coding total time, research total time, break total time.
# table for time information: ID, timespent.ID, start times, end times
def minSession():
    # returns minimum duration of sessions with the date
    Sessions_DF = getDataFrame("Sessions")
    return f"Minimum session duration: {Sessions_DF.duration_hours.min()} hours\nSession date: {Sessions_DF.date[Sessions_DF.duration_hours.idxmin()]}"


def minActivity():
    # returns the minimum duration for each activity and date
    Merged_DF = pd.merge(getDataFrame("Session_Information"), getDataFrame("Sessions"), on='session_id', how='inner')
    string = ""
    for activity in session_times.keys():
        min_activity_id = Merged_DF.loc[Merged_DF.activity_type == activity, 'activity_duration'].idxmin()
        string += f"{activity}: {Merged_DF.loc[min_activity_id, 'activity_duration']} hours   Date:{Merged_DF.loc[min_activity_id, 'date']}\n"
    return string[0:-1]


def maxSession():
    # returns maximum duration of sessions with the date
    Sessions_DF = getDataFrame("Sessions")
    return f"Minimum session duration: {Sessions_DF.duration_hours.max()} hours\nSession date: {Sessions_DF.date[Sessions_DF.duration_hours.idxmax()]}"


def maxActivity():
    # returns the minimum duration for each activity and date
    Merged_DF = pd.merge(getDataFrame("Session_Information"), getDataFrame("Sessions"), on='session_id', how='inner')
    string = ""
    for activity in session_times.keys():
        max_activity_id = Merged_DF.loc[Merged_DF.activity_type == activity, 'activity_duration'].idxmax()
        string += f"{activity}: {Merged_DF.loc[max_activity_id, 'activity_duration']} hours   Date:{Merged_DF.loc[max_activity_id, 'date']}\n"
    return string[0:-1]


def averagePerDay():
    # not done yet
    average_per_day = "average_per_day"
    return average_per_day


def averagePerWeek():
    # not done yet
    average_per_week = "average_per_week"
    return average_per_week


def averagePerMonth():
    # not done yet
    average_per_month = "average_per_month"
    return average_per_month


def total():
    Sessions_DF = getDataFrame("Sessions")
    return Sessions_DF.duration_hours.sum()


def piPlot():
    Session_Information_DF = getDataFrame("Session_Information")
    # Group by activity type and sum durations
    Session_Information_DF_Grouped = Session_Information_DF.groupby("activity_type")["activity_duration"].sum()
    # Sum of all activities, cannot use total()
    Session_Information_Sum = Session_Information_DF['activity_duration'].sum()
    # if any activity is equal to the sum
    if any(Session_Information_DF_Grouped == Session_Information_Sum):
        dominant_activity = \
            Session_Information_DF_Grouped[Session_Information_DF_Grouped == Session_Information_Sum].index[0]
        print(f"{dominant_activity} has 100% duration")
    else:
        plt.figure(figsize=(10, 6))
        plt.pie(Session_Information_DF_Grouped, labels=Session_Information_DF_Grouped.index, autopct='%1.1f%%')
        plt.title("Activity durations")
        plt.show()
        print("Must close plot for program to continue")


def play_reminder():
    global activity
    # for future version when it has sound to tell to get back to work
    # activity = changeMode("break") if activity != "break" else activity
    # print("\nChanged activity to 'break'\nRemember to switch it back (change)\nStill listening...")
    pygame.mixer.music.load(
        "BellSound.mp3")  # copyright free https://www.youtube.com/watch?v=YEf7_fPMbr4&pp=ygUZYmVsbCBzb3VuZCBjb3B5cmlnaHQgZnJlZQ%3D%3D
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue


def reminder():
    while True:
        sleep(3600)
        play_reminder()


def changeActivity(newActivity):
    global startTimeActivity, activity
    currentTime = datetime.datetime.now()
    session_times[activity]["ended"].append(currentTime)
    session_times[activity]["total"] += (currentTime.timestamp() - startTimeActivity.timestamp())
    session_times[newActivity]["started"].append(currentTime)
    startTimeActivity = currentTime
    print(f"Changed activity from {activity} to {newActivity}")
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
