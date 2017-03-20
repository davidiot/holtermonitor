// daq_testing2.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"
#include "nidaqmx.h"

// error handling
#define DAQmxErrChk(functionCall) if (DAQmxFailed(error=(functionCall)) ) goto Error; else

int _tmain(int argc, _TCHAR* argv[])
{
	// recording variables!
	int32 RecordLength = 8000000;	// record length, in samples. 

	float64 sampFreq = 200000.0;	// sampling frequency in Hz
	float64 minVolt = -1.0;			// minimum input voltage, in Volts
	float64 maxVolt =  1.0;			// maximum input voltage, in Volts


// DAQ variables
	int32 error = 0;
	TaskHandle taskHandle = 0;
	int32 read;
	float64 * data = NULL;
	char errBuff[2048] = {'\0'};

	data = new float64[RecordLength];

	printf("Test environment for NI-DAQ uses!\n");

	// Configure DAQ card
	DAQmxErrChk (DAQmxCreateTask("",&taskHandle));
	DAQmxErrChk (DAQmxCreateAIVoltageChan(taskHandle,"Dev1/ai0","", DAQmx_Val_Cfg_Default,minVolt,maxVolt, DAQmx_Val_Volts, NULL));
	DAQmxErrChk (DAQmxCfgSampClkTiming(taskHandle, "/Dev1/PFI7", sampFreq, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, RecordLength));

	// Start that DAQ!
	printf("DAQ Configured.  Acquiring data....\n");
	DAQmxErrChk (DAQmxStartTask(taskHandle));

	// Read out from DAQ!
	printf("Reading from DAQ card to local memory...\n");
	DAQmxErrChk (DAQmxReadAnalogF64(taskHandle, RecordLength, 10.0, DAQmx_Val_GroupByChannel, data, RecordLength, &read, NULL));

	
	// Store to local file
	printf("Cooper did not implement saving to a local file yet.  Lazy Cooper....\n");


Error:
	if( DAQmxFailed(error) )
		DAQmxGetExtendedErrorInfo(errBuff,2048);
	if( taskHandle!=0 )  {
		/*********************************************/
		// DAQmx Stop Code
		/*********************************************/
		DAQmxStopTask(taskHandle);
		DAQmxClearTask(taskHandle);
	}
	if( DAQmxFailed(error) )
		printf("DAQmx Error: %s\n",errBuff);

	if (data)
		delete[] data;

	printf("task complete!\n");
	getchar();
	return 0;
}

