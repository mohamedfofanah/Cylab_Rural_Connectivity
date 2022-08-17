from time import sleep
from Transport.tcp_interface import TcpInterface
from Transport.address_exhange import AddressExchanger
import asyncio as aio
from threading import Thread
from Interests.interest_handler import InterestHandler
import sys

tcp_port = 9000
udp_port = 5000


def run_address_ex_process(addr_ex: AddressExchanger) -> None:
    aio.run(addr_ex(port=tcp_port))


def run_receiver_process(interface: TcpInterface) -> None:
    aio.run(interface.receive())


async def main(content_source):
    addr_ex = AddressExchanger(port=udp_port)
    addr_ex_process = Thread(target=run_address_ex_process, args=(addr_ex,))
    addr_ex_process.daemon = True
    addr_ex_process.start()

    interest_handler = InterestHandler(addr_ex=addr_ex, content_source=content_source)
    interface = TcpInterface(on_data_received=interest_handler.on_new_message, addr_ex=addr_ex, port=tcp_port)
    await interface.open()
    receiver_process = Thread(target=run_receiver_process, args=(interface,))
    receiver_process.daemon = True
    receiver_process.start()

    interests_service = Thread(target=interest_handler.run_pending_interests_service, args=(interface,))
    interests_service.daemon = True
    interests_service.start()

    while not addr_ex.get_connections():
        print("waiting to connect ...")
        sleep(1)

    while True:
        sys.stdout.write('Enter your query: ')
        sys.stdout.flush()
        query = sys.stdin.readline()

        try:
            message = interest_handler.create_request(query=query)
            if message:
                interface.send(message)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    content = sys.argv[0]
    # noinspection PyBroadException
    try:
        loop = aio.get_event_loop()

        loop.run_until_complete(main(content_source=content))

    except:
        pass
