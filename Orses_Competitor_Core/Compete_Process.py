from .Block_Data_Aggregator import BlockAggregator
import multiprocessing


def compete_process(q_for_compete: multiprocessing.Queue):
    """
    :param q_for_compete: queue from main process, data from propagator initiator is sent to before
    :return:
    """
    while True:

        # receives main message dict
        msg = q_for_compete.get()


if __name__ == '__main__':
    pass