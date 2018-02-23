import pandas as pd
import os
import math
import reegis_tools.config as cfg


def get_grid_capacity(grid, plus, minus):
    tmp_grid = grid.query("plus_region_id == {:0d} & ".format(plus) +
                          "minus_region_id == {:1d} & ".format(minus) +
                          "scenario_name == 'status_quo_2012_distance'")

    if len(tmp_grid) > 0:
        capacity = tmp_grid.capacity_calc.sum()
        distance = tmp_grid.distance.iloc[0]
    else:
        capacity = 0
        distance = 0
    return capacity, distance


def get_electrical_transmission_de21(duplicate=False):
    f_security = cfg.get('transmission', 'security_factor')
    current_max = cfg.get('transmission', 'current_max')

    grid = pd.read_csv(os.path.join(
        cfg.get('paths', 'data_de21'),
        cfg.get('transmission', 'transmission_renpass')))

    # renpass F.Wiese (page 49)
    grid['capacity_calc'] = (grid.circuits * current_max * grid.voltage *
                             f_security * math.sqrt(3) / 1000)

    pwr_lines = pd.read_csv(os.path.join(
        cfg.get('paths', 'geo_de21'),
        cfg.get('transmission', 'powerlines_line')), index_col='name')

    for l in pwr_lines.index:
        split = l.split('-')
        a = ('110{0}'.format(split[0][2:]))
        b = ('110{0}'.format(split[1][2:]))
        # print(a, b)
        cap1, dist1 = get_grid_capacity(grid, int(a), int(b))
        cap2, dist2 = get_grid_capacity(grid, int(b), int(a))

        if cap1 == 0 and cap2 == 0:
            pwr_lines.loc[l, 'capacity'] = 0
            pwr_lines.loc[l, 'distance'] = 0
        elif cap1 == 0 and cap2 != 0:
            pwr_lines.loc[l, 'capacity'] = cap2
            pwr_lines.loc[l, 'distance'] = dist2
        elif cap1 != 0 and cap2 == 0:
            pwr_lines.loc[l, 'capacity'] = cap1
            pwr_lines.loc[l, 'distance'] = dist1
        else:
            print("Error in {0}".format(l))

    # plot_grid(pwr_lines)
    df = pwr_lines[['capacity', 'distance']]

    if duplicate:
        values = df.copy()

        def id_inverter(name):
            return '-'.join([name.split('-')[1], name.split('-')[0]])

        df.index = df.index.map(id_inverter)

        df = pd.DataFrame(pd.concat([values, df]))

    return df


def get_grid():
    return pd.read_csv(os.path.join('data', 'grid', 'de21_transmission.csv'),
                       index_col='Unnamed: 0')


if __name__ == "__main__":
    lines = get_electrical_transmission_de21(duplicate=False)
    print(lines)
    print(len(lines))
