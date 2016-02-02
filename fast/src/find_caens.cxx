/**
 * Find which USB caen digitizers are connected to the PC and what their id
 * numbers are
 */

#include <iostream>
#include "CAENDigitizer.h"

using namespace std;

int main(int argc, char const *argv[]) {
  CAEN_DGTZ_ErrorCode ret = CAEN_DGTZ_Success;
  int handle = 0;

  int id = 0;
  while (ret == CAEN_DGTZ_Success) {
    ret = CAEN_DGTZ_OpenDigitizer(CAEN_DGTZ_USB, id, 0, 0, &handle);
    if (ret == 0) {
      CAEN_DGTZ_BoardInfo_t bInfo;
      CAEN_DGTZ_GetInfo(handle, &bInfo);
      cout << bInfo.Channels << " channel, " << bInfo.ADC_NBits << " bit "
           << bInfo.ModelName << " found with id " << id << " and handle "
           << handle << endl;
      CAEN_DGTZ_CloseDigitizer(handle);
    } else if (id == 0) {
      cout << "no digitizers found." << endl;
    }

    ++id;
  }
}