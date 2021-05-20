import datetime
import serial
import time
import csv
from datetime import datetime



class Arduino:
    '''
    Generic class for arduino with connected sensors outputting data to serial port
    Assumes each loop outputs to own line, with data from each sensor separated by separator
    '''

    def __init__(self, port: str, baud_rate = 9600, timeout = 1, separator = ','):
        self.connection = serial.Serial(port = port, baudrate = baud_rate, timeout = timeout)
        self.separator = separator
        time.sleep(0.5)
        self.data = []


    def _collect_data_to_arr(self, max_time = 1000, max_arr_len = 1000, encoding = 'UTF-8'):
        '''
        Collects data to python array
        encoding = encoding of incoming data
        max_time = time to collect data [in ms]
        max_arr_len = maximum of datapoints to collect
        '''
        self.connection.reset_output_buffer()
        self.connection.reset_input_buffer()
        begin_time = (round(time.time()*1000))
        current_time = begin_time - 2*max_time
        arr_len = 0
        while((current_time - begin_time  < max_time ) and (arr_len < max_arr_len)):
            current_time = (round(time.time()*1000))
            #print(current_time-begin_time)
            if(self.connection.in_waiting):
                data = str(self.connection.readline()[:-2].decode(encoding))
                self.data.append(data)
                arr_len += 1


    def _collect_data_to_file(self, output_file, file_sep = ',', max_time = 1000, max_arr_len = 1000, encoding = 'UTF-8'):
        '''
        Collects data to output_file, appending to it if already exists
        encoding = encoding of incoming data
        file_sep = separator to use in output file
        max_time = time to collect data [in ms]
        max_arr_len = maximum number of data samples to collect
        '''
        self.connection.reset_output_buffer()
        begin_time = (round(time.time()*1000))
        current_time = begin_time - 2*max_time
        arr_len = 0
        print(output_file)
        with open(output_file, "a") as output:
            while((current_time - begin_time < max_time ) and (arr_len < max_arr_len)):
                current_time = (round(time.time()*1000))
                if(self.connection.in_waiting):
                    data = str(self.connection.readline()[:-2].decode(encoding))
                    data_arr = data.split(sep=self.separator)
                    for meas in data_arr[:-1]:
                        print(meas + file_sep)
                        output.write(meas + file_sep)
                    print(data_arr[len(data_arr)-1] + "\n")
                    output.write(data_arr[len(data_arr)-1] + "\n")
                    arr_len += 1

    def create_log_file(self, path_to_folder = '', file_ext = "csv", filename = None):
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
    arduino = Arduino("COM7")
    log_file, log_path= arduino.create_log_file()
    arduino._collect_data_to_file(output_file = log_path, max_time = 10000, max_arr_len=10000000000)
    # print(len(arduino.data))
