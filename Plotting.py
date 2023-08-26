import os
import glob
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# Find all .csv files in the directory tree
from pandas.core.dtypes.inference import is_float

csv_files = glob.glob('**/*.csv', recursive=True)

# Create a new folder for plots if it doesn't exist
plot_folder = os.path.join(os.path.dirname(__file__), 'plots')
os.makedirs(plot_folder, exist_ok=True)


# Process each CSV file
# def find_col_index(subdir_name_arg):
#     df_arg = pd.read_csv(subdir_name_arg, low_memory=False)
#     df_arg = df_arg.reset_index(drop=True)
#     df_cols = df_arg.columns
#     col_index = [df_cols.get_loc(name) for name in ['Date', 'LinePressure (kPa)', 'PressureRegulator (kPa)', 'OpticalTemp',
#                                                     'LaserStatus', 'LaserTotalPulses', 'LaserTotalTime',
#                                                     'LaserPower (W)', 'CoolingState', 'LaserRemoteInterlock',
#                                                     'TankPressure (kPa)', 'ProbeType', 'LaserPulseDuration (ms)',
#                                                     'LaserPulseDelay (ms)']]
#     print(col_index)
#     return col_index


def find_laser_index(treatment_time_arg):
    start_laser_index = []
    stop_laser_index = []
    pulse = df['LaserPulseDuration (ms)']
    delay = df['LaserPulseDelay (ms)']
    row_count = 1
    count = 0
    while row_count < len(df.index):
        for row in range(row_count, len(df.index)):
            if df['LaserStatus'][row] == 'Laser':
                start_laser_foo = row
                start_laser_index.append(start_laser_foo)
                for row_remain in range(start_laser_foo + 1, len(df.index)):
                    if df['LaserStatus'][row_remain - 1] == 'Laser' and df['LaserStatus'][row_remain] == 'Standby':
                        stop_laser_foo = row_remain - 1
                        if treatment_time_arg == '':
                            treatment_laser_on = df['LaserTotalTime'][
                                max([idx for idx in range(start_laser_foo, len(df['LaserTotalTime']) - 2) if not
                                     isinstance(df['LaserTotalTime'][idx], float)])]
                            try:
                                treatment_laser_on_foo = time.strptime(df['LaserTotalTime'][stop_laser_foo], '%H:%M:%S')
                                treatment_laser_on_foo = treatment_laser_on_foo.tm_hour * 3600 + treatment_laser_on_foo.tm_min * 60 + treatment_laser_on_foo.tm_sec
                                treatment_laser_on = time.strptime(treatment_laser_on, '%H:%M:%S')
                                treatment_laser_on = treatment_laser_on.tm_hour * 3600 + treatment_laser_on.tm_min * 60 + treatment_laser_on.tm_sec
                                if treatment_laser_on_foo + 1 >= treatment_laser_on:
                                    stop_laser_index.append(stop_laser_foo)
                                    treatment_time = treatment_laser_on_foo * (
                                                pulse[stop_laser_foo] + delay[stop_laser_foo]) / pulse[
                                                         stop_laser_foo] / 60
                                    print("Total Treatment Time: " + str(treatment_time))
                                    break
                            except ValueError:
                                print("LaserTotalTime does not follow normal format")
                                return 1
                        else:
                            treatment_laser_on = int(np.floor(float(treatment_time_arg) * pulse[stop_laser_foo] / (
                                        pulse[stop_laser_foo] + delay[stop_laser_foo])))
                            try:
                                if time.strptime(df['LaserTotalTime'][stop_laser_foo], '%H:%M:%S') > time.strptime(
                                        '00:' + str(treatment_laser_on) + ':00', '%H:%M:%S'):
                                    stop_laser_index.append(stop_laser_foo)
                                    break
                            except ValueError:
                                print("LaserTotalTime does not follow normal format")
                                return 1
                break
        if count == len(stop_laser_index):
            break
        row_count = stop_laser_index[count] + 1
        count += 1
    return start_laser_index, stop_laser_index


for csv_file in csv_files:
    # Read the CSV file into a pandas DataFrame, skipping the first row
    print(csv_file)
    # use_cols_arg = find_col_index(csv_file)
    use_cols_arg = [0, 11, 13, 107, 40, 42, 43, 49, 17, 45, 9, 20, 50, 51]
    df = pd.read_csv(csv_file).iloc[:, use_cols_arg].reset_index(drop=True)
    col_names = ['Date', 'LinePressure (kPa)', 'PressureRegulator (kPa)', 'OpticalTemp',
                 'LaserStatus', 'LaserTotalPulses', 'LaserTotalTime', 'LaserPower (W)',
                 'CoolingState', 'LaserRemoteInterlock', 'TankPressure (kPa)', 'ProbeType', 'LaserPulseDuration (ms)',
                 'LaserPulseDelay (ms)']
    df = df.rename(columns=dict(zip(df.columns, col_names)))

    # Get the parent folder name of the CSV file
    parent_folder = os.path.basename(os.path.dirname(csv_file))
    start_laser, stop_laser = find_laser_index(15)
    print(start_laser)
    print(stop_laser)
    for run in range(len(start_laser)):
        # Create a new plot with two y-axes
        fig, ax1 = plt.subplots()
        fig.set_size_inches(16, 6)  # Set the figure size (width: 16 inches, height: 6 inches)
        forward_index = 400
        if start_laser[run] >= 600:
            back_index = 600
        elif start_laser[run] >= 400:
            back_index = 400
        elif start_laser[run] >= 200:
            back_index = 200
        else:
            back_index = 100
        try:
            df_run = df[start_laser[run] - back_index:stop_laser[run] + forward_index]
        except IndexError:
            df_run = df[start_laser[run] - back_index:stop_laser[run] + 100]
        # Plot series 1 and series 2 on the primary y-axis (left side)
        line1, = ax1.plot(df_run['LinePressure (kPa)'], label='LinePressure (kPa)', linewidth=1.0, color='blue')
        line2, = ax1.plot(df_run['PressureRegulator (kPa)'], label='PressureRegulator (kPa)', linewidth=1.0, linestyle='--', color='black')
        ax1.set_xlabel('Data Point Index')
        ax1.set_ylabel('Pressure')
        ax1.set_ylim(0, 3500)  # Set the range for pressure axis
        ax1.tick_params(axis='y')

        # Create a secondary y-axis for series 3 (temperature)
        ax2 = ax1.twinx()
        line3, = ax2.plot(df_run['OpticalTemp'], label='Optical Temp (C)', linewidth=.50, color='red')
        ax2.set_ylabel('Temperature')
        ax2.set_ylim(5, 90)  # Set the range for temperature axis
        ax2.tick_params(axis='y')

        # Create a secondary y-axis for series 4 (power)
        ax3 = ax1.twinx()
        offset = 60  # Adjust this value to control the spacing between axes
        ax3.spines['right'].set_position(('outward', offset))
        ax3.yaxis.set_ticks_position('right')
        ax3.yaxis.set_label_position('right')
        line4, = ax3.plot(df_run['LaserPower (W)'], label='Dornier Laser (W)', linewidth=.50, color='green')
        ax3.set_ylabel('Power')
        ax3.set_ylim(0, 20)  # Set the range for temperature axis
        ax3.tick_params(axis='y')
        ax3.set_yticks(np.linspace(0, 20, 21))
        # Combine the legends into a single legend
        handles = [line1, line2, line3, line4]
        labels = [handle.get_label() for handle in handles]
        ax1.legend(handles, labels, loc='upper left')

        # Find the index of the maximum temperature value
        max_temp_index = df_run['OpticalTemp'].idxmax()
        # Find the index of the maximum pressure value
        max_pressure_index = df_run['LinePressure (kPa)'].idxmax()

        # Find the index of the spike temp
        df_short = df[start_laser[run]:start_laser[run] + 30]
        temp_spike_index = df_short['OpticalTemp'].idxmax()

        # Get the corresponding values for temperature and pressure
        max_temp = df.loc[max_temp_index, 'OpticalTemp']
        max_pressure = df.loc[max_pressure_index, 'LinePressure (kPa)']
        temp_spike = df.loc[temp_spike_index, 'OpticalTemp']

        # Add data point labels for the peak temperature and pressure
        ax2.annotate(f'Max Temp: {max_temp:.1f}°C', xy=(max_temp_index, max_temp), xytext=(max_temp_index + 200, max_temp + 2),
                     arrowprops=dict(arrowstyle='->'))
        ax1.annotate(f'Max Pressure: {max_pressure:.1f} kPa', xy=(max_pressure_index, max_pressure),
                     xytext=(max_pressure_index - 20, max_pressure - 500), arrowprops=dict(arrowstyle='->'))
        ax2.annotate(f'Spike Temp: {temp_spike:.1f}°C', xy=(temp_spike_index, temp_spike),
                     xytext=(temp_spike_index + 200, temp_spike + 5),
                     arrowprops=dict(arrowstyle='->'))
        # Add gridlines
        ax1.grid(True)
        ax2.grid(True)

        # Set plot title
        if len(start_laser) > 1:
            plt.title(parent_folder+'_run'+str(run+1))
        else:
            plt.title(parent_folder)

        # Save the plot as a PNG file in the plot folder
        if len(start_laser) > 1:
            plot_filename = parent_folder + '_run' + str(run+1) + '.png'
        else:
            plot_filename = parent_folder + '.png'
        plot_path = os.path.join(plot_folder, plot_filename)
        plt.savefig(plot_path)

        # Close the plot
        plt.close()

print("Plots saved successfully in the 'plots' folder.")

