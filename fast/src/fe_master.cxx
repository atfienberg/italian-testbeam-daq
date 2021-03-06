// Master Frontend

//--- std includes ----------------------------------------------------------//
#include <cassert>
#include <ctime>
#include <cstdio>
#include <iostream>
#include <vector>
using std::cout;
using std::endl;
using std::vector;
using std::string;

//--- other includes --------------------------------------------------------//
#include <boost/foreach.hpp>
#include <boost/variant.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
using namespace boost::property_tree;

#include <zmq.hpp>

//--- project includes -----------------------------------------------------//
#include "worker_list.hh"
#include "writer_online.hh"
#include "writer_root.hh"
#include "event_builder.hh"
#include "common.hh"

using namespace daq;

// Anonymous namespace for "global" parameters
namespace {

// simple declarations
bool is_running = false;
bool rc = 0;

// std declarations
string msg_string;
string conf_file;
string tmp_conf_file(tmpnam(nullptr));

// project declarations
WorkerList workers;
vector<WriterBase *> writers;
EventBuilder *event_builder = nullptr;
}

// Function declarations
int LoadConfig();   // just the file
int SetupConfig();  // all the workers and writers
int FreeConfig();   // free all the workers and writers
int StartRun();
int StopRun();

// The main loop
int main(int argc, char *argv[]) {
  // If there was a command line argument, grab that file.
  if (argc > 1) {
    conf_file = string(argv[1]);

  } else {
    // Set default config file location.
    conf_file = conf_dir + string(".default_master.json");
  }

  // Load the configuration
  LoadConfig();

  ptree conf;
  read_json(tmp_conf_file, conf);

  // Connect the sockets since they shouldn't ever change.
  zmq::socket_t trigger_sck(msg_context, ZMQ_PULL);
  trigger_sck.bind(conf.get<string>("trigger_port").c_str());

  zmq::socket_t handshake_sck(msg_context, ZMQ_REP);
  handshake_sck.bind(conf.get<string>("handshake_port").c_str());

  zmq::message_t msg;
  zmq::pollitem_t pollitems[2];
  pollitems[0].socket = (void *)trigger_sck;
  pollitems[0].events = ZMQ_POLLIN;
  pollitems[1].socket = (void *)handshake_sck;
  pollitems[1].events = ZMQ_POLLIN;

  while (true) {
    // Check for a message.

    do {
      try {
        zmq::poll(pollitems, 2, -1);
      } catch (const zmq::error_t &e) {
        // interruped system call
        continue;
      }
    } while ((pollitems[0].revents != ZMQ_POLLIN) &&
             (pollitems[1].revents != ZMQ_POLLIN));

    if (pollitems[0].revents == ZMQ_POLLIN) {
      do {
	try{
	  rc = trigger_sck.recv(&msg, ZMQ_DONTWAIT);
	} catch (const zmq::error_t& e){
	  continue;
	} 
      } while (rc != true);

      if (rc == true) {
        // Process the message.
        std::istringstream ss(static_cast<char *>(msg.data()));
        std::getline(ss, msg_string, ':');

        if (msg_string == string("START") && !is_running) {
          // Reload the external config.
          LoadConfig();

          // Change the run number.
          string file_name("data/cenparun_");
          std::getline(ss, msg_string, ':');
          file_name.append(msg_string);
          file_name.append(".root");

          // Save the internal config.
          ptree conf;
          read_json(tmp_conf_file, conf);
          conf.put("writers.root.file", file_name);
          write_json(tmp_conf_file, conf);

          // Setup the config and run.
          SetupConfig();
          StartRun();

        } else if (msg_string == string("STOP") && is_running) {
          StopRun();
          FreeConfig();
        }
      }

      usleep(daq::long_sleep);
    }

    if (pollitems[1].revents == ZMQ_POLLIN) {
      
      do {
	try{
	  rc = handshake_sck.recv(&msg, ZMQ_DONTWAIT);
	} catch (const zmq::error_t& e){
	  continue;
	} 
      } while (rc != true);

      if (rc == true) {
        usleep(long_sleep);

        do {
	  try{
	    rc = handshake_sck.send(msg, ZMQ_DONTWAIT);
	  } catch (const zmq::error_t& e) {
	    continue;
	  }
        } while (rc == false);
      }
    }
  }

  return 0;
}

int LoadConfig() {
  // Load up the configuration file to refresh the internal one.

  ptree conf;
  read_json(conf_file, conf);
  write_json(tmp_conf_file, conf);

  return 0;
}

int SetupConfig() {
  // Load the internal config file.
  ptree conf;
  read_json(tmp_conf_file, conf);

  // Get the fake data writers (for testing).
  /*BOOST_FOREACH (const ptree::value_type &v, conf.get_child("devices.fake")) {
    string name(v.first);
    string dev_conf_file(v.second.data());

    workers.PushBack(new WorkerFake(name, conf_dir + dev_conf_file));
  }*/

  // Set up the sis3350 devices.
  BOOST_FOREACH (const ptree::value_type &v,
                 conf.get_child("devices.sis_3350")) {
    string name(v.first);
    string dev_conf_file(v.second.data());

    workers.PushBack(new WorkerSis3350(name, conf_dir + dev_conf_file));
  }

  // Set up the sis3302 devices.
  BOOST_FOREACH (const ptree::value_type &v,
                 conf.get_child("devices.sis_3302")) {
    string name(v.first);
    string dev_conf_file(v.second.data());

    workers.PushBack(new WorkerSis3302(name, conf_dir + dev_conf_file));
  }

  // Set up the caen1785 devices.
  BOOST_FOREACH (const ptree::value_type &v,
                 conf.get_child("devices.caen_1785")) {
    string name(v.first);
    string dev_conf_file(v.second.data());

    workers.PushBack(new WorkerCaen1785(name, conf_dir + dev_conf_file));
  }

  // Set up the caen5730 devices.
  BOOST_FOREACH (const ptree::value_type &v,
                 conf.get_child("devices.caen_5730")) {
    string name(v.first);
    string dev_conf_file(v.second.data());

    workers.PushBack(new WorkerCaenDT5730(name, conf_dir + dev_conf_file));
  }

  // Set up the caen6742 devices.
  std::vector<WorkerCaen6742 *> caen_vec;
  BOOST_FOREACH (const ptree::value_type &v,
                 conf.get_child("devices.caen_6742")) {
    string name(v.first);
    string dev_conf_file(v.second.data());

    caen_vec.push_back(new WorkerCaen6742(name, conf_dir + dev_conf_file));
  }

  // Now push back the old caen6742 devices based on sn == 406
  for (auto &caen : caen_vec) {
    if (caen->dev_sn() == 406) {
      workers.PushBack(caen);
    }
  }
  // Now push back the new device
  for (auto &caen : caen_vec) {
    if (caen->dev_sn() != 406) {
      workers.PushBack(caen);
    }
  }

  // Set up the caen1742 devices.
  BOOST_FOREACH (const ptree::value_type &v,
                 conf.get_child("devices.caen_1742")) {
    string name(v.first);
    string dev_conf_file(v.second.data());

    workers.PushBack(new WorkerCaen1742(name, conf_dir + dev_conf_file));
  }

  // Set up the caen5720 devices.
  BOOST_FOREACH (const ptree::value_type &v,
                 conf.get_child("devices.caen_5720")) {
    string name(v.first);
    string dev_conf_file(v.second.data());

    workers.PushBack(new WorkerCaenDT5720(name, conf_dir + dev_conf_file));
  }

  // Set up the DRS4 devices.
  // BOOST_FOREACH (const ptree::value_type &v, conf.get_child("devices.drs4"))
  // {
  //   string name(v.first);
  //   string dev_conf_file(v.second.data());

  //   workers.PushBack(new WorkerDrs4(name, conf_dir + dev_conf_file));
  // }

  // Set up the writers.
  BOOST_FOREACH (const ptree::value_type &v, conf.get_child("writers")) {
    if (string(v.first) == string("root") && v.second.get<bool>("in_use")) {
      writers.push_back(new WriterRoot(tmp_conf_file));

    } else if (string(v.first) == string("online") &&
               v.second.get<bool>("in_use")) {
      writers.push_back(new WriterOnline(tmp_conf_file));
    } 
  }

  // Set up the event builder.
  event_builder = new EventBuilder(workers, writers, tmp_conf_file);

  return 0;
}

int FreeConfig() {
  // this call will free workers through workerlist destructor
  // (event builder has a worker list member variable)
  delete event_builder;

  cout << "deleting workers " << endl;
  workers.Resize(0);

  // Delete the allocated writers.
  for (auto &writer : writers) {
    cout << "deleting writer" << endl;
    delete writer;
  }
  writers.resize(0);

  cout << "config freed" << endl;
  return 0;
}

// Flush the buffers and start data taking.
int StartRun() {
  is_running = true;

  // Start the event builder
  event_builder->StartBuilder();

  // Start the writers
  for (auto it = writers.begin(); it != writers.end(); ++it) {
    (*it)->StartWriter();
  }

  // Start the data gatherers
  workers.StartRun();

  return 0;
}

// Write the data file and reset workers.
int StopRun() {
  is_running = false;

  // Stop the event builder
  event_builder->StopBuilder();

  while (!event_builder->FinishedRun())
    ;

  // Stop the writers
  for (auto it = writers.begin(); it != writers.end(); ++it) {
    (*it)->StopWriter();
  }

  // Stop the data gatherers
  workers.StopRun();

  return 0;
}
