import os
import sys
import csv
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# ensure repository root is on sys.path so `from App ...` imports work
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASSWORD", "db_pass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "wdi_project")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'Data')




def _clean_val(v):
    if v is None:
        return None
    v = str(v).strip()
    if v == '' or v == '\\N':
        return None
    # remove surrounding quotes if present
    if v.startswith('"') and v.endswith('"'):
        v = v[1:-1]
    # try numeric conversion
    try:
        if '.' in v:
            return float(v)
        return int(v)
    except Exception:
        try:
            return float(v)
        except Exception:
            return v


def load_csv_to_table(csv_path, table_name, column_order=None, dedupe_key=None, id_map=None, id_map_col=None, unique_cols=None, conn=None):
    rows = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # normalize keys to match DB columns (strip spaces)
            row = {}
            for k, v in r.items():
                key = k.strip()
                key = key.replace(' ', '_') if ' ' in key and key.lower().endswith('_id') else key
                row[key] = _clean_val(v)
            if column_order:
                filtered = {col: row.get(col) for col in column_order}
            else:
                filtered = row
            if id_map and id_map_col and id_map_col in filtered:
                original = filtered.get(id_map_col)
                if original in id_map:
                    filtered[id_map_col] = id_map[original]
            rows.append(filtered)

    if not rows:
        print(f"No rows found in {csv_path}")
        return {}

    # optionally deduplicate rows by a key (useful for indicator detail tables)
    id_mapping_result = {}
    if dedupe_key:
        seen = {}
        deduped = []
        id_col = column_order[0] if column_order else None
        for r in rows:
            val = r.get(dedupe_key)
            rid = r.get(id_col) if id_col else None
            if val in seen:
                canonical = seen[val]
                if rid is not None:
                    id_mapping_result[rid] = canonical
                continue
            seen[val] = rid
            deduped.append(r)
        rows = deduped

    # optionally deduplicate data rows by unique columns (prevent UNIQUE constraint errors)
    if unique_cols:
        seen_keys = set()
        filtered_rows = []
        for r in rows:
            key = tuple(r.get(c) for c in unique_cols)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            filtered_rows.append(r)
        rows = filtered_rows

    cols = list(rows[0].keys())
    cols_sql = ', '.join(cols)
    placeholders = ', '.join(['%s'] * len(cols))
    insert_sql = f"INSERT INTO {table_name} ({cols_sql}) VALUES ({placeholders})"

    if conn is None:
        raise RuntimeError("Database connection (conn) must be provided to load_csv_to_table")

    cur = conn.cursor()
    try:
        try:
            cur.execute(f"TRUNCATE TABLE {table_name};")
        except Exception:
            pass

        data_tuples = [tuple(r.get(c) for c in cols) for r in rows]
        if data_tuples:
            cur.executemany(insert_sql, data_tuples)
            conn.commit()
    finally:
        cur.close()

    print(f"Loaded {len(rows)} rows into {table_name} from {csv_path}")
    return id_mapping_result


def main():
    # create/drop DB and schema
    try:
        # import locally to avoid circular at module import
        from App.db_setup import setup_nuclear
        setup_nuclear()
    except Exception as e:
        print(f"Warning: could not run setup_nuclear(): {e}")

    # open a DB connection and disable foreign key checks for the duration of the bulk load
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, port=DB_PORT)
    cur = conn.cursor()
    try:
        cur.execute("SET FOREIGN_KEY_CHECKS=0;")
    finally:
        cur.close()

    # mapping: csv filename -> (table_name, column_order)
    mapping = {
        'countries.csv': ('countries', ['country_id', 'country_name', 'country_code', 'region'], None, None),
        'energy_indicator_details.csv': ('energy_indicator_details', ['energy_indicator_id', 'indicator_name', 'indicator_code', 'indicator_description', 'measurement_unit'], 'indicator_code', None),
        'energy_data.csv': ('energy_data', ['country_id', 'energy_indicator_id', 'year', 'indicator_value', 'data_source'], None, ['country_id', 'energy_indicator_id', 'year']),
        'freshwater_indicators.csv': ('freshwater_indicator_details', ['freshwater_indicator_id', 'indicator_name', 'description', 'unit_of_measure'], None, None),
        'freshwater_data.csv': ('freshwater_data', ['country_id', 'freshwater_indicator_id', 'indicator_value', 'year', 'source_notes'], None, ['country_id', 'freshwater_indicator_id', 'year']),
        'ghg_indicator_details.csv': ('ghg_indicator_details', ['ghg_indicator_id', 'indicator_name', 'indicator_description', 'unit_symbol'], None, None),
        'greenhouse_emissions.csv': ('greenhouse_emissions', ['country_id', 'ghg_indicator_id', 'indicator_value', 'share_of_total_pct', 'uncertainty_pct', 'year', 'source_notes'], None, ['country_id', 'ghg_indicator_id', 'year']),
        'health_indicator_details.csv': ('health_indicator_details', ['health_indicator_id', 'indicator_name', 'indicator_description', 'unit_symbol'], None, None),
        'health_system.csv': ('health_system', ['country_id', 'health_indicator_id', 'indicator_value', 'year', 'source_notes'], None, ['country_id', 'health_indicator_id', 'year']),
        'sustainability_indicator_details.csv': ('sustainability_indicator_details', ['sus_indicator_id', 'indicator_name', 'indicator_code', 'indicator_description'], None, None),
        'sustainability_data.csv': ('sustainability_data', ['country_id', 'sus_indicator_id', 'year', 'indicator_value', 'source_note'], None, ['country_id', 'sus_indicator_id', 'year']),
    }

    # global mapping of old indicator ids -> canonical ids per id column name
    global_id_map = {}

    for fname, (table, cols, *extra) in mapping.items():
        csv_path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(csv_path):
            print(f"CSV not found: {csv_path}, skipping {table}")
            continue
        # some CSV headers use slightly different names; try to standardize keys
        # For freshwater_data and health_system consistency, our load function maps by header names.
        dedupe_key = extra[0] if extra else None
        unique_cols = extra[1] if len(extra) > 1 else None
        # determine if we need to pass an id_map for remapping referenced ids
        id_map = None
        id_map_col = None
        # if this table is a detail table and returns mappings, capture them
        if dedupe_key:
            res = load_csv_to_table(csv_path, table, column_order=cols, dedupe_key=dedupe_key, unique_cols=unique_cols, conn=conn)
            # res maps old_id -> canonical_id for this detail table
            if res:
                # store mapping keyed by its id column name (first column)
                id_col = cols[0]
                global_id_map[id_col] = res
        else:
            # for data tables that reference an id column, attempt to remap using global_id_map
            # pick potential id column names from cols to see if any mapping exists
            for possible_id_col in cols:
                if possible_id_col in global_id_map:
                    id_map = global_id_map[possible_id_col]
                    id_map_col = possible_id_col
                    break
            load_csv_to_table(csv_path, table, column_order=cols, id_map=id_map, id_map_col=id_map_col, unique_cols=unique_cols, conn=conn)

    # re-enable foreign key checks after loading
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=1;")
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
