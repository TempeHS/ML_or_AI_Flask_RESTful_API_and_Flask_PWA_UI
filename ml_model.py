# This script will import a markbook and allow you to estimate a mark
# Written by Peter Parker - 5/11/2024
# Version 0.6

# this script works with the file marksWithHeadings.csv sample file

import numpy
import csv
import os.path
from sklearn.linear_model import LinearRegression


# holds data on the students and tasks
# returns data in different ways
class Markbook:
    def __init__(self):
        self.headings = []
        self.marks = []
        self.students = []

    # returns a 2dimentional array of marks [student][mark]
    def getMarks(self):
        return self.marks

    # returns a single mark which is the particular mark a student got for a task
    # student is student number not name, zero indexed
    def getTaskMark(self, student, task):
        return self.marks[student][task]

    # return all tasks for a particular task
    def getTaskMarks(self, task):
        taskMarks = []
        for student in self.marks:
            taskMarks.append(student[task])
        return taskMarks

    # return marks for each task for a particular student
    def getStudentMarks(self, student):
        return self.marks[student].copy()

    # returns the rank a student got for a particular task
    # student is student number not name
    def getTaskRank(self, student, task):
        marksSorted = self.getTaskMarks(task)

        marksSorted.sort(reverse=True)
        rank = marksSorted.index(self.marks[student][task])
        return rank

    # returns an array of the rank for each student for a particular task
    def getStudentTaskRanks(self, student):
        ranks = []
        studentMarks = self.getStudentMarks(student)

        task = 0
        for studentMark in studentMarks:
            if studentMark == -1:
                ranks.append(-1)
            else:
                ranks.append(self.getTaskRank(student, task))
            task = task + 1

        return ranks

    # returns a list of the students in the markbook
    def getStudentList(self):
        students = self.students.copy()
        return students

    # returns a list of the names of the tasks in the markbook
    def getTaskList(self):
        headings = self.headings.copy()
        headings.pop(0)
        return headings

    # returns a list of all the headings in the markbook (Students heading + tasks)
    def getHeadings(self):
        headings = self.headings.copy()
        return headings

    # returns the min mark, max mark and average mark for a particular task
    def getTaskStats(self, task):
        marks = self.getTaskMarks(task)

        marks.sort()

        # clear out any missing marks
        while marks[0] == -1:
            marks.pop(0)

        # not using built in min and max functions as want -1 values to be ignored
        minMark = marks[0]
        maxMark = marks[-1]

        markTotal = 0

        for mark in marks:
            markTotal = markTotal + mark

        averageMark = round(markTotal / len(marks))

        return minMark, maxMark, averageMark

    # set the array of headings
    def setTaskList(self, headings):
        self.headings = headings
        self.headings[0] = "Students"
        return True

    # set the students in the markbook
    def setStudents(self, students):
        self.students = students
        return True

    # set the marks for the tasks
    def setMarks(self, marks):
        self.marks = marks
        return True

    # add a student and their marks to the student and marks lists
    def addStudent(self, studentData):
        self.students.append(studentData.pop(0))
        self.marks.append(studentData)
        return True


# deals with importing the data from the csv file
class DataImporter:
    def __init__(self, dataFile):
        self.dataFile = dataFile
        self.marks = []

    # import the data from a csv file.
    # the first row should be headings,  the first column should be student names
    def importData(self):
        marks = []
        marksFile = open(self.dataFile)
        marksRawInit = csv.reader(marksFile)
        marksRaw = list(marksRawInit)

        marks.append(marksRaw.pop(0))

        # iterate over each row in the file
        for student in marksRaw:
            studentMarksInt = []

            studentMarksInt.append(student.pop(0))

            # iterate over each task converting the mark from a string to an integer
            for mark in student:
                if mark == "":
                    studentMarksInt.append(-1)
                else:
                    studentMarksInt.append(int(mark))

            marks.append(studentMarksInt)

        self.marks = marks
        return True

    # make sure that no marks are over 100 or less than 0
    # make sure that every student has the right number of tasks
    def validate(self):
        return True

    # put the extracted details together into the markbook object
    def createMarkBook(self):
        markbook = Markbook()

        markbook.setTaskList(self.marks[0])

        counter = 1
        while counter < len(self.marks):
            markbook.addStudent(self.marks[counter])
            counter = counter + 1

        return markbook


# manipulates data out of the markbook to derive the estimates
class DataProcessor:
    def __init__(self, markbook):
        self.markbook = markbook

    # estimate a mark based upon an estimated rank for the student for the given task
    def estimateMark(self, student, task):
        # Create base data with the task to estimate omitted
        # x axis
        ranksBase = (
            []
        )  # this needs to be an array of arrays with a single item which is the task
        # y axis
        marksBase = []  # this is a 1 dimensional array of ranks in other tasks

        markRanks = self.taskMarkRanks(task)

        counter = 0
        for entry in markRanks:
            if (
                counter != student and entry[0] != -1
            ):  # So that we omit the student that we are estimating
                rank = [entry[1]]
                ranksBase.append(rank)
                marksBase.append(entry[0])
            counter = counter + 1

        # print(ranksBase)
        # print(marksBase)

        # Create the model
        model = LinearRegression()
        model.fit(ranksBase, marksBase)

        # get the estimated rank for the student for the task
        rankForStudentEstimate = self.estimateRank(student, task)

        estimatedMark = model.predict([[rankForStudentEstimate]])

        return round(estimatedMark[0])

    # estimates the rank for the student by looking at their ranks for other assessment tasks
    def estimateRank(self, student, task):
        # Create base data with the task to estimate omitted
        # x axis
        tasksBase = (
            []
        )  # this needs to be an array of arrays with a single item which is the task
        # y axis
        ranksBase = []  # this is a 1 dimensional array of ranks in other tasks

        studentRanks = self.markbook.getStudentTaskRanks(student)

        counter = 0
        for rank in studentRanks:
            if counter != task:  # So that we omit the task that we are estimating
                taskTitle = [counter]
                tasksBase.append(taskTitle)
                ranksBase.append(rank)
            counter = counter + 1

        # print (tasksBase)
        # print (ranksBase)

        # Create the model
        model = LinearRegression()
        model.fit(tasksBase, ranksBase)

        estimatedRank = model.predict([[task]])

        return round(estimatedRank[0])

    # get a list of task marks and their associated ranks
    # returns a 2-dimensional array of mark and rank for each student
    def taskMarkRanks(self, task):
        marks = self.markbook.getTaskMarks(task)

        marksSorted = marks.copy()
        marksSorted.sort(reverse=True)

        markRank = []

        for mark in marks:
            markEntry = []
            markEntry.append(mark)
            markEntry.append(marksSorted.index(mark))
            markRank.append(markEntry)

        return markRank


# manages printing information to the screen and getting input from the user
# could be expanded to include GUI elements
# input actions include data validation where appropriate
class UI:
    def __init__(self):
        return

    # ask the user which .csv file to import from
    def getMarksFile(self):
        # marksFile = input('Marks file to open (.csv) : ')
        # marksFile = 'marksWithHeadings.csv'
        # make life a bit easier during development / testing
        marksFile = "marksWithHeadingsAndMissing.csv"

        # check the file actually exists
        while marksFile == "" or os.path.isfile(marksFile) == False:
            if marksFile == "":
                print("Please enter a valid file.")
            elif os.path.isfile(marksFile) == False:
                print("The supplied file doesn't seem to exist.  Possible typo?")

            marksFile = input("Marks file to open (.csv) : ")

        return marksFile

    # print the markbook in a nicely formatted table
    # missing marks are indicated with a "--"
    def printMarkbook(self, markbook):
        # work out width of each column
        columnWidths = self.calculateColumnWidths(markbook)
        totalCharacters = 0

        # print headings
        print("")
        headings = markbook.getHeadings()
        counter = 0
        for heading in headings:
            totalCharacters = totalCharacters + columnWidths[counter]
            spaces = columnWidths[counter] - len(heading)
            print(heading, " " * spaces, sep="", end="")

        print("")  # to add a newline at the end
        print("=" * totalCharacters)

        # print results rows
        students = markbook.getStudentList()
        marks = markbook.getMarks()

        counter = 0
        while counter < len(students):
            spaces = columnWidths[0] - len(students[counter])
            print(students[counter], " " * spaces, sep="", end="")

            taskCounter = 0
            while taskCounter < len(marks[counter]):
                if marks[counter][taskCounter] == -1:
                    markPrint = "--"
                else:
                    markPrint = str(marks[counter][taskCounter])
                spaces = columnWidths[taskCounter + 1] - len(markPrint)
                print(markPrint, " " * spaces, sep="", end="")
                taskCounter = taskCounter + 1

            print("")  # to add a newline at the end
            counter = counter + 1

        print("")
        return True

    # work out the required widths for the table columns
    def calculateColumnWidths(self, markbook):
        columnWidths = []
        minColumnWidth = 10

        headings = markbook.getHeadings()

        for heading in headings:
            if len(heading) + 3 < 10:
                columnWidths.append(10)
            else:
                columnWidths.append(len(heading) + 3)

        # Now check if any student names are longer than the heading
        students = markbook.getStudentList()

        for student in students:
            if len(student) > columnWidths[0]:
                columnWidths[0] = len(student)

        return columnWidths

    # ask which task and for which student the mark should be estimated
    def getTaskToEstimate(self, markbook):
        students = markbook.getStudentList()
        tasks = markbook.getTaskList()

        print("Please select the student and task to estimate :")
        numStudents = len(students)
        print(f"Student 1 to {numStudents}")
        print("Tasks : ", sep="", end="")
        counter = 1
        for task in tasks:
            print(f" {task} ({counter}),  ", sep="", end="")
            counter = counter + 1
        print("")

        student = (
            int(input("Student to estimate : ")) - 1
        )  # -1 to adjust for zero indexing
        task = (
            int(input("Task to estimate    : ")) - 1
        )  # -1 to adjust for zero indexing

        while (
            student == ""
            or task == ""
            or student < 0
            or student > len(students)
            or task < 0
            or task > len(tasks)
        ):
            print("Invalid input")
            student = (
                int(input("Student to estimate : ")) - 1
            )  # -1 to adjust for zero indexing
            task = (
                int(input("Task to estimate    : ")) - 1
            )  # -1 to adjust for zero indexing

        return student, task

    # print the results of the processing and some supporting statistics
    def printEstimate(self, student, task, markEstimate, rankEstimate, markbook):
        studentPrint = markbook.students[student]
        taskPrint = markbook.headings[task + 1]
        print("")
        print(f"Estimate for student {studentPrint} for task {taskPrint}")
        print(f"The estimated mark is : {markEstimate}")
        print(f"This gives an estimated rank of : {rankEstimate}")

        minMark, maxMark, averageMark = markbook.getTaskStats(task)

        print(
            f"Stats for task - Min mark : {minMark}, Max mark : {maxMark}, Average mark : {averageMark}"
        )

        print("")
        return True


# Manage the overall processing
def main():
    ui = UI()

    # Set up Markbook
    dataFile = ui.getMarksFile()
    dataImporter = DataImporter(dataFile)
    dataImporter.importData()
    markbook = dataImporter.createMarkBook()

    # Show details of markbook currently
    ui.printMarkbook(markbook)

    # Input the task to estimate
    student, task = ui.getTaskToEstimate(markbook)
    # student = 7
    # task = 2

    # Process the estimate
    dataProcessor = DataProcessor(markbook)
    rankEstimate = dataProcessor.estimateRank(student, task)
    markEstimate = dataProcessor.estimateMark(student, task)

    # Report on results
    ui.printEstimate(student, task, markEstimate, rankEstimate, markbook)


main()
