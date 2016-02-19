#include <iostream>
#include <string>
#include <zmq.hpp>

using namespace std;

string do_work() {
  cout << "starting work" << endl;
  sleep(5);
  cout << "done with work" << endl;
  return "work done";
}

int main(int argc, char const *argv[]) {
  zmq::context_t context(1);
  zmq::socket_t sock(context, ZMQ_REP);
  sock.connect("tcp://127.0.0.1:6670");

  while (true) {
    cout << "waiting for work request" << endl;
    zmq::message_t recv_msg;
    sock.recv(&recv_msg);
    string msg_str((char *)recv_msg.data(),
                   (char *)recv_msg.data() + recv_msg.size());
    cout << "received work request : " << msg_str << endl;

    msg_str = do_work();

    // reply
    zmq::message_t reply_msg(msg_str.begin(), msg_str.end());
    sock.send(reply_msg);
    cout << "reply sent" << endl;
    cout << "-----" << endl;
  }

  return 0;
}