import datetime
import serial
import time
from datetime import datetime
import numpy as np
from serial.serialutil import Timeout
import pandas as pd

class Arduino:
    '''
    Generic class for arduino with connected sensors outputting data to serial port
    Assumes each loop outputs to own line
    '''
    def __init__(self, port: str, baud_rate = 9600, timeout = 1, separator = ',', sensors = None, time_sig = True):
        '''
        port = COM port arduino is connected to
        separator = separator used in arduino output
        sensors = arraylike, list of sensor names, if not provided assumes arduino will provide in first line of output
        time_sig = boolean, set true if first column of arduino output is time signature of measurement
        '''
        self.connection = serial.Serial(port = port, baudrate = baud_rate, timeout = timeout)
        self.timeout = timeout
        self.separator = separator
        time.sleep(0.5)
        self.sensors = {}
        self.has_sensors = False
        self.has_time = time_sig
        self.headers = sensors
        if sensors:
            self.has_sensors = True
            for sensor in sensors:
                self.sensors[sensor] = np.array([])
        if self.has_time:
            self.sensors["Time Sig"] = np.array([])
        


    def _collect_data_to_arr(self, max_time = 1000, max_arr_len = 1000, encoding = 'UTF-8', timeout = 3000):
        '''
        Collects data to python array
        encoding = encoding of incoming data
        max_time = time to collect data [in ms]
        max_arr_len = maximum number of data samples to collect
        timeout = time to wait for first data [in ms]
        '''
        self.connection.reset_output_buffer()
        self.connection.reset_input_buffer()
        begin_time = (round(time.time()*1000))
        compare_time = begin_time
        current_time = begin_time - 2*max_time
        arr_len = 0
        first_received = False
        print("Waiting for data begin...")
        while((current_time - compare_time  < max_time ) and (arr_len < max_arr_len) and compare_time - begin_time < timeout):
            current_time = (round(time.time()*1000))
            if not first_received:
                    compare_time = current_time
            if(self.connection.in_waiting):
                data = str(self.connection.readline()[:-2].decode(encoding))
                data_arr = data.split(self.separator)
                if not first_received:
                        print("Collecting...")
                first_received = True
                if(arr_len == 0 and not self.has_sensors):  #first line should be sensor names if list not provided
                    self.headers = data_arr[int(self.has_time):] # first may be time_sig
                    for sensor in self.headers:
                        self.sensors[sensor] = np.array([])

                else:
                    if self.has_time:
                        self.sensors["Time Sig"] = np.append(self.sensors["Time Sig"], data_arr[0])
                    try:
                        if len(data_arr) != len(self.headers) + int(self.has_time):
                            raise Exception    
                        for i, sensor in enumerate(self.headers):
                            self.sensors[sensor] = np.append(self.sensors[sensor], int(data_arr[i+int(self.has_time)]))
                    except Exception as e:
                        print("Unexpected error, please check if correct amount of data samples is being sent")
                        break
                arr_len += 1
        self.sensors = pd.DataFrame(self.sensors)
        if first_received:
            print("Data collected, time taken: " + str(current_time-compare_time) + " ms, data samples collected: " + str(arr_len))
        else:
            print("Timed out, no data received")

    def _collect_data_to_file(self, output_file, file_sep = ',', max_time = 1000, max_arr_len = 1000, encoding = 'UTF-8', timeout = 3000):
        '''
        Collects data to output_file, appending to it if already exists
        encoding = encoding of incoming data
        file_sep = separator to use in output file
        max_time = time to collect data [in ms]
        max_arr_len = maximum number of data samples to collect
        timeout = time to wait for first data [in ms]
        '''
        self.connection.reset_output_buffer()
        begin_time = (round(time.time()*1000))
        compare_time = begin_time
        current_time = begin_time - 2*max_time
        arr_len = 0
        first_received = False
        with open(output_file, "a") as output:
            print("Waiting for data begin...")
            while((current_time - compare_time < max_time ) and (arr_len < max_arr_len) and compare_time - begin_time < timeout):
                current_time = (round(time.time()*1000))
                if not first_received:
                    compare_time = current_time
                if(self.connection.in_waiting):
                    if not first_received:
                        print("Collecting...")
                    first_received = True
                    data = str(self.connection.readline()[:-2].decode(encoding))
                    data_arr = data.split(sep=self.separator)
                    for meas in data_arr[:-1]:
                        output.write(meas + file_sep)
                    output.write(data_arr[len(data_arr)-1] + "\n")
                    arr_len += 1
            if first_received:
                print("Data collected, time taken: " + str(current_time-compare_time) + " ms, data samples collected: " + str(arr_len))
            else:
                print("Timed out, no data received")

    def _log_data_to_file(self, output_path, file_sep = ','):
        """
        logs data from sensor arr to file specified output_path, overwriting the file
        """
        if(isinstance(self.sensors, pd.DataFrame)):
            file_ext = output_path.split('.')[-1]
            if file_ext == "json":
                self.sensors.to_json(output_path)
            else:
                self.sensors.to_csv(output_path, sep = file_sep, index_label=False)
        else:
            print("Error: data has not been collected, Arduino._collect_data_to_arr() should be ran first")


    def _get_data_from_file(self, input_file: str, file_sep = ','):
        """
        gets data to sensor dataframe from input file, assumes data is separated by file_sep
        input file = json or supported by DataFrame.read_csv()
        """
        file_ext = input_file.split('.')[-1]
        try:
            if file_ext == "json": #jak olejek se stwierdzi ze bedziemy przez wifi przesylac to sie przyda moze
                self.sensors = pd.read_json(input_file)
            else:
                self.sensors = pd.read_csv(input_file, sep = file_sep)
        except Exception as e:
            print(e)
            print("Error, please check if file provided is correct")


    def _create_log_file(self, path_to_folder = '', file_ext = "csv", filename = None):
        '''
        Creates file for logging
        Opens file and returns filename and full filepath

        path_to_folder = where to store the file
        file_ext = extension, must be trivially writeable
        filename = custom filename, bu default creates datestamped log LOG_datestamp
        '''
        if not filename:
            now = datetime.now()
            str_now = now.strftime("%m%d_%H%M%S")
            filename = "LOG_" + str_now + '.' + file_ext
        fullpath = path_to_folder + filename
        try:
            file = open(fullpath, "x")
            file.close()
            return tuple([filename, fullpath])
        except Exception as e:
            print("Error creating log, check if file already exists")
        return tuple(None, None)


if __name__ == "__main__":
    '''
        Tu tylko testuje jbc
    '''
    arduino = Arduino("COM7", sensors=["EKG", "MPK", "HWDP"])
    
    #log_file, log_path= arduino._create_log_file()
    #arduino._collect_data_to_arr(max_time = 10000, max_arr_len=10)
    arduino._log_data_to_file("test.csv")
    arduino._get_data_from_file("test.csv")
    print(arduino.sensors)
    