import sqlite3
from insert_new_fix import AVAILABLE_CATEGORIES, print_fixes_table
from typing import TypeAlias
from shutil import copyfileobj
from os import path, mkdir


# Configurator menu string constants
GREETING = ("\nHello and welcome to the RHEL STIG configurator!\n"
            "This program automatically generates an Ansible playbook to fix STIG findings based on your desired settings.\n"
            "You may select fixes via category, CAT rating, or group ID.\n"
            "Type --help to see this message again, --categories to see a list of available categories, or --list to see all fixes.\n"
            "Type 'c' to continue to the configurator, or 'q' to quit. ")
QUERY_DESC = ("\nBegin your query with CATEGORY, CAT_RATING, or GROUP_ID.\n"
              "Then, use the == operator to specify exact input, followed by a requested value. CAT_RATING queries may also use <, <=, >, >=.\n"
              "Example queries: CATEGORY = SSH | CAT_RATING < 3 | GROUP_ID = 258145 (without pipes.)\n")
QUERY_MENU = ("\nType a query to add the corresponding fixes to the playbook. Type 'q' to quit.\n"
                 "Alternatively, type --list to see all table entries, --lang for a query language description, or --categories to see category selection.")
DB_NAME = "fixes.db"
TEMPLATE_FILE = "./stig_template.yaml"  # Playbook start. Define hosts and configuration options here.


def main() -> int:  
       # Initialize tables, establish connection and cursor.
       initialize_tables()
       configurator()

       return 0

def print_categories() -> None:
    print("\nCategories: ", *AVAILABLE_CATEGORIES)


# Init the table of STIG fixes.
def initialize_tables() -> None:
    # Sqlite database connection and cursor, for making queries.
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    print("\nWelcome. Initializing table...")

    # Create fixes table
    cur.execute("""
                CREATE TABLE IF NOT EXISTS Fixes(
                group_id INTEGER PRIMARY KEY,
                category VARCHAR(25) NOT NULL,
                cat_rating INTEGER NOT NULL,
                file_path VARCHAR(50) NOT NULL,
                CHECK (cat_rating >= 1 AND cat_rating <= 3)
                );
                """)
    
    cur.close()
    con.commit()
    con.close()


# Generate a custom STIG configuration.
def configurator() -> None:
    VALID_MAIN_SELECTIONS = ['c', 'q', "--help", "--categories", "--list"]
    print(GREETING)
    selection = None
    
    # Main selection loop.
    while selection != 'q':
        match selection:
            case 'c':
                generate()
            case "--help":
                print(GREETING)
            case "--categories":
                print_categories()
            case "--list":
                print_fixes_table()

        selection = None
        while selection not in VALID_MAIN_SELECTIONS:
            selection = input("\nSelection: ").lower().strip()
            if selection not in VALID_MAIN_SELECTIONS:
                print("\nInvalid selection. Type 'c' to move to the configurator, or 'q' to quit. \n"
                  "Alternatively, type --help to see the welcome message again, --categories to see all available categories, or --list to see a list of all fixes.")
            elif selection == 'q':
                print("\nQuitting...")


# Handles config generation and writing to file.
def generate() -> None:
    # Constants for query typechecking.
    VALID_QUERY_SELECTIONS = ['q', "--categories", "--list", "--lang"]
    SELECTORS = ["cat_rating", "category", "group_id"]
    VALID_CAT_OPERATORS = ["=", "<", "<=", ">=", ">"] 
    VALID_FLAGS = ["--lang", "--categories", "--list"]
    SELECTOR = 0
    OPERATOR = 1
    VALUE = 2
    QUERY_LEN = 3

    # Filenames type - a list of filename strings.
    Filenames: TypeAlias = list[str]

    # List of all fixes for this configurator session; protects against duplicate plays. 
    playbook_fix_list: Filenames = []

    # Get a desired filename.
    def get_desired_output_path() -> str:
        file_path = None
        output_dir = "./playbook_output/"

        if not path.exists(output_dir):
            mkdir(output_dir)

        while file_path is None or path.exists(file_path):
            file_path = output_dir + input("\nEnter the desired output file name with no extension: ") + ".yaml"

            if path.exists(file_path):
                print("\nFile exists! Enter a different name.")
        
        open(file_path, 'x')  # Create this file
        # Copy the template to the destination to begin the playbook.
        with open(file_path, 'a') as destination:
            with open(TEMPLATE_FILE, 'r') as template:
                copyfileobj(template, destination)  # shutil method that copies whole file contents
        return file_path

    # Query language parser. Returns True upon a well-typed query, and False if the query is bad. 
    def parse_query(query: str) -> bool:
        query = query.split()

        # Query must have three parts: selector, operator, keyword.
        if len(query) != QUERY_LEN:
            print("\nImproperly typed query!")
            return False

        # Query must begin with CATEGORY, CAT_RATING, or GROUP_ID
        if query[SELECTOR] not in SELECTORS:
            print("\nInvalid selector! Choose from CATEGORY, GROUP_ID, and CAT_RATING.")
            return False
        
        # If a CATEGORY or GROUP_ID query, direct comparison is required.
        if query[SELECTOR] == "category" or query[SELECTOR] == "group_id":
            if query[OPERATOR] != "=":
                print(f"\n{query[SELECTOR].upper()} queries must use the = operator!")
                return False
        # If a CAT query, must be a valid numeric comparison operator.
        else:
            if query[OPERATOR] not in VALID_CAT_OPERATORS:
                print("\nCAT_RATING queries must use a valid numeric operator! ", *VALID_CAT_OPERATORS)
                return False
        
        # A CATEGORY query must reference a valid category.
        if query[SELECTOR] == "category":
            if query[VALUE].upper() not in AVAILABLE_CATEGORIES:
                print("\nInvalid category!")
                return False
        # CAT_RATING and GROUP_ID queries must reference integer data
        else:
            try:
                check_int = int(query[VALUE])
            except ValueError:
                print(f"{query[SELECTOR].upper()} queries must reference integer values!")
                return False

        # Valid query; return true.
        print("\nValid query! Loading results, excluding duplicates...")
        return True

    # Executes built SQL query, returns a list of file addresses.
    def execute_query(query: str) -> Filenames:
        # Split the query and convert the value to integer, if required.
        found_fixes: Filenames = []
        query = query.split()
        if query[SELECTOR] != "category":
            query[VALUE] = int(query[VALUE])
        
        # Build the SQL query
        sql_query = f"SELECT file_path FROM Fixes WHERE "

        # String values use the LIKE operator without percent signs for exact matches
        if query[SELECTOR] == "category":
            sql_query += f"{query[SELECTOR]} LIKE ?"
        else:
            sql_query += f"{query[SELECTOR]} {query[OPERATOR]} ?"

        # Connect to database
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()

        # Insert value, execute
        value_tuple = (query[VALUE],)
        
        cur.execute(sql_query, value_tuple)

        for entry in cur.fetchall():
            if entry[0] not in playbook_fix_list:  # Prevents duplicate plays
                found_fixes.append(entry[0])

        # Close connection, return found filenames
        cur.close()
        con.close()
        return found_fixes
    
    # Takes the requested fixes and appends them to a configuration file.
    def to_file(files_to_add: Filenames, dest_file: str) -> None:
        # Copy all fixes to the file.
        with open(dest_file, 'a') as destination:
            for f in files_to_add:
                with open(f, 'r') as fix:
                    copyfileobj(fix, destination)

        print(f"\nAdded all fixes to destination file {dest_file}!")   
        
    # --------------------------------------------------------- MAIN LOOP -------------------------------------
    output_path = get_desired_output_path()
    query = ""
    # Generation loop.
    while query != 'q':
        # Display info or execute query and write to file. 
        match query:
            case "--categories":
                print_categories()
            case "--list":
                print_fixes_table()
            case "--lang":
                print(QUERY_DESC)
        
        # Gather query input
        valid_query = False
        query = ""
        while query not in VALID_QUERY_SELECTIONS and not valid_query:
            print(QUERY_MENU)
            query = input("\nSelection: ").strip().lower()
            if query == 'q':
                print("\nExiting generator...")
            else:
                # If not a quit command or a flag, validate the query.
                if query not in VALID_FLAGS:
                    valid_query = parse_query(query)
                    
                    # If the query is valid, execute SQL that grabs list of fixes. 
                    if valid_query:
                        found_fixes = execute_query(query)
                        playbook_fix_list.extend(found_fixes)  # Add these fixes to the session list

                        for fix in found_fixes:
                            print(fix)  # Print the new fixes 
                        
                        to_file(found_fixes, output_path)  # Send these fixes to file


if __name__ == "__main__":
    main()
