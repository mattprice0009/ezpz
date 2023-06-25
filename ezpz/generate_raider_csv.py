import csv
import json
import re
import traceback
from datetime import datetime, timedelta
"""
TODO:
- add "last loot date"
- add performance metrics (parses, etc.)
- iterate on generalization (easy)
"""

# TODO: Move to constants file
MAIN_RAID_GROUP = 'Attendance'
OUTPUT_FP = 'raider_data.csv'
# June 22, 2023 was TOGC release date
TOGC_START_DATE = datetime(2023, 6, 22)
# Jan 19, 2023 was ulduar release date
ULDUAR_START_DATE = datetime(2023, 1, 19)
IGNORE_PREVIOUS_PHASES = True
NUM_DAYS_LOOT_IS_RECENT = 30
TMB_JSON_EXPORT_FP = 'source_data/tmb_export_20230625.json'
CURRENT_RAID_FP = 'source_data/current_raid.csv'


# TODO: Move to constants file
class Keys:
  ACTIVE = '_is_active'
  ARCHETYPE = 'archetype'
  ATTENDANCE_PERCENT = 'attendance_percentage'
  CLASS = 'class'
  NAME = 'name'
  NUM_RAIDS = 'raid_count'
  SPEC = 'display_spec'
  USERNAME = 'member_slug'

  LOOT_TOTAL = '_loot_total'
  BIS_TOTAL = '_bis_total'
  UPGRADES_TOTAL = '_upgrade_total'
  OS_TOTAL = '_offspec_total'

  LOOT_RECENTLY = f'_loot_last_{NUM_DAYS_LOOT_IS_RECENT}_days'
  BIS_RECENTLY = f'_bis_last_{NUM_DAYS_LOOT_IS_RECENT}_days'
  MS_RECENTLY = f'_ms_last_{NUM_DAYS_LOOT_IS_RECENT}_days'

  LOOT_PER_RAID = '_loot_per_raid'
  BIS_PER_RAID = '_bis_per_raid'
  MS_PER_RAID = '_ms_per_raid'

  PRIOS_RECEIVED = '_prios_received'
  PRIOS_CURRENT = '_prios_active'
  PRIOS_CURRENT_LIST = '_prios_active_list'

  WISHLIST_RECIEVED = '_wishlist_received'
  WISHLIST_PERCENT = '_wishlist_completion_percent'
  WISHLIST_LIST = '_wishlist_list'

  BIS_LIST = '_bis_list'

  IS_OF_INTEREST = '_focus'


# TODO: Move to constants file
class RC_VAL_SUBSTRINGS:
  BIS = 'bis'
  OS = 'offspec'
  UPGRADE = 'upgrade'


# TODO: Move to constants file
GENERAL_KEYS = [
  Keys.NAME,
  Keys.USERNAME,
  Keys.CLASS,
  # Keys.SPEC,
  Keys.ARCHETYPE,
  Keys.NUM_RAIDS,
  Keys.ATTENDANCE_PERCENT,
  Keys.IS_OF_INTEREST,
]

# TODO: Move to constants file
LOOT_KEYS = [
  Keys.LOOT_TOTAL, Keys.BIS_TOTAL, Keys.UPGRADES_TOTAL, Keys.OS_TOTAL, Keys.LOOT_RECENTLY,
  Keys.BIS_RECENTLY, Keys.MS_RECENTLY, Keys.LOOT_PER_RAID, Keys.BIS_PER_RAID,
  Keys.MS_PER_RAID, Keys.BIS_LIST
]

# TODO: Move to constants file
PRIO_KEYS = [Keys.PRIOS_RECEIVED, Keys.PRIOS_CURRENT, Keys.PRIOS_CURRENT_LIST]

# TODO: Move to constants file
WISHLIST_KEYS = [Keys.WISHLIST_RECIEVED, Keys.WISHLIST_PERCENT, Keys.WISHLIST_LIST]


class RaiderDataHandler():

  def __init__(self):
    self.current_raiders = set()
    with open(CURRENT_RAID_FP, 'r') as reader:
      for row in reader:
        self.current_raiders.add(row.strip().lower())
    self.current_raiders_loaded = set()

  def _format_cell_value_for_list(self, list_val):
    delim = '\n'
    return f'"{delim.join(list_val)}"'

  def _format_csv_row(self, row):
    return ','.join([str(s) for s in row]) + '\n'

  def _get_loot_date(self, loot):
    return datetime.strptime(loot['pivot']['received_at'].split(' ')[0], '%Y-%m-%d')

  def _get_loot_quality(self, loot):
    try:
      if not loot['pivot']['officer_note']:
        return None
      regex_res = re.findall(r'"(.+?)"', loot['pivot']['officer_note'].lower())
      loot_note = regex_res[0]
      for k in [RC_VAL_SUBSTRINGS.BIS, RC_VAL_SUBSTRINGS.OS, RC_VAL_SUBSTRINGS.UPGRADE]:
        if k in loot_note:
          return k
    except:
      print(json.dumps(loot, sort_keys=True, indent=2, default=str))
      print(traceback.format_exc())
      return None  # TODO: Handle these exceptions instead of allowing
      raise RuntimeError('damn')

  def _is_loot_recent(self, loot_date):
    earliest_recent_date = datetime.strptime(
      (datetime.today() -
       timedelta(NUM_DAYS_LOOT_IS_RECENT)).date().isoformat().replace('-',
                                                                      ' '), '%Y %m %d'
    )
    return loot_date >= earliest_recent_date

  def _set_initial_vals(self, raider, keys):
    for k in keys:
      if '_list' in k:
        raider[k] = []
      else:
        raider[k] = 0

  def is_active_raider(self, raider):
    return any(
      raid_group['name'] == MAIN_RAID_GROUP
      for raid_group in raider['secondary_raid_groups']
    )

  def read_tmb_json(self, filename):
    raiders = []
    with open(filename, 'r') as reader:
      data = json.load(reader)
      for raider in data:
        raider[Keys.ACTIVE] = self.is_active_raider(raider)
        raiders.append(raider)
    return raiders

  def filter_raiders(self, raiders):
    return [ raider for raider in raiders if raider[Keys.ACTIVE] ]

  def set_loot_history_for_raider(self, raider):
    self._set_initial_vals(raider, LOOT_KEYS)
    for loot in raider['received']:
      loot_date = self._get_loot_date(loot)
      loot_quality = self._get_loot_quality(loot)
      loot_is_recent = self._is_loot_recent(loot_date)
      if not loot_quality:
        # Ignore PVP gear or null officer notes
        # TODO: If we wanna add it here, check out the note when loot_quality
        # is null.
        continue
      if IGNORE_PREVIOUS_PHASES and loot_date < TOGC_START_DATE:
        # This loot was won before current phase
        continue
      raider[Keys.LOOT_TOTAL] += 1
      if loot_is_recent:
        raider[Keys.LOOT_RECENTLY] += 1
      if loot_quality == RC_VAL_SUBSTRINGS.BIS:
        raider[Keys.BIS_LIST].append(loot['name'])
        if loot_is_recent:
          raider[Keys.BIS_RECENTLY] += 1
      if loot_quality in [RC_VAL_SUBSTRINGS.BIS, RC_VAL_SUBSTRINGS.UPGRADE
                          ] and loot_is_recent:
        raider[Keys.MS_RECENTLY] += 1
      qual_key = f'_{loot_quality}_total'
      raider[qual_key] += 1
    # Generate per raid numbers
    if raider[Keys.NUM_RAIDS] > 0:
      raider[Keys.LOOT_PER_RAID
             ] = round(float(raider[Keys.LOOT_TOTAL]) / float(raider[Keys.NUM_RAIDS]), 4)
      raider[Keys.BIS_PER_RAID
             ] = round(float(raider[Keys.BIS_TOTAL]) / float(raider[Keys.NUM_RAIDS]), 4)
      mainspec_total = raider[Keys.BIS_TOTAL] + raider[Keys.UPGRADES_TOTAL]
      raider[Keys.MS_PER_RAID
             ] = round(float(mainspec_total) / float(raider[Keys.NUM_RAIDS]), 4)
    raider[Keys.BIS_LIST] = self._format_cell_value_for_list(raider[Keys.BIS_LIST])

  def set_prio_fields_for_raider(self, raider):
    self._set_initial_vals(raider, PRIO_KEYS)
    for prio in raider['prios']:
      if prio['pivot']['is_received'] == 1:
        raider[Keys.PRIOS_RECEIVED] += 1
      else:
        raider[Keys.PRIOS_CURRENT] += 1
        raider[Keys.PRIOS_CURRENT_LIST].append(prio['name'])
    raider[Keys.PRIOS_CURRENT_LIST
           ] = self._format_cell_value_for_list(raider[Keys.PRIOS_CURRENT_LIST])

  def set_wishlist_fields_for_raider(self, raider):
    self._set_initial_vals(raider, WISHLIST_KEYS)
    num_wishlist = 0
    for wishlist in raider['wishlist']:
      num_wishlist += 1
      if wishlist['pivot']['is_received'] == 1:

        raider[Keys.WISHLIST_RECIEVED] += 1
      else:
        raider[Keys.WISHLIST_LIST].append(wishlist['name'])
    if num_wishlist > 0:
      raider[Keys.WISHLIST_PERCENT
             ] = round(float(raider[Keys.WISHLIST_RECIEVED]) / float(num_wishlist), 4)
    raider[Keys.WISHLIST_LIST
           ] = self._format_cell_value_for_list(raider[Keys.WISHLIST_LIST])

  def generate_output(self, raiders):
    rows = []
    header_row = GENERAL_KEYS + LOOT_KEYS + PRIO_KEYS + WISHLIST_KEYS
    for raider in raiders:
      row = []
      # Set loot history values for the raider
      self.set_loot_history_for_raider(raider)
      raider[Keys.IS_OF_INTEREST] = raider[Keys.NAME].lower() in self.current_raiders
      # Set prios values for raider
      self.set_prio_fields_for_raider(raider)
      # Set wishlist values for raider
      self.set_wishlist_fields_for_raider(raider)
      # Assign flag for current raid roster
      if raider[Keys.IS_OF_INTEREST]:
        self.current_raiders_loaded.add(raider[Keys.NAME].lower())
      for k in header_row:
        row.append(raider[k])
      rows.append(row)

    # Write output
    with open(OUTPUT_FP, 'w') as writer:
      writer.write(
        self._format_csv_row([s.replace('_', ' ').title().strip() for s in header_row])
      )
      for row in rows:
        writer.write(self._format_csv_row(row))
    return rows

  def ProcessExport(self, export_fp):
    """
      1. Reads TMB JSON (export from TMB)
      2. Filters out irrelevant raiders
      3. Generates CSV and saves to local file
    """
    all_raiders = self.read_tmb_json(export_fp)
    active_raiders = self.filter_raiders(all_raiders)
    self.generate_output(active_raiders)
    for curr_raider in self.current_raiders:
      if curr_raider not in self.current_raiders_loaded:
        print(f'"{curr_raider}" missing')


if __name__ == '__main__':

  handler = RaiderDataHandler()
  handler.ProcessExport(TMB_JSON_EXPORT_FP)
