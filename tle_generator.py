"""
Takes an ITU formatted Microsoft Database (.mdb) file with a single filing in it, and converts that filing to
a set of TLEs in a formatted text file.
"""

import datetime
import numpy as np
import math
import mdb_funcs as tle
import os
from skyfield.api import load
import pandas as pd
from scipy import constants as consts
from open_source_i_n import skyfield_funcs as sky_funcs
from open_source_i_n.utils import open_file_dialog
m_earth = 5.972e24
mu = consts.G * m_earth

# Set epoch of TLE
epoch_date = datetime.datetime(2021, 12, 1, 0, 0, 0) #y,m,d,h,m,s
spare_tles = 0  # number of spare tles per orbital plane (set to 0 if there are none)


def generate_tle(mdb_path, epoch_date):
    # pulls information from mdb file
    """
    Generates the TLE txt file based on a microsoft access database file (mdb) pulled from the ITU
    :param mdb_path: path to mdb file containing tle information
    :param epoch_date: Start date of the TLE epoch defined above
    :param tle_fname: Output file name for the TLE txt file
    """
    #Choose which tables to pull from the mdb file: orbit, phase, com_el
    sql = ["SELECT DISTINCT * FROM orbit", "SELECT DISTINCT * FROM phase", "SELECT DISTINCT * FROM com_el",
           "SELECT phase.*, orbit.* FROM orbit INNER JOIN phase ON (orbit.orb_id = phase.orb_id) AND (orbit.ntc_id = phase.ntc_id)"]

    # SQL commands to operate on the mdb

    # Run all the queries defined in sql variable on mdb store in dictionary db_dictionary, with keys Query 0, Query 1, Query 2
    opened_db = tle.open_database(mdb_path) # open mdb file
    dict_db = {"Query {}".format(sql.index(i)): tle.run_query_on_open_db(opened_db, i) for i in sql} #query the specified tables

    # Convert dictionary elements to numpy arrays
    orbit_data = np.array(dict_db["Query 0"][1])
    phase_data = np.array(dict_db["Query 1"][1])
    sat_el = np.array(dict_db["Query 2"][1])

    # # Dataframe objects for easier viewing in the debugger
    #orbit_pd = pd.DataFrame(orbit_data, columns=dict_db['Query 0'][0])
    #phase_pd = pd.DataFrame(phase_data, columns=dict_db['Query 1'][0])
    #sat_pd = pd.DataFrame(sat_el, columns=dict_db['Query 2'][0])

    # Join phase and orbit data tables
    orbit_and_phases = np.unique(phase_data[:, 1].astype(int), return_counts=True)
    orbits = orbit_and_phases[0]
    phases_per_orbit = orbit_and_phases[1]

    master_table = np.array([])

    #for each orbit/phase record
    #for orbit_id in range(len(orbits)):
    #    arr = np.repeat([orbit_data[orbits[orbit_id] - 1, :]], phases_per_orbit[orbit_id], 0)
    #    if not len(master_table):
    #        master_table = arr
    #    else:
    #        master_table = np.vstack((master_table, arr))
    #master_table_old = np.hstack((phase_data, master_table))
    master_table = sat_el = np.array(dict_db["Query 3"][1])

    #if(master_table_old != master_table):
    #    #THROW AN ERROR


    # master_table_pd = pd.DataFrame(master_table, columns=dict_db['Query 1'][0] + dict_db['Query 0'][0])

    # Generate title lines
    sys_name = sat_el[0, 5]
    title_lines = [f"{sys_name} Plane {row[1]} Sat {row[2]}" for row in master_table.tolist()]

    # Generate line 1's
    line_1s = []
    year_day_1 = datetime.datetime(epoch_date.year, 1, 1, 0, 0, 0)
    for i in range(len(master_table)):
        line_1 = [" "] * 69

        # Calculate line items
        sat_num = str(i+1).zfill(5)
        epoch_yr = str(epoch_date.year)[-2:]        # Last two digits of epoch year
        epoch_dy = (epoch_date - year_day_1).total_seconds() / 86400
        ep_dy_spl = str(epoch_dy).rsplit(".")
        launch_yr = epoch_yr
        launch_no = '1'
        launch_piece = 'A'
        elmt_set_no = '1'

        line_1[0] = '1'                 # Line number
        line_1[2:7] = sat_num           # Sat catalog number
        line_1[7:8] = 'U'                # Classification
        line_1[9:11] = launch_yr      # Int'l dsgntr (last 2 dgts lnch yr.)
        line_1[11:14] = launch_no.zfill(3)        # Int'l dsgntr (lnch no. of yr)
        line_1[14:17] = launch_piece.ljust(3, ' ')         # Int'l dsgntr (piece of lnch)
        line_1[18:20] = epoch_yr         # Epoch yr. (last two digits)
        line_1[20:32] = ep_dy_spl[0].rjust(3, ' ') + "." + ep_dy_spl[1].ljust(8, '0')[:8]         # Epoch (day of the year and fractional portion of the day)
        line_1[33:43] = "-.00000000"         # 1st deriv. of mean motion (ballistic coeff)
        line_1[44:52] = '000000-0'         # 2nd deriv. of mean motion (leading decimal pnt assumed)
        line_1[53:61] = '-00000-0'         # Drag term/Radiation Pressure coeff/Bstar (leading decimal pnt assumed)
        line_1[62:63] = '0'         # Ephemeris type (always 0)
        line_1[64:68] = elmt_set_no.rjust(4, '0')  # Element set number (incremented each time a new TLE is generated)

        # Final character is the checksum
        checksum = 0
        for char in line_1[:68]:
            if char.isnumeric():
                checksum += int(char)
            elif char == "-":
                checksum += 1
        line_1[68] = str(checksum % 10)

        # Combine list into single string
        line_1_str = "".join(line_1)
        line_1s.append(line_1_str)


    # Generate line 2's
    line_2s = []
    for i in range(len(master_table)):
        line_2 = [" "] * 69

        # Calculate eccentricity
        peri = master_table[i, 17] * np.power(10, master_table[i, 18])
        apo = master_table[i, 15] * np.power(10, master_table[i, 16])
        semi_ma = (peri + apo) / 2 # calculate semimajor axis of orbit
        ecc = (apo / semi_ma) - 1 # calculate orbital eccentricity

        # Calculate other line items
        sat_num = str(i+1).zfill(5)
        inc = master_table[i, 11]
        raan = master_table[i, 10]
        arg_p = master_table[i, 19]
        mn_ano = master_table[i, 3]
        if float(mn_ano) < 0.0: mn_ano = str(360.0 + float(mn_ano))
        mn_mot = sky_funcs.calc_period_from_alt(peri, apo, mode='rev/day')      # Revolutions per day
        rev_no = 1

        # Some variables must be split at the decimal to calculate padding correctly
        ecc_spl = str(ecc).rsplit(".")
        inc_spl = str(inc).rsplit(".")
        raan_spl = str(raan).rsplit(".")
        arg_p_spl = str(arg_p).rsplit(".")
        mn_ano_spl = str(mn_ano).rsplit(".")
        mn_mot_spl = str(mn_mot).rsplit(".")

        line_2[0] = '2'                                                                 # Line number
        line_2[2:7] = sat_num                                                           # Sat catalog number
        line_2[8:16] = inc_spl[0].rjust(3, ' ') + "." + inc_spl[1].ljust(4, '0')[:4]         # Inclination (deg)
        line_2[17:25] = raan_spl[0].zfill(3) + "." + raan_spl[1].ljust(4, '0')[:4]      # RAAN (deg)
        line_2[26:33] = ecc_spl[1].ljust(7, '0')                                       # Eccentricity (leading dec pnt assumed)
        line_2[34:42] = arg_p_spl[0].zfill(3) + "." + arg_p_spl[1].ljust(4, '0')[:4]         # Arg of perigee (deg)
        line_2[43:51] = mn_ano_spl[0].zfill(3) + "." + mn_ano_spl[1].ljust(4, '0')[:4]         # Mean anomaly (deg)
        line_2[52:63] = mn_mot_spl[0].zfill(2) + "." + mn_mot_spl[1].ljust(8, '0')[:8]         # Mean motion (rev/day)
        line_2[63:68] = str(rev_no).rjust(5, '0')         # Rev number @ epoch (revs)

        # Final character is the checksum
        checksum = 0
        for char in line_2[:68]:
            if char.isnumeric():
                checksum += int(char)
            elif char == "-":
                checksum += 1
        line_2[68] = str(checksum % 10)

        # Combine list into single string
        line_2_str = "".join(line_2)
        line_2s.append(line_2_str)


    # Write to file
    f_name = f"TLEs_{sys_name}.txt"
    with open(f"TLEs_{sys_name}.txt", 'w') as f:
        for i in range(len(master_table)):
            f.write(title_lines[i]+"\n")
            f.write(line_1s[i]+"\n")
            f.write(line_2s[i]+"\n")

    return f_name


if __name__ == '__main__':
    mdb_path = open_file_dialog(os.getcwd(), file_types=[('Microsoft Access databases', '.mdb')])
    tle_fname = generate_tle(mdb_path, epoch_date)
    tle_check = load.tle_file(tle_fname) # checks that skyfield can load in the TLE correctly
