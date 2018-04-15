import collections


class SpokenMessages:
    """
    Base class for different types of messages.

    This allows one to easily add a message type by creating the messages to be sent (or sequence of messages to be
    sent

    In this case, to nodes, a sender and receiver speak to each other using an iterator self.messages_to_be_spoken.
    the Speak() method is used to send data and listen() method is used to append to self.messages_heard list
    Before speaking, each node checks to see if the other node has sent an end, reject or verified message

    """

    def __init__(self, messages_to_be_spoken):
        """


        :param messages_to_be_spoken: non-dict iterable (list, set, tuple) of bytes/byte string message ie b'hello'
        """
        assert (isinstance(messages_to_be_spoken, collections.Iterable)), "first argument of SpokenMessages Class must " \
                                                                          "be and iterable (list, set, tuple) "

        self.messages_to_be_spoken = iter(messages_to_be_spoken)

        self.messages_heard = list()
        self.last_msg = b'end'
        self.reject_msg = b'rej'
        self.verified_msg = b'ver'
        self.end_convo = False

    def speak(self):
        """
        For veri nodes must override this method not to look for rejection or acceptance msg
        :return:
        """
        try:
            if self.messages_heard and self.messages_heard[-1] in {self.last_msg, self.reject_msg, self.verified_msg}:
                self.end_convo = True
                return self.last_msg
            return next(self.messages_to_be_spoken)

        except StopIteration:
            self.end_convo = True
            return self.last_msg

    def listen(self, msg):
        """
        in Protocol().dataReceived() listen() must come first before speak() (for both client and server(listener node)
        in Protocol().connectionMade() the client
        :param msg: append into self.message_heard list
        :return: None
        """
        self.messages_heard.append(msg)

    def follow_up(self):
        """
        call this function in Protocol.connectionLost()
        this function generally stores messages in database of message. while storing it notes if the message
        was verified, rejected or incomplete (connection was closed or lost)
        :return:
        """
        pass