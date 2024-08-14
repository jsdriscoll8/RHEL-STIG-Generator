import sqlite3
from insert_new_fix import print_fixes_table, AVAILABLE_CATEGORIES
from typing import TypeAlias


# Script constants. 
DEL_QUERY_LEN = 2
MOD_QUERY_LEN = 5
QUERY_OP = 0
QUERY_GROUPID = 1
QUERY_SELECTOR = 2
QUERY_EQUALS = 3
QUERY_VALUE = 4

LANG_DESC = ("\nBegin your query with DEL or MOD."
              "\nNext, type the group ID of the tag you wish to modify or delete."
              "\nFor MOD queries, select the property to modify: CATEGORY or CAT_RATING."
              "\nFinish a MOD query with = [value], without the brackets."
              "\nExample queries: DEL 123456 | MOD 987654 TAG = SSH without pipes.")
BASE_DEL_QUERY = ("DELETE FROM Fixes WHERE group_id = ?;")
BEGIN_MOD_QUERY = ("UPDATE Fixes SET")
END_MOD_QUERY = ("= ? WHERE group_id = ?;")

VALID_FLAGS: list[str] = ["--lang", "--categories", "--list"]
SELECTORS: list[str] = ["category", "cat_rating"]

Query: TypeAlias = list[str]


# Delete or modify entries.
def main() -> int:
    # Print the main 
    def print_query_lang() -> None: 
        print("\nType --lang to see a query language description, --categories to see a list of categories, or --list to see a complete list of entries.")
    
    # Handle flag output.
    def flags(flag: str) -> None:
        match flag:
            case "--lang":
                print(LANG_DESC)
            case "--categories":
                print(AVAILABLE_CATEGORIES)
            case "--list":
                print_fixes_table()
    
    # Main loop
    cont = None
    while cont != 'n':
        # Get continue confirmation
        while cont != 'n' and cont != 'y':
            cont = input("\nWould you like to delete or modify additional fixes? y/n: ").lower().strip()

            if cont != 'n' and cont != 'y':
                print("\nInvalid choice.")
        
        # Get modification or deletion choice, continue.
        if cont != 'n':
            print_query_lang()
            query = input("Type your query here: ").lower().strip()

            # Proceed with query processing.
            if query not in VALID_FLAGS:
                query = query.split()
                if len(query) < 1:
                    print("\nInvalid query!")
                
                # Read the query operation. Execute query if well-typed. 
                else:
                    match query[QUERY_OP]:
                        case "mod":
                            if parse_mod_query(query):
                               execute_mod_query(query)
                        case "del":
                            if parse_del_query(query):
                                execute_del_query(query)
                        case _:
                            print("\nQueries must begin with DEL or MOD!")

            # Or print a flag. Reset cont. 
            else:
                flags(query)
            cont = None
    
    print("\nExiting...")
    return 0


# Parse a delete query.
def parse_del_query(query: Query) -> bool:
    # Del query must have only "DEL" and a group ID.
    if len(query) != DEL_QUERY_LEN:
        print("\nToo many or too few arguments!")
        return False
    
    # Group ID must be an integer that exists in the table.
    return check_group_id(query[QUERY_GROUPID])


# Execute a delete query.
def execute_del_query(query: Query) -> None:
    # Build the initial query, tuple; connect to database & cursor. 
    del_query = BASE_DEL_QUERY
    del_tuple = (query[QUERY_GROUPID],)
    con = sqlite3.connect("fixes.db")
    cur = con.cursor()

    # Execute query.
    cur.execute(del_query, del_tuple)
    print(f"\nDeleted fix with group ID {query[QUERY_GROUPID]}!")

    # Commit & close.
    cur.close()
    con.commit()
    con.close()


# Parse a mod query.
def parse_mod_query(query: Query) -> bool:
    # Mod query must have "MOD", group ID, column to modify, '=', and the modification value.
    if len(query) != MOD_QUERY_LEN:
        print("\nToo many or few arguments!")
        return False
    
    # Group ID must be an integer that exists in the table.
    if not check_group_id(query[QUERY_GROUPID]):
        return False
    
    # Desired modification must be a category or CAT rating.
    if(query[QUERY_SELECTOR]) not in SELECTORS:
        print("\nDesired column does not exist! Select from CATEGORY or CAT_RATING.")
        return False

    # Equals sign required, for consistency with config_generator.
    if(query[QUERY_EQUALS] != '='):
        print("\nQuery is not well typed!")
        return False
    
    # Verify query value based on the selected column.
    match query[QUERY_SELECTOR]:
        # Cat ratings must be integers.
        case "cat_rating":
            try:
                query[QUERY_VALUE] = int(query[QUERY_VALUE])
                
                # CAT ratings must be between 1 and 3.
                if query[QUERY_VALUE] < 1 or query[QUERY_VALUE] > 3:
                    print("\nCAT rating must be an integer between 1 and 3!")
                    return False
            except ValueError:
                print("\nCAT rating must be an integer between 1 and 3!")
                return False
        
        # Available categories are predetermined.
        case "category":
            if query[QUERY_VALUE].upper() not in AVAILABLE_CATEGORIES:
                print("\nValue is not a valid category! See --categories for all options.")
                return False
    
    # All parts of query good.
    return True


# Execute a modify query.
def execute_mod_query(query: Query) -> None:
    # Fix case issues.
    if query[QUERY_SELECTOR] == "category":
        query[QUERY_VALUE] = query[QUERY_VALUE].upper()

    # Build the initial query, tuple; connect to database & cursor. 
    mod_query = BEGIN_MOD_QUERY + f" {query[QUERY_SELECTOR]} " + END_MOD_QUERY
    mod_tuple = (query[QUERY_VALUE], query[QUERY_GROUPID])
    con = sqlite3.connect("fixes.db")
    cur = con.cursor()

    # Execute query.
    cur.execute(mod_query, mod_tuple)
    print(f"\nUpdated query with group ID {query[QUERY_GROUPID]}: {query[QUERY_SELECTOR]} set to {query[QUERY_VALUE]}!")

    # Commit & close.
    cur.close()
    con.commit()
    con.close()


def check_group_id(init_id: str) -> bool:
    # Group ID must be an integer.
    try:
        init_id = int(init_id)
        
        # Group ID must exist.
        if not verify_entry(init_id):
            return False

    except ValueError:
        print("\nGroup ID must be an integer!")
        return False
    
    return True

    
# Verify that a requested entry exists.
def verify_entry(group_id: int) -> bool:
    entry_found = False

    # Connect to db. 
    con = sqlite3.connect("fixes.db")
    cur = con.cursor()

    # Build query
    verify_query = "SELECT file_path FROM Fixes WHERE group_id = ?"
    group_id_tup = (group_id,)
    cur.execute(verify_query, group_id_tup)

    if len(cur.fetchall()) < 1:
        print("\nEntered group ID not found in table!")
    else:
        entry_found = True

    # Commit and close. 
    cur.close()
    con.commit()
    con.close()
    return entry_found


if __name__ == "__main__":
    main() 
