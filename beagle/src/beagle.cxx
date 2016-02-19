#include <iostream>
#include <string>
#include <zmq.hpp>

using namespace std;

int main(int argc, char const *argv[]) {
  zmq::context_t context(1);
  zmq::socket_t sock(context, ZMQ_REQ);
  int timeout = 2000;
  int linger = 0;
  sock.setsockopt(ZMQ_RCVTIMEO, &timeout, sizeof(timeout));
  sock.setsockopt(ZMQ_LINGER, &linger, sizeof(linger));

  sock.connect("tcp://192.168.0.22:6669");

  if(argc < 2){
    cout << "must give request string." << endl;
    exit(0);
  }

  // send work request
  string request_str;
  for(int i = 1; i < argc; ++i){
    request_str += argv[i];
    request_str += " ";
  }
  zmq::message_t request_msg(request_str.begin(), request_str.end());
  sock.send(request_msg);
  cout << "sent request " << request_str << endl;

  // wait for reply
  zmq::message_t recv_msg;
  if (sock.recv(&recv_msg)){

    string msg_str((char *)recv_msg.data(), 
		   (char *)recv_msg.data() + recv_msg.size());
    cout << "got reply: " << msg_str << endl;

  } else {
    cout << "beagle board not responding." << endl;
  }

  return 0;
}
