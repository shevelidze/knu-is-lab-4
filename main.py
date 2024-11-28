import sys
import json


class ScheduleCSP:
    def __init__(self, variables, domains, hard_constraints):
        self.variables = variables  # Variables (subject IDs)
        self.domains = domains  # Domains for each variable
        self.hard_constraints = hard_constraints  # Hard constraints
        self.assignments = {}  # Current schedule assignments

    def is_consistent(self, variable, value):
        """
        Check if assigning a value to a variable satisfies all constraints.
        """
        self.assignments[variable] = value
        for constraint in self.hard_constraints:
            if not constraint(self.assignments):
                del self.assignments[variable]
                return False
        del self.assignments[variable]
        return True

    def backtrack(self):
        """
        Backtracking search algorithm.
        """
        if len(self.assignments) == len(self.variables):
            return self.assignments  # Solution found

        unassigned = [v for v in self.variables if v not in self.assignments]
        variable = unassigned[0]  # Choose the first unassigned variable

        for value in self.domains[variable]:
            if self.is_consistent(variable, value):
                self.assignments[variable] = value
                result = self.backtrack()
                if result is not None:
                    return result
                del self.assignments[variable]  # Backtrack

        return None  # No solution found


# Hard constraint definitions
def unique_time_room(assignments):
    """
    Ensure no two events share the same time slot and room.
    """
    used_time_rooms = set()
    for value in assignments.values():
        time_room = (value["timeSlot"], value["room"])
        if time_room in used_time_rooms:
            return False
        used_time_rooms.add(time_room)
    return True


def unique_lecturer_time(assignments):
    """
    Ensure a lecturer cannot be scheduled for two events at the same time.
    """
    lecturer_time_slots = set()
    for value in assignments.values():
        time_lecturer = (value["timeSlot"], value["lecturer"])
        if time_lecturer in lecturer_time_slots:
            return False
        lecturer_time_slots.add(time_lecturer)
    return True


def unique_group_time(assignments, data):
    """
    Ensure no two events for the same group are scheduled at the same time.
    """
    group_time_slots = set()
    for (subject_id, _), value in assignments.items():
        # Find the group ID for the subject
        group_id = next(
            subject["groupId"]
            for subject in data["subjects"]
            if subject["id"] == subject_id
        )

        # Check time slot and group combination
        time_group = (value["timeSlot"], group_id)
        if time_group in group_time_slots:
            return False
        group_time_slots.add(time_group)
    return True


def find_solution(data):
    """
    Solve the scheduling problem using CSP.
    """
    # Create domains for each subject using IDs
    domains = {
        (subject["id"], subject_count): [
            {"timeSlot": timeSlot, "room": room["id"], "lecturer": lecturer["id"]}
            for timeSlot in data["timeSlots"]
            for room in data["rooms"]
            for lecturer in data["lecturers"]
            if lecturer["id"] in subject["suitedLecturers"]
            and room["capacity"]
            >= next(
                group["size"]
                for group in data["groups"]
                if group["id"] == subject["groupId"]
            )
        ]
        for subject in data["subjects"]
        for subject_count in range(subject["count"])
    }

    variables = [
        (subject["id"], subject_count)
        for subject in data["subjects"]
        for subject_count in range(subject["count"])
    ]

    # Define constraints
    hard_constraints = [
        unique_time_room,
        unique_lecturer_time,
        lambda assignments: unique_group_time(assignments, data),
    ]

    # Create the CSP instance
    schedule_csp = ScheduleCSP(variables, domains, hard_constraints)

    # Find a solution
    solution = schedule_csp.backtrack()

    return solution


def print_solution(solution, data):
    """
    Print the solution in a readable format.
    """
    for (subject_id, _), details in solution.items():
        subject = next(
            subject for subject in data["subjects"] if subject["id"] == subject_id
        )
        room = next(room for room in data["rooms"] if room["id"] == details["room"])
        lecturer = next(
            lecturer
            for lecturer in data["lecturers"]
            if lecturer["id"] == details["lecturer"]
        )

        print(
            f"Subject: {subject['name']}, Time Slot: {details['timeSlot']}, "
            f"Room: {room['name']}, Lecturer: {lecturer['name']}"
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    with open(input_file, "r") as file:
        data = json.load(file)

        solution = find_solution(data)

        if solution:
            print("Schedule Solution:")
            print_solution(solution, data)
        else:
            print("No solution found.")
