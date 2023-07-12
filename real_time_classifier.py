import serial
import time
import numpy as np
from scipy.signal import firwin
from database_class import DatabaseConnector
import os
import pywt
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))

debug = True  # prints debug text

# TO DO: Add your own config file and model path
configFileName = f'{script_dir}/config_files/xwr16xx_profile_2023_04_18T16_04_15_382.cfg'

CLIport = {}
Dataport = {}
byteBuffer = np.zeros(2 ** 15, dtype='uint8')
byteBufferLength = 0

db_connector = DatabaseConnector(f"{script_dir}/radar_database.db")


# ------------------------------------------------------------------
def wavelet_denoising(data, wavelet='db4', value=0.5):
    # Perform the wavelet transform.
    coefficients = pywt.wavedec2(data, wavelet)

    # Threshold the coefficients.
    threshold = pywt.threshold(coefficients[0], value=value)
    coefficients[0] = pywt.threshold(coefficients[0], threshold)

    # Inverse wavelet transform.
    denoised_data = pywt.waverec2(coefficients, wavelet)

    return denoised_data


def pulse_doppler_filter(radar_data):
    # Radar data dimensions: [range_bins, doppler_bins]
    range_bins, doppler_bins = radar_data.shape

    # Doppler filter length
    filter_length = 11

    # Generate filter coefficients using FIR filter design
    filter_coeffs = firwin(filter_length, cutoff=0.2, window='hamming', fs=4.5)

    # Output filtered data
    filtered_data = np.zeros((range_bins, doppler_bins))

    # Apply the pulse Doppler filter
    for i in range(doppler_bins):
        filtered_data[:, i] = np.convolve(radar_data[:, i], filter_coeffs, mode='same')

    return filtered_data


def create_peak_matrix(matrix, threshold):
    peak_matrix = np.zeros_like(matrix)

    rows, cols = matrix.shape

    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            current_value = matrix[i, j]
            neighbors = [
                matrix[i - 1, j],  # top
                matrix[i + 1, j],  # bottom
                matrix[i, j - 1],  # left
                matrix[i, j + 1]  # right
            ]

            if current_value >= np.max(neighbors) and current_value >= threshold:
                peak_matrix[i, j] = 1

    return peak_matrix


def highlight_peaks(matrix, threshold):
    rows, cols = matrix.shape
    peaks = []

    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            if matrix[i, j] >= threshold:
                neighbors = matrix[i - 1:i + 2, j - 1:j + 2]
                if matrix[i, j] == np.max(neighbors):
                    peaks.append((i, j))

    return peaks


def classifier_func(rangeArray, range_doppler):
    mask = np.ones((16, 256))
    mask[8] = 0  # make central frequencies zero

    range_doppler_denoised = wavelet_denoising(range_doppler, wavelet='haar', value=0.7)
    filtered_frame = pulse_doppler_filter(range_doppler_denoised) * mask
    peaks = create_peak_matrix(filtered_frame, threshold=0.9)

    std_peaks = np.std(peaks)

    classes_values = ["Human_Present", "No_Human_detected"]

    highlighted_peaks = highlight_peaks(range_doppler, threshold=70.0)
    highlighted_peaks_array = np.array(highlighted_peaks)
    picked_elements = rangeArray[highlighted_peaks_array[:, 1]].round(2)[:4] # select only 4 detected objects

    stacked_arr = np.vstack((picked_elements[:2],) * 5)  # Fist 2 elements of the detected range array stacked 5 times

    if np.any(stacked_arr > 2.2):
        predicted_class = classes_values[0]
    else:
        predicted_class = classes_values[1]

    time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if predicted_class == "Human_Present":
        db = {'Prediction': predicted_class, "Score": std_peaks, "Detected objects": picked_elements, 'Time': time_now}
    else:
        db = {'Prediction': predicted_class, "Score": std_peaks, "Detected objects": [], 'Time': time_now}

    db_connector.connect()
    db_connector.insert_data("Prediction", f"{db['Prediction']}", "Score", f"{db['Score']}", "Detected objects",
                             f"{db['Detected objects']}", "Time", f"{db['Time']}")
    db_connector.insert_rdv_matrix(range_doppler, f"{db['Time']}")
    db_connector.close()

    if debug:
        print(db)


# Function to configure the serial ports and send the data from
# the configuration file to the radar
def serialConfig(configFileName):
    global CLIport
    global Dataport

    port_found = False

    while not port_found:
        try:
            # Open the serial ports for the configuration and the data ports

            # Raspberry Pi / Ubuntu
            CLIport = serial.Serial('/dev/ttyACM0', 115200)
            Dataport = serial.Serial('/dev/ttyACM1', 921600)

            # Windows
            # CLIport = serial.Serial('COM6', 115200)
            # Dataport = serial.Serial('COM7', 852272)

            port_found = True

        except serial.SerialException:
            print("Serial port not found. Retrying in 1 second...")
            time.sleep(1)

    # Read the configuration file and send it to the board
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:
        CLIport.write((i + '\n').encode())
        print(i)
        time.sleep(0.01)

    return CLIport, Dataport


# ------------------------------------------------------------------

# Function to parse the data inside the configuration file
def parseConfigFile(configFileName):
    configParameters = {}  # Initialize an empty dictionary to store the configuration parameters

    # Read the configuration file and send it to the board
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:

        # Split the line
        splitWords = i.split(" ")

        # Hard code the number of antennas, change if other configuration is used
        numRxAnt = 4
        numTxAnt = 2

        # Get the information about the profile configuration
        if "profileCfg" in splitWords[0]:
            startFreq = int(float(splitWords[2]))
            idleTime = int(splitWords[3])
            rampEndTime = float(splitWords[5])
            freqSlopeConst = float(splitWords[8])
            numAdcSamples = int(splitWords[10])
            numAdcSamplesRoundTo2 = 1

            while numAdcSamples > numAdcSamplesRoundTo2:
                numAdcSamplesRoundTo2 = numAdcSamplesRoundTo2 * 2

            digOutSampleRate = int(splitWords[11])

        # Get the information about the frame configuration
        elif "frameCfg" in splitWords[0]:

            chirpStartIdx = int(splitWords[1])
            chirpEndIdx = int(splitWords[2])
            numLoops = int(splitWords[3])
            numFrames = int(splitWords[4])
            framePeriodicity = int(splitWords[5])

    # Combine the read data to obtain the configuration parameters
    numChirpsPerFrame = (chirpEndIdx - chirpStartIdx + 1) * numLoops
    configParameters["numDopplerBins"] = numChirpsPerFrame / numTxAnt
    configParameters["numRangeBins"] = numAdcSamplesRoundTo2
    configParameters["rangeResolutionMeters"] = (3e8 * digOutSampleRate * 1e3) / (
            2 * freqSlopeConst * 1e12 * numAdcSamples)
    configParameters["rangeIdxToMeters"] = (3e8 * digOutSampleRate * 1e3) / (
            2 * freqSlopeConst * 1e12 * configParameters["numRangeBins"])
    configParameters["dopplerResolutionMps"] = 3e8 / (
            2 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * configParameters["numDopplerBins"] * numTxAnt)
    configParameters["maxRange"] = (300 * 0.9 * digOutSampleRate) / (2 * freqSlopeConst * 1e3)
    configParameters["maxVelocity"] = 3e8 / (4 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * numTxAnt)

    return configParameters


# ------------------------------------------------------------------

# Funtion to read and parse the incoming data
def readAndParseData16xx(Dataport, configParameters):
    global byteBuffer, byteBufferLength

    # Constants
    OBJ_STRUCT_SIZE_BYTES = 12
    BYTE_VEC_ACC_MAX_SIZE = 2 ** 15
    MMWDEMO_UART_MSG_DETECTED_POINTS = 1
    MMWDEMO_UART_MSG_RANGE_PROFILE = 2
    MMWDEMO_OUTPUT_MSG_NOISE_PROFILE = 3
    MMWDEMO_OUTPUT_MSG_AZIMUT_STATIC_HEAT_MAP = 4
    MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP = 5
    maxBufferSize = 2 ** 15
    magicWord = [2, 1, 4, 3, 6, 5, 8, 7]

    # Initialize variables
    magicOK = 0  # Checks if magic number has been read
    dataOK = 0  # Checks if the data has been read correctly
    frameNumber = 0
    detObj = {}
    tlv_type = 0

    readBuffer = Dataport.read(Dataport.in_waiting)
    byteVec = np.frombuffer(readBuffer, dtype='uint8')
    byteCount = len(byteVec)

    # Check that the buffer is not full, and then add the data to the buffer
    if (byteBufferLength + byteCount) < maxBufferSize:
        byteBuffer[byteBufferLength:byteBufferLength + byteCount] = byteVec[:byteCount]
        byteBufferLength = byteBufferLength + byteCount

    # Check that the buffer has some data
    if byteBufferLength > 16:

        # Check for all possible locations of the magic word
        possibleLocs = np.where(byteBuffer == magicWord[0])[0]

        # Confirm that is the beginning of the magic word and store the index in startIdx
        startIdx = []
        for loc in possibleLocs:
            check = byteBuffer[loc:loc + 8]
            if np.all(check == magicWord):
                startIdx.append(loc)

        # Check that startIdx is not empty
        if startIdx:

            # Remove the data before the first start index
            if 0 < startIdx[0] < byteBufferLength:
                byteBuffer[:byteBufferLength - startIdx[0]] = byteBuffer[startIdx[0]:byteBufferLength]
                byteBuffer[byteBufferLength - startIdx[0]:] = np.zeros(len(byteBuffer[byteBufferLength - startIdx[0]:]),
                                                                       dtype='uint8')
                byteBufferLength = byteBufferLength - startIdx[0]

            # Check that there have no errors with the byte buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0

            # word array to convert 4 bytes to a 32-bit number
            word = [1, 2 ** 8, 2 ** 16, 2 ** 24]

            # Read the total packet length
            totalPacketLen = np.matmul(byteBuffer[12:12 + 4], word)

            # Check that all the packet has been read
            if (byteBufferLength >= totalPacketLen) and (byteBufferLength != 0):
                magicOK = 1

    # If magicOK is equal to 1 then process the message
    if magicOK:
        # word array to convert 4 bytes to a 32-bit number
        word = [1, 2 ** 8, 2 ** 16, 2 ** 24]

        # Initialize the pointer index
        idX = 0

        # Read the header
        magicNumber = byteBuffer[idX:idX + 8]
        idX += 8
        version = format(np.matmul(byteBuffer[idX:idX + 4], word), 'x')
        idX += 4
        totalPacketLen = np.matmul(byteBuffer[idX:idX + 4], word)
        idX += 4
        platform = format(np.matmul(byteBuffer[idX:idX + 4], word), 'x')
        idX += 4
        frameNumber = np.matmul(byteBuffer[idX:idX + 4], word)
        idX += 4
        timeCpuCycles = np.matmul(byteBuffer[idX:idX + 4], word)
        idX += 4
        numDetectedObj = np.matmul(byteBuffer[idX:idX + 4], word)
        idX += 4
        numTLVs = np.matmul(byteBuffer[idX:idX + 4], word)
        idX += 4
        subFrameNumber = np.matmul(byteBuffer[idX:idX + 4], word)
        idX += 4

        # Read the TLV messages
        for tlvIdx in range(numTLVs):

            # word array to convert 4 bytes to a 32-bit number
            word = [1, 2 ** 8, 2 ** 16, 2 ** 24]

            # Check the header of the TLV message
            try:
                tlv_type = np.matmul(byteBuffer[idX:idX + 4], word)
                idX += 4
                tlv_length = np.matmul(byteBuffer[idX:idX + 4], word)
                idX += 4
            except:
                pass

            # Read the data depending on the TLV message
            if tlv_type == MMWDEMO_UART_MSG_DETECTED_POINTS:

                # word array to convert 4 bytes to a 16-bit number
                word = [1, 2 ** 8]
                tlv_numObj = np.matmul(byteBuffer[idX:idX + 2], word)
                idX += 2
                tlv_xyzQFormat = 2 ** np.matmul(byteBuffer[idX:idX + 2], word)
                idX += 2

                # Initialize the arrays
                rangeIdx = np.zeros(tlv_numObj, dtype='int16')
                dopplerIdx = np.zeros(tlv_numObj, dtype='int16')
                peakVal = np.zeros(tlv_numObj, dtype='int16')
                x = np.zeros(tlv_numObj, dtype='int16')
                y = np.zeros(tlv_numObj, dtype='int16')
                z = np.zeros(tlv_numObj, dtype='int16')

                for objectNum in range(tlv_numObj):
                    # Read the data for each object
                    rangeIdx[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                    idX += 2
                    dopplerIdx[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                    idX += 2
                    peakVal[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                    idX += 2
                    x[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                    idX += 2
                    y[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                    idX += 2
                    z[objectNum] = np.matmul(byteBuffer[idX:idX + 2], word)
                    idX += 2

                # Make the necessary corrections and calculate the rest of the data
                rangeVal = rangeIdx * configParameters["rangeIdxToMeters"]
                dopplerIdx[dopplerIdx > (configParameters["numDopplerBins"] / 2 - 1)] = dopplerIdx[dopplerIdx > (
                        configParameters["numDopplerBins"] / 2 - 1)] - 65535
                dopplerVal = dopplerIdx * configParameters["dopplerResolutionMps"]
                x = x / tlv_xyzQFormat
                y = y / tlv_xyzQFormat
                z = z / tlv_xyzQFormat

                # Store the data in the detObj dictionary
                detObj = {"numObj": tlv_numObj, "rangeIdx": rangeIdx, "range": rangeVal, "dopplerIdx": dopplerIdx,
                          "doppler": dopplerVal, "peakVal": peakVal, "x": x, "y": y, "z": z}

                dataOK = 1

            elif tlv_type == MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP:

                # Get the number of bytes to read
                numBytes = int(2 * configParameters["numRangeBins"] * configParameters["numDopplerBins"])
                # Convert the raw data to int16 array
                payload = byteBuffer[idX:idX + numBytes]
                idX += numBytes
                rangeDoppler = payload.view(dtype=np.int16)

                # Some frames have strange values, skip those frames
                # TO DO: Find why those strange frames happen
                if np.max(rangeDoppler) > 10000:
                    continue

                # Convert the range doppler array to a matrix
                rangeDoppler = np.reshape(rangeDoppler, (
                    int(configParameters["numDopplerBins"]), int(configParameters["numRangeBins"])),
                                          'F')  # Fortran-like reshape
                rangeDoppler = np.append(rangeDoppler[int(len(rangeDoppler) / 2):],
                                         rangeDoppler[:int(len(rangeDoppler) / 2)], axis=0)
                rangeDoppler = 20 * np.log10(rangeDoppler)
                # Generate the range and doppler arrays for the plot
                rangeArray = np.array(range(configParameters["numRangeBins"])) * configParameters["rangeIdxToMeters"]
                dopplerArray = np.multiply(
                    np.arange(-configParameters["numDopplerBins"] / 2, configParameters["numDopplerBins"] / 2),
                    configParameters["dopplerResolutionMps"])

                classifier_func(rangeArray, rangeDoppler)

        # Remove already processed data
        if 0 < idX < byteBufferLength:
            shiftSize = totalPacketLen

            byteBuffer[:byteBufferLength - shiftSize] = byteBuffer[shiftSize:byteBufferLength]
            byteBuffer[byteBufferLength - shiftSize:] = np.zeros(len(byteBuffer[byteBufferLength - shiftSize:]),
                                                                 dtype='uint8')
            byteBufferLength = byteBufferLength - shiftSize

            # Check that there are no errors with the buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0

    return dataOK, frameNumber, detObj


# -------------------------    MAIN   -----------------------------------------

# Configurate the serial port
CLIport, Dataport = serialConfig(configFileName)

# Get the configuration parameters from the configuration file
configParameters = parseConfigFile(configFileName)

# Main loop
detObj = {}
frameData = {}
currentIndex = 0
while True:
    try:
        dataOk, frameNumber, detObj = readAndParseData16xx(Dataport, configParameters)

        if dataOk:
            # Store the current frame into frameData
            frameData[currentIndex] = detObj
            currentIndex += 1

        time.sleep(0.03)  # Sampling frequency of 30 Hz

    # Stop the program and close everything if Ctrl + c is pressed
    except KeyboardInterrupt:
        CLIport.write('sensorStop\n'.encode())
        CLIport.close()
        Dataport.close()
        break
