#include <iostream>
#include <string>
#include <zmq.hpp>

typedef std::vector<zmq::message_t> multi_mesg;

multi_mesg recv_multipart(zmq::socket_t& sock);

// for send, please don't try to send an empty multi_msg
// multi_msg must be at least size 1
void send_multipart(zmq::socket_t& sock, multi_mesg& msg);

void send_multipart(zmq::socket_t& sock, multi_mesg&& msg);

int main(int argc, char const* argv[]) {
  zmq::context_t context(1);

  zmq::socket_t r_sock(context, ZMQ_ROUTER);
  r_sock.bind("tcp://*:6669");

  zmq::socket_t d_sock(context, ZMQ_DEALER);
  d_sock.bind("tcp://*:6670");

  zmq::pollitem_t pollitems[] = {{(void*)r_sock, 0, ZMQ_POLLIN, 0},
                                 {(void*)d_sock, 0, ZMQ_POLLIN, 0}};

  while (true) {
    std::cout << "polling for work requests" << std::endl;
    zmq::poll(pollitems, 2, -1);

    if (pollitems[0].revents & ZMQ_POLLIN) {
      std::cout << "got request, passing to dealer" << std::endl;
      send_multipart(d_sock, recv_multipart(r_sock));
    }

    if (pollitems[1].revents & ZMQ_POLLIN) {
      std::cout << "got reply, passing to router" << std::endl;
      send_multipart(r_sock, recv_multipart(d_sock));
    }
    std::cout << "passed to router" << std::endl;
  }

  return 0;
}

multi_mesg recv_multipart(zmq::socket_t& sock) {
  multi_mesg recvd_msg;

  int more;
  auto more_size = sizeof(more);
  do {
    recvd_msg.push_back({});
    sock.recv(&recvd_msg.back());
    sock.getsockopt(ZMQ_RCVMORE, &more, &more_size);
  } while (more != 0);

  return recvd_msg;
}

void send_multipart(zmq::socket_t& sock, multi_mesg& mmsg) {
  assert(mmsg.size() > 0);

  for (std::size_t i = 0; i < mmsg.size() - 1; ++i) {
    sock.send(mmsg[i], ZMQ_SNDMORE);
  }

  sock.send(mmsg.back(), 0);
}

void send_multipart(zmq::socket_t& sock, multi_mesg&& mmsg) {
  send_multipart(sock, mmsg);
}
