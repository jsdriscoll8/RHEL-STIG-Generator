import sqlite3
import os


# Script constants
AVAILABLE_CATEGORIES: list[str] = ["AUDIT", "ENCRYPTION", "DNS", "GUI", "IP", "LOGIN", "PACKAGE",
                                   "SESSION", "SSH", "LOGGING"]
GROUP_ID = 0
CATEGORY = 1
CAT_RATING = 2
FILE_PATH = 3


# Insert new fixes entries.
def main() -> int:
    cont = None
    
    while cont != 'n':
        cont = None
        while cont != 'n' and cont != 'y':
            cont = input("Would you like to insert additional fixes? y/n: ").lower().strip()
        
        if cont == 'y':
            # Gather a table entry, open connection and cursor.
            entry = gather_input()
            con = sqlite3.connect("fixes.db")
            cur = con.cursor()

            # Build, execute statement.
            insert_statement = ("INSERT INTO Fixes VALUES (?, ?, ?, ?);")
            insert_tuple = (entry[GROUP_ID], entry[CATEGORY], entry[CAT_RATING], entry[FILE_PATH])
            cur.execute(insert_statement, insert_tuple)

            # Close & commit cursor, connection. 
            cur.close()
            con.commit()
            con.close()
    
    # Test: print table.
    print_fixes_table()

    return 0 


# Gather the fix entry data.
def gather_input() -> list:
    query_parameters = list()

    # Gather cleaned parameters.
    # Group ID
    group_id = None
    while type(group_id) is not int:
        try:
            group_id = int(input("Enter the group ID of the fix: "))
        except ValueError:
            group_id = None
            print("Group ID must be an integer value; exclude any prefixes.")
    query_parameters.append(group_id)

    # Category
    category = None
    while category not in AVAILABLE_CATEGORIES:
        print("Available categories: ", *AVAILABLE_CATEGORIES)
        category = input("Enter the fix category: ").upper().strip()
        if category not in AVAILABLE_CATEGORIES:
            print("Ensure your category is one of the available options.")
    query_parameters.append(category)

    # CAT rating
    cat_rating = None
    while type(cat_rating) is not int:
        try:
            cat_rating = int(input("Enter the CAT rating (1-3): "))
            if cat_rating < 1 or cat_rating > 3:
                cat_rating = None
                print("CAT rating must be between 1 and 3.")
        except ValueError:
            group_id = None
            print("Group ID must be an integer value; exclude any prefixes.")
    query_parameters.append(cat_rating)

    # File path
    fix_file_path = "./files/" + input("Enter the fix file name; it must be in the ./files/ directory: ").strip()
    while not os.path.exists(fix_file_path):
        print("File not found. Correct the path, insert the file, or press Ctrl+C to abort.")
        fix_file_path = "./files/" + input("Enter the fix file name; it must be in the ./files/ directory: ").strip()
    query_parameters.append(fix_file_path)

    print("Entry: ", query_parameters)
    return query_parameters


# Testing function; prints entire table.
def print_fixes_table() -> None:
    con = sqlite3.connect("fixes.db")
    cur = con.cursor()

    cur.execute("SELECT * FROM Fixes")
    print("")
    for entry in cur.fetchall():
        print(entry)

    cur.close()
    con.close()


if __name__ == "__main__":
    main() 
