# tle_generator
Generate a text file of Two Line Elements (TLEs) from an ITU filing database (.mdb)

Instructions:
At present, the ITU IFIC database MUST CONTAIN ONLY A SINGLE FILING IN IT. 

If you have an ITU account, you can use the Space Network List (Part-B, https://www.itu.int/net/ITU-R/space/snl/bsearchb/spublication.asp) to download a singular filing. Simply search the name of the system of interest, click its notification ID, and select DOWNLOAD. 

When the TLE generator script is run, it will prompt you to select a database. Simply select the downloaded .mdb file.


*Note* Several simplifications are made by the generator (e.g. drag and ballistic coefficients are set to zero by default). 
