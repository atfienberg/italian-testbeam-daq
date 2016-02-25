// Generate a start trigger for the DAQ.

//--- std includes ----------------------------------------------------------//
#include <iostream>
#include <string>
#include <ctime>
using std::cout;
using std::endl;

//--- other includes --------------------------------------------------------//
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <zmq.hpp>

int main(int argc, char *argv[])
{
  // Set default config file location.
  std::string conf_file("/home/venanzoni/testBeam/italian-testbeam-daq/fast/");

  conf_file += std::string("config/.default_master.json");

  // Check for a different config file
  if (argc > 1) conf_file = std::string(argv[1]);

  // Get the system configuration
  boost::property_tree::ptree conf;
  boost::property_tree::read_json(conf_file, conf);

  zmq::context_t ctx(1);
  zmq::socket_t start_sck(ctx, ZMQ_PUSH);
  zmq::socket_t handshake_sck(ctx, ZMQ_REQ);

  start_sck.connect(conf.get<std::string>("trigger_port").c_str());
  handshake_sck.connect(conf.get<std::string>("handshake_port").c_str());

  std::string connect("CONNECTED:");
  zmq::message_t handshake_msg(connect.size());
  memcpy(handshake_msg.data(), connect.c_str(), connect.size());

  bool rc = false;
  int num_tries = 0;

  // Attempt to establish a connection.
  do {
    rc = handshake_sck.send(handshake_msg, ZMQ_DONTWAIT);
    ++num_tries;
  } while (!rc && (num_tries < 500));

  if (rc == true) {

    // Complete the handshake.
    do {
      rc = handshake_sck.recv(&handshake_msg, ZMQ_DONTWAIT);
    } while (rc == false);

    // Create the start message
    std::string trigger("START:test:");
    zmq::message_t start_msg(trigger.size());
    memcpy(start_msg.data(), trigger.c_str(), trigger.size());

    do {
      rc = start_sck.send(start_msg);
    } while (rc == false);

    cout << "Connection established.  Sending start trigger." << endl;
    return 0;

  } else {
    
    cout << "Connection not established.  No trigger sent." << endl;
    return 1;
  }
}
