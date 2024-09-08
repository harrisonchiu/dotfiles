# Go to course history in Mosaic and copy and paste
raw_grades_text = """
"""

from enum import Enum

Grade = Enum("Grade", ["SCALE12", "SCALE4", "PERCENTAGE"])

grade_mapping = {
    "A+": {Grade.SCALE12: 12, Grade.SCALE4: 4},
    "A": {Grade.SCALE12: 11, Grade.SCALE4: 3.9},
    "A-": {Grade.SCALE12: 10, Grade.SCALE4: 3.7},
    "B+": {Grade.SCALE12: 9, Grade.SCALE4: 3.3},
    "B": {Grade.SCALE12: 8, Grade.SCALE4: 3},
    "B-": {Grade.SCALE12: 7, Grade.SCALE4: 2.7},
    "C+": {Grade.SCALE12: 6, Grade.SCALE4: 2.3},
    "C": {Grade.SCALE12: 5, Grade.SCALE4: 2},
    "C-": {Grade.SCALE12: 4, Grade.SCALE4: 1.7},
    "D+": {Grade.SCALE12: 3, Grade.SCALE4: 1.3},
    "D": {Grade.SCALE12: 2, Grade.SCALE4: 1},
    "D-": {Grade.SCALE12: 1, Grade.SCALE4: 0.7},
    "F": {Grade.SCALE12: 0, Grade.SCALE4: 0},
}


def main():
    total_units = 0
    total_grade_scale12 = 0
    total_grade_scale4 = 0
    for line in raw_grades_text.splitlines():
        if line in {"Taken", "Transferred", "In Progress"}:
            continue

        course = line.split("\t")

        # Error; something is wrong with input
        # Only lines less than 5 should be handled by first lines
        if len(course) < 5:
            print(course)
            continue

        # Calculate average: sum(grade * unit) / sum(units)
        course_code, course_name, term, grade, unit = course[:5]
        if grade in {"T", "COM", "NC", "W", " "} or not grade:
            continue
        unit = int(float(unit))

        total_grade_scale12 += grade_mapping[grade][Grade.SCALE12] * unit
        total_grade_scale4 += grade_mapping[grade][Grade.SCALE4] * unit
        total_units += unit

    # Calculate and display average
    scale12_average = total_grade_scale12 / total_units
    scale4_average = total_grade_scale4 / total_units

    print(f"Total grade points for 12 scale: {total_grade_scale12}")
    print(f"Total grade points for 4 scale: {total_grade_scale4}")
    print(f"Total units taken: {total_units}")
    print()
    print(f"12 scale average: {scale12_average}")
    print(f"4 scale average: {scale4_average}")


main()
