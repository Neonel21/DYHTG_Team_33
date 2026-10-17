from config import STUDENT_COLOURS, SUBJECTS

def colour_code_students(id, students, colour_flag):
    if colour_flag == "none":
            return STUDENT_COLOURS[0]
    
    student = students[students["Student ID"] == id]
    if student.empty:
        return STUDENT_COLOURS[0]
    student = student.iloc[0]

    if colour_flag == "year":
        year_of_study = student["Year of Study"]
        colour = STUDENT_COLOURS[int(year_of_study)]
        return colour
    
    if colour_flag == "subject":
        subject = student["Subject"]
        if subject in SUBJECTS:
            i = SUBJECTS.index(subject)
        else:
            i = 30
        return STUDENT_COLOURS[i]

    return STUDENT_COLOURS[0]