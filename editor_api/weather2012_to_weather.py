import os
import datetime
from sys import argv, stdout, path
from shutil import copyfile

path.insert(0, "C:/SWAT/SWATPlus/Workflow/packages")

from helper_functions import read_from, copy_file, write_to, show_progress, list_files


def convert_weather(weather_source, weather_data_dir, file_count=None):
    print("")
    weather_dir = weather_source
    destination = weather_data_dir
    if not os.path.isdir(destination):
        os.makedirs(destination)

    forks = ["pcp.txt", "wnd.txt", "slr.txt", "hmd.txt", "tmp.txt"]
    counting = 0
    for fork_file in forks:
        fork_path = "{0}/{1}".format(weather_dir, fork_file)
        if os.path.isfile(fork_path):
            fork_content = read_from(fork_path)
            new_fork_string = "file names - file written by SWAT+ editor auto-workflow v1.0 [{0}]\nfilename\n".format(
                str(datetime.datetime.now()).split(".")[0])
            for line in fork_content:
                if line == fork_content[0]:
                    continue
                if not file_count is None:
                    counting += 1
                    show_progress(counting, file_count,
                                  string_before="\t   formating weather: ")
                filename = "{0}.{1}".format(
                    line.split(",")[1], fork_file.split(".")[0])
                new_fork_string += "{0}\n".format(filename)

                file_2012 = ""
                date_ = None
                start_date = None
                nyears = 1
                version2012_station_content = read_from(
                    "{0}/{1}.txt".format(weather_dir, line.split(",")[1]))
                for line_2012 in version2012_station_content:
                    if line_2012 == version2012_station_content[0]:
                        date_ = datetime.datetime(int(line_2012[:4]), 1, 1)
                        start_date = datetime.datetime(
                            int(line_2012[:4]), 1, 1)
                        continue
                    else:
                        if date_.year - start_date.year > 0:
                            start_date = datetime.datetime(date_.year, 1, 1)
                            nyears += 1
                        if fork_file == "tmp.txt":
                            min_tmp = float(line_2012.split(",")[1])
                            max_tmp = float(line_2012.split(",")[0])

                            tmp_values = "{0}{1}".format("{0}".format(
                                max_tmp).rjust(10), "{0}".format(min_tmp).rjust(10))
                            file_2012 += "{0}{1}{2}\n".format(date_.year, str(
                                int((date_ - start_date).days) + 1).rjust(5), tmp_values)
                        else:
                            file_2012 += "{0}{1}{2}\n".format(date_.year, str(
                                int((date_ - start_date).days) + 1).rjust(5), str(float(line_2012)).rjust(9))

                        date_ += datetime.timedelta(days=1)
                station_info = "{z}{o}{t}{th}{f}".format(z=str(nyears).rjust(4), o="0".rjust(10), t=line.split(
                    ",")[2].rjust(10), th=line.split(",")[3].rjust(10), f=line.split(",")[4].rjust(11))
                file_header_ = \
                    "{1}: data - file written by SWAT+ editor auto-workflow v1.0 [{0}]\nnbyr     tstep       lat       lon      elev\n{2}".format(
                        str(datetime.datetime.now()).split(".")[0], filename, station_info)

                file_header_ += file_2012
                write_to("{dest}/{fname}".format(fname=filename,
                                                 dest=destination), file_header_)

            write_to("{0}/{1}.cli".format(
                destination, fork_file.split(".")[0]), new_fork_string)
        # else:
        #     print("\t! could not find {0} in {1}".format(fork_file, weather_dir))
    print("\n\t   finished.\n")


if __name__ == "__main__":
    forks = ["pcp.txt", "wnd.txt", "slr.txt", "hmd.txt", "tmp.txt"]

    weather_source = argv[1]
    weather_data_dir = argv[2]

    all_files = 0
    for fork in forks:
        try:
            all_files += len(read_from("{0}/{1}".format(weather_source, fork))) - 1
        except:
            pass

    convert_weather(weather_source, weather_data_dir, all_files)
