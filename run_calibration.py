'''
date        : 31/03/2020
description : this module coordinates calibration

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''
# imports
import os, sys
import multiprocessing
import shutil
import numpy as np
import numpy
import time
import subprocess

from itertools import product

sys.path.insert(0, os.path.join(os.environ["swatplus_wf_dir"], "packages"))
sys.path.insert(0, sys.argv[1])

sys.argv[1] = sys.argv[1].replace("\\\\", "/")
sys.argv[1] = sys.argv[1].replace("\\", "/")

from helper_functions import read_from, write_to, copy_directory
import pandas
import pystran as py
import namelist


# functions

def clear_directory(dir_path):
    try:
        shutil.rmtree(dir_path)
    except:
        print("\t! Workspace was not cleared.")


def calculate_nse(observation_fn, simulated_fn, t_step=2):
    observed_df = pandas.read_csv(observation_fn)
    simulated_df = pandas.read_csv(simulated_fn)

    observed_df.columns = ["Date", "Observed"]
    simulated_df.columns = ["Date", "Simulated"]

    observed_df[observed_df.columns[0]] = pandas.to_datetime(
        observed_df[observed_df.columns[0]])
    simulated_df[simulated_df.columns[0]] = pandas.to_datetime(
        simulated_df[simulated_df.columns[0]])

    if t_step == 1:
        observed_df = observed_df.resample(
            "D", on=observed_df.columns[0]).mean()
        simulated_df = simulated_df.resample(
            "D", on=simulated_df.columns[0]).mean()

    if t_step == 2:
        observed_df = observed_df.resample(
            "M", on=observed_df.columns[0]).mean()
        simulated_df = simulated_df.resample(
            "M", on=simulated_df.columns[0]).mean()

    if t_step == 3:
        observed_df = observed_df.resample(
            "Y", on=observed_df.columns[0]).mean()
        simulated_df = simulated_df.resample(
            "Y", on=simulated_df.columns[0]).mean()

    data_df = pandas.merge(observed_df, simulated_df, on='Date')
    data_df.dropna(inplace=True)

    obs = data_df['Observed'].tolist()
    sim = data_df['Simulated'].tolist()

    npsim = numpy.array(sim).astype(numpy.float)
    npobs = numpy.array(obs).astype(numpy.float)

    try:
        return 1 - numpy.sum((npsim-npobs)**2)/numpy.sum((npobs-numpy.mean(npobs))**2)
    except:
        return None


def set_calibration_cal(header, parameter_set, chg_typ_dict, calibration_header):

    parameter_set = ['{0:.4g}'.format(float(value)) for value in parameter_set]
    cal_string = ""
    line_template = "{parname}        {chgtyp}                {value}" \
        "       0     0      0      0      0      0      0        0\n"
    par_count = 0

    for ind in range(0, len(parameter_set)):
        cal_string += line_template.format(
            parname=str(header[ind]).ljust(8),
            chgtyp=chg_typ_dict[header[ind]],
            value=parameter_set[ind],
        )
        par_count += 1
    calibration_cal = calibration_header.format(
        number_of_parms=par_count, all_parms=cal_string)
    return calibration_cal


def run_parameter_set(parameter_set_list, core_number, chg_typ_dict, header, calibration_header, working_dir):
    """

    """
    report = "{0},NSE\n".format(",".join(header))
    for parameter_set in parameter_set_list:
        calibration_cal = set_calibration_cal(
            header, parameter_set, chg_typ_dict, calibration_header)
        # write to the correct location relative to the 'working' directory
        write_to("{working_dir}/{core}/calibration.cal".format(
            working_dir=working_dir, core=core_number),
            calibration_cal,
            report_=False,
        )
        os.chdir("{working_dir}/{core}".format(
            working_dir=working_dir, core=core_number))

        if not os.path.isfile("rev60.1_64rel.exe"):
            shutil.copyfile(swat_exe, "rev60.1_64rel.exe")
        print("\t> running SWAT+ in process {0}".format(core_number))
        os.system("rev60.1_64rel.exe")
        # subprocess.Popen('rev60.1_64rel.exe', stdout=subprocess.PIPE)

        # extract flow for specified unit at specified timestep

        sim_results = read_from("{working_dir}/{core}/channel_sd_day.csv".format(
            working_dir=working_dir, core=core_number))[3:]

        simulated_string = "Date,Simulated\n"

        results_index = None
        if calibration_variable == "1":
            results_index = 47
        if calibration_variable == "2":
            results_index = 9

        if not results_index is None:
            for r_line in sim_results:
                if r_line.split(",")[4] == str(unit_number):
                    day_val = r_line.split(",")[2]
                    simulated_string += "{dd}/{mm}/{yy},{val}\n".format(
                        dd=day_val,
                        mm=r_line.split(",")[1],
                        yy=r_line.split(",")[3],
                        val=r_line.split(",")[results_index],
                    )

            simulated_fn = "{working_dir}/{core}/simulated.csv".format(
                working_dir=working_dir, core=core_number)
            report_fn = "{working_dir}/{core}/report.csv".format(
                working_dir=working_dir, core=core_number)
            observed_fn = "{home_dir}/data/observations/{cal_obs_fn}".format(
                cal_obs_fn=observation_filename, home_dir=sys.argv[1])

            write_to(
                simulated_fn,
                simulated_string
            )

        # calculate nse and append to list table
        if calibration_time_step == '1':
            print("\t > calculating NSE at daily timestep")
            NSE = calculate_nse(simulated_fn, observed_fn, t_step=1)
        if calibration_time_step == '2':
            print("\t > calculating NSE at monthly timestep")
            NSE = calculate_nse(simulated_fn, observed_fn, t_step=2)
        if calibration_time_step == '3':
            print("\t > calculating NSE at yearly timestep")
            NSE = calculate_nse(simulated_fn, observed_fn, t_step=3)

        if not NSE is None:
            front_string = ""
            for item in parameter_set:
                front_string += str(item) + ","
            report += front_string + str(NSE) + "\n"
            # report += "{0},{1}\n".format(",".join(parameter_set), NSE)

        write_to(report_fn, report)


if __name__ == "__main__":
    if namelist.Model_2_namelist:
        sys.exit(0)
    if not namelist.Calibrate:
        sys.exit(0)
    start_time = time.time()

    # set variables
    swat_exe = "C:/SWAT/SWATPlus/Workflow/editor_api/swat_exe/rev60.1_64rel.exe"
    base = "{0}/{1}/Scenarios/Default".format(
        sys.argv[1], namelist.Project_Name)
    working_dir = "{base_dir}/working".format(base_dir=base)
    runs = namelist.Number_of_Runs
    output_dir = working_dir + "/output/"
    config_file_name = namelist.Calibration_Config_File
    home_dir = sys.argv[1]
    config_file_path = "{home_dir}/data/calibration/{config_file}".format(
        config_file=config_file_name, home_dir=home_dir)

    observation_filename = read_from(config_file_path)[2].split(",")[2]
    unit_number = read_from(config_file_path)[3].split(",")[2]
    print("\t> calibrating to channel number {0}".format(unit_number))
    calibration_time_step = read_from(config_file_path)[4].split(",")[2]
    calibration_variable = read_from(config_file_path)[5].split(",")[2]

    core_count = namelist.Number_of_Processes
    pool_cores = multiprocessing.Pool(core_count)
    file_cio = read_from("{base}/TxtInOut/file.cio".format(base=base))

    calibration_header = "calibration.cal parameters for sensitivity analysis and " \
        "calibration by SWAT+ Workflow\n {number_of_parms}\nNAME           CHG_TYP  " \
        "                VAL   CONDS  LYR1   LYR2  YEAR1  YEAR2   DAY1   DAY2  OBJ_TOT"\
        "\n{all_parms}"

    # prepare workspace
    clear_directory(working_dir)
    if not os.path.isdir(working_dir):
        os.makedirs(working_dir)

    # prepare environment
    parameters = read_from(config_file_path)[8:]
    copy_results = None

    # prepare file.cio to read calibration.cal
    cio_string = ""
    for line in file_cio:
        if line.startswith("chg"):
            cio_string += "chg               cal_parms.cal     "\
                "calibration.cal   null              null              "\
                "null              null              null              "\
                "null              null              \n"
        else:
            cio_string += line

    write_to("{base}/TxtInOut/file.cio".format(base=base), cio_string)

    # duplicate txtinout
    fn_list = ["{working_dir}/{core}/cal_parameters.csv".format(
        working_dir=working_dir, core=i) for i in range(
            1, core_count + 1)]

    with pool_cores:
        copy_results = pool_cores.starmap(
            copy_directory,
            product(
                ["{base}/TxtInOut".format(base=base)],
                [working_dir],
                [i for i in range(1, core_count + 1)],
            )
        )

    if False in copy_results:
        print("\t! There was an error making copies of the model")
        print("\t  Check free space available on the disk")
        sys.exit(1)

    # Import parameter ranges in correct format (min, max, name) and convert to list of tuples
    temp_param_ranges = pandas.read_csv(
        config_file_path, sep=",", skiprows=[0, 1, 2, 3, 4, 5, 6, 7],
        usecols=[0, 1, 2], skip_blank_lines=True, names=["name", "min", "max"],
        engine="python").dropna()

    chg_typ_dict = {}
    headers = []
    for line in parameters:
        chg_typ_dict[line.split(",")[0]] = line.split(",")[3].strip("\n")
        headers.append(line.split(",")[0])

    param_ranges_df = temp_param_ranges[["min", "max", "name"]]
    param_ranges = param_ranges_df.apply(tuple, axis=1).tolist()

    # Prepare model class
    global_oat = py.GlobalOATSensitivity(param_ranges, ModelType="external")

    # Prepare the parameter sample and save to text file with header for visualisation purposes
    global_oat.PrepareSample(nbaseruns=runs, perturbation_factor=0.01,
                             samplemethod="lh", numerical_approach="single")
    par_sets = global_oat.parset2run
    print("\t> number of parameter sets: {f}\n".format(f=par_sets.shape[0]))
    time.sleep(2)

    par_sets = [list(par_set) for par_set in par_sets]

    parameter_groups = []
    for i in range(1, core_count + 1):
        parameter_groups.insert(0, [])

    position = 0
    for par_dist in par_sets:
        if position == core_count:
            position = 0
        parameter_groups[position].append(list(par_dist))
        position += 1
    pool = multiprocessing.pool.ThreadPool(core_count + 1)
    print(working_dir)
    for i in range(1, core_count + 1):
        print("\t > running SWAT+ in loop {0}".format(i))
        time.sleep(2)
        pool.apply_async(
            run_parameter_set, (parameter_groups[i-1], i, chg_typ_dict, headers, calibration_header, working_dir,))

    # close the pool and wait for each running task to complete
    pool.close()
    pool.join()
    os.chdir(working_dir)

    report_df = pandas.read_csv("1/report.csv")

    for j in range(2, core_count + 1):
        report_df = pandas.concat(
            [report_df, pandas.read_csv("{0}/report.csv".format(j))])

    report_df.to_csv("all.csv")
    report_df = report_df.sort_values(by='NSE', ascending=False)
    report_df.to_csv("sorted.csv")
    report_df = report_df.reset_index()

    # adding best parameters to model.
    new_headers = []
    new_parameter_set = []
    par_names = list(report_df.columns.values)[1:-1]
    print("Best Parameters")
    for par_name in par_names:
        new_headers.append(par_name)
        new_parameter_set.append(str(report_df.loc[0, par_name]))
        print("{0}\t: {1}".format(par_name, report_df.loc[0, par_name]))

    new_calibration_cal = set_calibration_cal(
        new_headers, new_parameter_set, chg_typ_dict, calibration_header)
    write_to("{base}/TxtInOut/calibration.cal".format(base=base),
             new_calibration_cal)
    os.chdir("{base}/TxtInOut/".format(base=base))
    os.system(swat_exe)

    sys.exit()
