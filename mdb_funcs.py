import pyodbc
debug = False


# OPEN/CLOSE DATABASES
def open_database(file_path):
    bitness = check_sys_prerequisites()

    # Set connection string, depending on the bitness.
    if bitness == "32bit":
        conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb)};'r'DBQ=' + file_path + ';')
    else:
        conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'r'DBQ=' + file_path + ';')

    # Connect to the MS Access database, specified by the filepath
    try:
        cnxn = pyodbc.connect(conn_str)
        print("Connected. \t", file_path.split("\\")[-1])
    except pyodbc.Error:
        print(".mdb not found at {} \n\nPress return key to close.".format(file_path))
        input()
        return None  # TODO temp, remove later maybe
    debug_print(conn_str)

    return cnxn


def close_database(database):
    # Close the MS Access database
    debug_print("Closing MS Access database.")
    database.commit()
    database.close()
    debug_print("Access database closed.")


def check_sys_prerequisites():
    from platform import architecture
    from sys import stderr
    bitness = architecture()[0]
    jet = False
    ace = False
    driver_install_guide = """
            Go here and download the Microsoft Access driver using whichever bitness matches your Python install.
            https://www.microsoft.com/en-us/download/details.aspx?id=54920
            If the installer gives you trouble about conflicting with your current Microsoft install, do the following:
            Win+R to open the Run dialog
            Browse to the downloaded accessdatabaseengine.exe and select it
            Add /quiet to that (outside of any quote marks if the appear), e.g.
            "C:\\temp\\accessdatabaseengine.exe" /quiet
            """

    # Check for drivers
    driver_list = pyodbc.drivers()
    if driver_list.__contains__('Microsoft Access Driver (*.mdb)'):
        debug_print("Jet driver detected")
        jet = True
    else:
        debug_print("Jet driver NOT detected.")
    if driver_list.__contains__('Microsoft Access Driver (*.mdb, *.accdb)'):
        debug_print("ACE driver detected.")
        ace = True
    else:
        debug_print("ACE driver NOT detected.")

    # Error messages
    if bitness == "32bit" and jet is False:
        print("Error: Your Python install is 32-bit and you are missing the 32-bit Jet MS Access driver. You must "
              "install the appropriate driver(s) otherwise Python may be unable to find or open database files.",
              file=stderr)
        print(driver_install_guide)
    elif bitness == "64bit" and ace is False:
        print("Error. Your Python install is 64-bit and you are missing the 64-bit ACE MS Access driver. You must "
              "install the appropriate driver(s) otherwise Python may be unable to find or open database files.",
              file=stderr)
        print("Is Jet installed?", jet)
        print("Is ACE installed?", ace)
        print("\n", driver_install_guide)
    else:
        debug_print("Your system is % and the appropriate drivers are installed." % bitness)

    return bitness


# EXECUTE QUERIES
def open_and_run_query_on_db(db_path, query, input_array=None):
    db = open_database(db_path)
    crsr = db.cursor()  # Defines a 'cursor' object that can be directed to move throughout the MS Access database to read specific information.
    if input_array:
        crsr.execute(query, input_array)
    else:
        crsr.execute(query)
    rows = crsr.fetchall()
    close_database(db)
    return rows


def run_query_on_open_db(db_object, query, input_array=None):
    crsr = db_object.cursor()  # Defines a 'cursor' object that can be directed to move throughout the MS Access database to read specific information.
    if input_array:
        crsr.execute(query, input_array)
    else:
        crsr.execute(query)
    rows = crsr.fetchall()
    columns = [column[0] for column in crsr.description]
    return [columns, rows]


# CURSOR
def print_cursor_rows(cursor):
    rows = cursor.fetchall()  # Store the information in an array so it may be read
    for row in rows:
        print(row)


def print_cursor_tables(cursor):
    for table_info in cursor.tables(tableType='TABLE'):
        print(table_info.table_name)


# UTILITY
def debug_print(string):
    if debug: print(string)
