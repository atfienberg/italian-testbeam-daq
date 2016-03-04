/**
 * Find which USB caen digitizers are connected to the PC and what their id
 * numbers are
 */

#include <iostream>
#include "CAENDigitizer.h"

#include "common.hh"

using namespace std;

int main(int argc, char const *argv[]) {
  CAEN_DGTZ_ErrorCode ret = CAEN_DGTZ_Success;
  int handle = 0;

  int id = 1;
  cout << "opening : " << CAEN_DGTZ_OpenDigitizer(CAEN_DGTZ_USB, id, 0, 0, &handle) << endl;

  CAEN_DGTZ_Reset(handle);

  CAEN_DGTZ_BoardInfo_t bInfo;
  CAEN_DGTZ_GetInfo(handle, &bInfo);
  cout << bInfo.Channels << " channel, " << bInfo.ADC_NBits << " bit "
       << bInfo.ModelName << " found with id " << id << " and handle "
       << handle << endl;
  
  uint32_t data;
  cout << "reading gain register: " << CAEN_DGTZ_ReadRegister(handle, 
							      0x1028,
							      &data) << endl;
  cout << "value : " << data << endl;
  cout << "setting gain register: " << CAEN_DGTZ_WriteRegister(handle, 
							       0x1028,
							       1) << endl;

  cout << "reading gain register 0: " << CAEN_DGTZ_ReadRegister(handle, 
								0x1028,
								&data) << endl;
  cout << "value : " << data << endl;

  cout << "reading gain register 1: " << CAEN_DGTZ_ReadRegister(handle, 
								0x1128,
								&data) << endl;



  cout << "read trace length: " << CAEN_DGTZ_GetRecordLength(handle, &data) << endl;

  cout << "value : " << data << endl;

  cout << "set trace length: " << CAEN_DGTZ_SetRecordLength(handle, CAEN_5730_LN) << endl;

  cout << "read trace length: " << CAEN_DGTZ_GetRecordLength(handle, &data) << endl;

  cout << "value : " << data << endl;

  cout << "read post trigger: " << CAEN_DGTZ_GetPostTriggerSize(handle, &data) << endl;

  cout << "value : " << data << endl;

  cout << "set post trigger: " << CAEN_DGTZ_SetPostTriggerSize(handle, 54) << endl;

  cout << "read post trigger: " << CAEN_DGTZ_GetPostTriggerSize(handle, &data) << endl;

  cout << "value : " << data << endl;

  cout << "read dc offet 0: " << CAEN_DGTZ_GetChannelDCOffset(handle, 0, &data) << endl;

  cout << "value : " << data << endl;

  cout << "set dc offet 0: " << CAEN_DGTZ_SetChannelDCOffset(handle, 0, 0x1) << endl;
  
  cout << "read dc offet 0: " << CAEN_DGTZ_GetChannelDCOffset(handle, 0, &data) << endl;

  cout << "value : " << data << endl;

  cout << "read dc offet 1: " << CAEN_DGTZ_GetChannelDCOffset(handle, 1, &data) << endl;
  
  cout << "value : " << data << endl;

  cout << "set channel enable mask: " << CAEN_DGTZ_SetChannelEnableMask(handle, 0xff) << endl;

  cout << "get channel enable mask: " << CAEN_DGTZ_GetChannelEnableMask(handle, &data) << endl;
  
  cout << "value == 0xff : " << std::boolalpha << (data==0xff) << endl;

  CAEN_DGTZ_SetRecordLength(handle, CAEN_5730_LN);

  if (CAEN_DGTZ_SetChannelDCOffset(handle, 0, 0x0000)) {
    cout << ("Error setting DC offset") << endl;
  }

  sleep(1);

  uint32_t size, bsize;
  char* buffer;

  CAEN_DGTZ_UINT16_EVENT_t* event;
  char* eventptr;

  CAEN_DGTZ_EventInfo_t eventinfo;


  if (CAEN_DGTZ_MallocReadoutBuffer(handle, &buffer, &size)) {
    cout << ("failed to allocate readout buffer.") << endl;
  }
  if (CAEN_DGTZ_AllocateEvent(handle, (void**)&event)) {
    cout << ("failed to allocate event") << endl;
  }


  if (CAEN_DGTZ_SWStartAcquisition(handle)) {
    cout << "failed to start acq" << endl;
  }

  if(CAEN_DGTZ_SendSWtrigger(handle)){
    cout << "Failed to send sw trigger" << endl;
  }

  if (CAEN_DGTZ_ReadData(handle, CAEN_DGTZ_SLAVE_TERMINATED_READOUT_MBLT,
                         buffer, &bsize)) {
    cout << ("failed to read data") << endl;
  }

  uint32_t num_events;
  if (CAEN_DGTZ_GetNumEvents(handle, buffer, bsize, &num_events)) {
    cout << ("failed to get num events") << endl;
  }

  if(num_events > 0){
    
    cout << ("getting event!") << endl;

    daq::caen_5730 bundle;

    if (CAEN_DGTZ_GetEventInfo(handle, buffer, bsize, 0, &eventinfo,
			       &eventptr)) {
      cout << ("failed to get event info") << endl;
    }

    cout << ("event counter %i", eventinfo.EventCounter) << endl;

    if (CAEN_DGTZ_DecodeEvent(handle, eventptr, (void**)&event)) {
      cout << ("could't decode event") << endl;
    } else {
      cout << ("successfully decoded event.") << endl;
    }

    bundle.event_index = eventinfo.EventCounter;

    for (uint32_t i = 0; i < CAEN_5730_CH; ++i) {
      std::copy(event->DataChannel[i], event->DataChannel[i] + CAEN_5730_LN,
		bundle.trace[i]);
    }

    cout << bundle.event_index << endl;
    cout << bundle.trace[0][5000] << endl;
  }
  
  
  if (CAEN_DGTZ_FreeEvent(handle, (void**)&event)) {
    cout << "failed to free event" << endl;
  }
  if (CAEN_DGTZ_FreeReadoutBuffer(&buffer)) {
    cout << "failed to free buffer " << endl;
  }
  
  if (CAEN_DGTZ_SWStopAcquisition(handle)) {
    cout << "failed to stop acq" << endl;
  }

  cout << "closing : " << CAEN_DGTZ_CloseDigitizer(handle) << endl;
}
