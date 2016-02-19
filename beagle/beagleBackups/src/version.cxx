#include <zmq.hpp>
#include <iostream>
#include <vector>

int main(){
  int major, minor, patch;

  std::vector<double> test;

  zmq_version (&major, &minor, &patch); printf ("Current ØMQ version is %d.%d.%d\n", major, minor, patch);
  return 0;
}
