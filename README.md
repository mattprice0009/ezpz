# ezpz


## **Requirements**
* Python 3 installed
* There are currently no additional install requirements.

---

## **NOTES**:
* When I reference a variable in all caps (e.g. `MAIN_RAID_GROUP`), those are referring to variables defined and used in `generate_raider_csv.py`.
* Ideal TODOs:
  1. Move the output target of this into a cloud sheet (e.g. Google Sheets) that automatically applies formatting/filtering.
  2. Automate the retrieval of the TMB JSON export (probably can be easily done by calling an endpoint or hitting the Download button with a web crawler).
  3. Figure out a good way to automate the current raid, instead of relying on Guldamn to generate the list and post in Discord.
  4. Get other LC members to actually learn what the stats in here are, and get them to actually use this. Then, we can improve some of the stats and add a few more.
      * For example, it would be great to add "number of raids over last 6 weeks", since we currently only see "number of raids total".

---

## **Generating raider loot stats**
To generate raider loot statistics using `generate_raider_csv.py`, perform the following steps:

### **Prerequisites**
1. Make sure all raiders of interest are members of the `MAIN_RAID_GROUP` raid group in TMB.
    * This can be done at https://thatsmybis.com/8953/ez-pz/raid-groups/10584/characters/general
2. Make sure all loot is imported into TMB.

### **Manual steps needed per run**
1. Export TMB json blob
    * From https://thatsmybis.com/8953/ez-pz/export
    * Download the "Giant JSON Blob"
    * Move to `ezpz/source_data`, rename, and set as the `TMB_JSON_EXPORT_FP` in the code.
2. If you want to be able to use the `"_focus"` filter (useful for applying a quick filter to filter to a specified list of raiders), get the roster list from Guldamn (he usually posts it hours before raid time). Paste it into the path specified in `CURRENT_RAID_FP`.

### **Running the script**
1. To run the script, just run `python generate_raider_csv.py`.
    * TODO: Move the inputs into CLI args so that we can specify input/output files in the command, rather than needing to modify actual code.

### **Using the output**
1. The script will output results to the path specified in `OUTPUT_FP`.
2. I created a formatted .xlsm file for a visually appealing way to use the output data. You can copy the contents of `OUTPUT_FP` and paste into `Raider Data Formatted.xlsm` (paste values only, do not overwrite formatting).
3. To filter the results down to the current raids' players only, filter by the "Focus" column ("Focus" === TRUE).

