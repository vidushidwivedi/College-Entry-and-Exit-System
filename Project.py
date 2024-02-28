from collections import defaultdict
import random
import numpy as np
import simpy
import tkinter as tk

random.seed(42)
STUDENT_ARRIVAL_MEAN = 5
STUDENT_ON_GATE_MEAN= 100
STUDENT_ON_GATE_STD= 30
ARRIVALS = [random.expovariate(1 / STUDENT_ARRIVAL_MEAN) for _ in range(60)]
ON_BOARD = [int(random.gauss(STUDENT_ON_GATE_MEAN, STUDENT_ON_GATE_STD)) for _ in range(60)]
arrivals = defaultdict(lambda: 0)
punch_machine_wait = defaultdict(lambda: [])
guard_wait = defaultdict(lambda: [])
event_log = []
def register_arrivals(time, num): #This function updates the arrivals defaultDict with the new value of num for the key time
    arrivals[time] += num
def register_punch_machine_wait(time, wait):
    punch_machine_wait[time].append(wait)
def register_guard_wait(time, wait):
    guard_wait[time].append(wait)
def avg_wait(raw_waits):
    waits = [w for i in raw_waits.values() for w in i]
    return round(np.mean(waits), 1) if len(waits) > 0 else 0 #calculates the mean of waits using numpy library
def register_student_arrival(time, student_id, total_students):
    register_arrivals(time, len(total_students))
    event_log.append({
        "event": "STUDENT_ARRIVAL",
        "studentId": student_id,
        "time": round(time, 2), #rounds the time to 2 decimal places using round()
        "totalStudents": total_students
    })
def register_group_moving_to_punch_machine(students, walk_begin, walk_end, punch_line, queue_begin, queue_end,
                                             punch_begin, punch_end):

    wait = queue_end - queue_begin
    service_time = punch_end - punch_begin
    register_punch_machine_wait(queue_end, wait)
    event_log.append({
        "event": "WALK_TO_PUNCH_MACHINE",
        "students": students,
        "PunchLine": punch_line,
        "time": round(walk_begin, 2),
        "duration": round(walk_end - walk_begin, 2)
    })
    event_log.append({
        "event": "WAIT_IN_PUNCH_MACHINE_LINE",
        "students": students,
        "PunchLine": punch_line,
        "time": round(queue_begin, 2),
        "duration": round(queue_end - queue_begin, 2)
    })
    event_log.append({
        "event": "PUNCHING_STARTS",
        "students": students,
        "PunchLine": punch_line,
        "time": round(punch_begin, 2),
        "duration": round(punch_end - punch_begin, 2)
    })
def register_student_moving_to_guard(student, walk_begin, walk_end, guard_line, queue_begin, queue_end, guard_scanning_begin,
                                       guard_scanning_end):
    wait = queue_end - queue_begin
    service_time = guard_scanning_end - guard_scanning_begin
    register_guard_wait(queue_end, wait)
    event_log.append({
        "event": "WALK_TO_GUARD",
        "student": student,
        "guardLine": guard_line,
        "time": round(walk_begin, 2),
        "duration": round(walk_end - walk_begin, 2)
    })
    event_log.append({
        "event": "WAIT_IN_GUARD_LINE",
        "student": student,
        "guardLine": guard_line,
        "time": round(queue_begin, 2),
        "duration": round(queue_end - queue_begin, 2)
    })
    event_log.append({
        "event": "SCAN_STUDENTS",
        "student": student,
        "guardLine": guard_line,
        "time": round(guard_scanning_begin, 2),
        "duration": round(guard_scanning_end - guard_scanning_begin, 2)
    })

main = tk.Tk() #creates a new instance of the Tk class from the tkinter module, which is the main window of the application
main.title("College Gate Simulation")
main.config(bg="#fff")
top_frame = tk.Frame(main)
top_frame.pack(side=tk.TOP, expand=False)
canvas = tk.Canvas(main, width=1300, height=350, bg="light blue")
canvas.pack(side=tk.TOP, expand=False)
class QueueGraphics:
    text_height = 35
    icon_top_margin = -10

    def __init__(self, icon_file, icon_width, queue_name, num_lines, canvas, x_top, y_top):
        self.icon_file = icon_file
        self.icon_width = icon_width
        self.queue_name = queue_name
        self.num_lines = num_lines
        self.canvas = canvas
        self.x_top = x_top
        self.y_top = y_top
        self.image = tk.PhotoImage(file=self.icon_file)
        self.icons = defaultdict(lambda: [])
        for i in range(num_lines):
            canvas.create_text(x_top, y_top + (i * self.text_height), anchor=tk.NW, text=f"{queue_name} #{i + 1}")
        self.canvas.update()

    def add_to_line(self, punch_number):
        count = len(self.icons[punch_number])
        x = self.x_top + 60 + (count * self.icon_width)
        y = self.y_top + ((punch_number - 1) * self.text_height) + self.icon_top_margin
        self.icons[punch_number].append(
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.image)
        )
        self.canvas.update()
    def remove_from_line(self, punch_number):
        if len(self.icons[punch_number]) == 0: return
        to_del = self.icons[punch_number].pop()
        self.canvas.delete(to_del)
        self.canvas.update()

PUNCH_LINES = 3
def Punch(canvas, x_top, y_top):
    return QueueGraphics("C:/Users/vidus/PycharmProjects/pythonProject/pythonProject1/pw.png", 25, "Punch", PUNCH_LINES, canvas, x_top, y_top)

GUARD_LINES=2
def Guards(canvas, x_top, y_top):
    return QueueGraphics("C:/Users/vidus/PycharmProjects/pythonProject/pythonProject1/pw2.png", 18, "Guard", GUARD_LINES, canvas, x_top, y_top)
class studentLog:
    TEXT_HEIGHT = 30

    def __init__(self, canvas, x_top, y_top):
        self.canvas = canvas
        self.x_top = x_top
        self.y_top = y_top
        self.student_count = 0

    def next_student(self, minutes):
        x = self.x_top
        y = self.y_top + (self.student_count * self.TEXT_HEIGHT)
        self.canvas.create_text(x, y, anchor=tk.NW, text=f"Next student in {round(minutes, 1)} minutes")
        self.student_count = self.student_count + 1
        self.canvas.update()

    def student_arrived(self, students):
        x = self.x_top + 135
        y = self.y_top + (self.student_count * self.TEXT_HEIGHT)
        self.canvas.create_text(x, y, anchor=tk.NW, fill="green")
        self.student_count = self.student_count + 1
        self.canvas.update()
class ClockAndData:
    def __init__(self, canvas, x1, y1, x2, y2, time):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.canvas = canvas
        self.train = canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, fill="#fff")
        self.time = canvas.create_text(self.x1 + 10, self.y1 + 10, text="Time = " + str(round(time, 1)) + "m",
                                       anchor=tk.NW)
        self.punch_machine_waits = canvas.create_text(self.x1 + 10, self.y1 + 40,
                                                      text="Avg. Punch machine Wait  = " + str(
                                                          avg_wait(punch_machine_wait)), anchor=tk.NW)
        self.guard_waits = canvas.create_text(self.x1 + 10, self.y1 + 70,
                                              text="Avg. Scanner Wait = " + str(avg_wait(guard_wait)), anchor=tk.NW)
        self.canvas.update()

    def tick(self, time):
        self.canvas.delete(self.time)
        self.canvas.delete(self.punch_machine_waits)
        self.canvas.delete(self.guard_waits)
        self.time = canvas.create_text(self.x1 + 10, self.y1 + 10, text="Time = " + str(round(time, 1)) + "m",
                                       anchor=tk.NW)
        self.punch_machine_waits = canvas.create_text(self.x1 + 10, self.y1 + 30,
                                                      text="Avg. Punch Machine Wait  = " + str(
                                                          avg_wait(punch_machine_wait)) + "m",
                                                      anchor=tk.NW)
        self.guard_waits = canvas.create_text(self.x1 + 10, self.y1 + 50,
                                              text="Avg. Scanner Wait = " + str(avg_wait(guard_wait)) + "m",
                                              anchor=tk.NW)

student_log = studentLog(canvas, 5, 20)
punch = Punch(canvas, 340, 100)
guards = Guards(canvas, 770, 100)
clock = ClockAndData(canvas, 800, 260, 1290, 340, 0)
def pick_shortest(lines): #simulation started
    shuffled = list(zip(range(len(lines)), lines))  # tuples of (i, line)
    random.shuffle(shuffled)
    shortest = shuffled[0][0]
    for i, line in shuffled:
        if len(line.queue) < len(lines[shortest].queue):
            shortest = i
            break
    return (lines[shortest], shortest + 1)
def create_clock(env):
    while True:
        yield env.timeout(0.1)
        clock.tick(env.now)

TIME_TO_WALK_TO_PUNCH_MEAN = 1
TIME_TO_WALK_TO_PUNCH_STD = 0.25
TIME_TO_WALK_TO_GUARD_MEAN = 0.5
TIME_TO_WALK_TO_GUARD_STD = 0.1
def student_arrival(env, punch_lines, guard_lines):
    next_student_id = 0
    next_person_id = 0
    while True:
        next_student = ARRIVALS.pop()
        on_board = ON_BOARD.pop()
        student_log.next_student(next_student)
        yield env.timeout(next_student)
        student_log.student_arrived(on_board)
        students_ids = list(range(next_person_id, next_person_id + on_board)) #dikkattt
        register_student_arrival(env.now, next_student_id, students_ids)
        next_person_id += on_board
        next_student_id += 1

        STUDENT_RATIO_MEAN = 0.3
        STUDENT_GROUP_RATIO_MEAN = 2.25
        STUDENT_GROUP_RATIO_STD = 0.50
        while len(students_ids) > 0:
            remaining = len(students_ids)
            group_size = min(round(random.gauss(STUDENT_GROUP_RATIO_MEAN, STUDENT_GROUP_RATIO_STD)), remaining)
            people_processed = students_ids[-group_size:]  # Grab the last `group_size` elements
            students_ids = students_ids[:-group_size]  # Reset people_ids to only those remaining
            if random.random() > STUDENT_RATIO_MEAN:

                env.process(scanning_student(env, people_processed, guard_lines, TIME_TO_WALK_TO_PUNCH_MEAN + TIME_TO_WALK_TO_GUARD_MEAN, TIME_TO_WALK_TO_PUNCH_STD + TIME_TO_WALK_TO_GUARD_STD))
            else:
                env.process(punched_student(env, people_processed, punch_lines, guard_lines))
def punched_student(env, people_processed, punch_lines, guard_lines):
    walk_begin = env.now
    yield env.timeout(random.gauss(TIME_TO_WALK_TO_PUNCH_MEAN, TIME_TO_WALK_TO_PUNCH_STD))
    walk_end = env.now
    queue_begin = env.now
    punch_line = pick_shortest(punch_lines)
    with punch_line[0].request() as req:
        punch.add_to_line(punch_line[1])
        yield req
        punch.remove_from_line(punch_line[1])
        queue_end = env.now
        sale_begin = env.now
        yield env.timeout(random.gauss(PUNCH_MEAN, PUNCH_STD))
        sale_end = env.now
        register_group_moving_to_punch_machine(people_processed, walk_begin, walk_end, punch_line[1], queue_begin,
                                                 queue_end, sale_begin, sale_end)

        env.process(scanning_student(env, people_processed, guard_lines, TIME_TO_WALK_TO_GUARD_MEAN, TIME_TO_WALK_TO_GUARD_STD))

PUNCH_MACHINE_PER_LINE = 1
PUNCH_MEAN= 1
PUNCH_STD= 0.2

GUARD_PER_LINE = 1
GUARD_MEAN = 1/20 #time taken by guard to scan= 3 s
GUARD_STD = 0.01
def scanning_student(env, people_processed, guard_lines, walk_duration, walk_std, student=None):
    walk_begin = env.now
    yield env.timeout(random.gauss(walk_duration, walk_std))
    walk_end = env.now
    queue_begin = env.now
    guard_line = pick_shortest(guard_lines)
    with guard_line[0].request() as req:
        for _ in people_processed: guards.add_to_line(guard_line[1])
        yield req
        for _ in people_processed: guards.remove_from_line(guard_line[1])
        queue_end = env.now
        for student in people_processed:
            guard_scanning_begin = env.now
            yield env.timeout(random.gauss(GUARD_MEAN, GUARD_STD))  # Scan
            guard_scanning_end = env.now
            register_student_moving_to_guard(student, walk_begin, walk_end, guard_line[1], queue_begin, queue_end, guard_scanning_begin, guard_scanning_end)

env = simpy.Environment()
punch_lines = [simpy.Resource(env, capacity=PUNCH_MACHINE_PER_LINE) for _ in range(PUNCH_LINES)]
guard_lines = [simpy.Resource(env, capacity=GUARD_PER_LINE) for _ in range(GUARD_LINES)]
env.process(student_arrival(env, punch_lines, guard_lines))
env.process(create_clock(env))
env.run(until=40)
main.mainloop()