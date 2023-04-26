import asyncio
from getpass import getpass
import hashlib
import os
import pickle
import sys
import socket

from app import protocol
import client


def console_input(prompt='', clearing=0, is_hiding=False):
    input_func = getpass if is_hiding else input

    result = input_func(prompt)
    if clearing == 1:
        print(client.CLEARING_STRING)
    elif clearing == 2:
        os.system('cls' if os.name == 'nt' else 'clear')
    return result


def connect(cli, host, port):
    try:
        cli.run(host, port)
        auth_request = {}
        if cli.auth_mode:
            auth_request['username'] = console_input('Enter username: ', clearing=2)
            if cli.auth_mode == 'password':
                password_md5 = hashlib.md5(console_input('Enter password: ', clearing=2, is_hiding=True).encode()) \
                                      .hexdigest()
                auth_request['password'] = password_md5
        cli.auth(**auth_request)
        #os.system('cls' if os.name == 'nt' else 'clear')

    except ConnectionError as e:
        print(f'Error: {e}')
        exit()


def rum_messanger(cli):
    print(f'= {cli.username} =======\n\n')

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, cli.echo)

    while True:
        try:
            message = console_input('', clearing=1)
            cli.send(message)
        except ConnectionError as e:
            print(f'Error: {e}')
            exit()
        except KeyboardInterrupt:
            cli.close()
            exit()
        except Exception as e:
            print('some error')
            print(e)


def main():
    service = client.ManagerServiceClient
    proto = protocol.SocketProtocol(family=socket.AF_INET, type=socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 7070

    args = sys.argv[1:]
    if args:
        with open(service.HOSTS_DIR, 'rb') as file:
            server_meta = pickle.load(file, encoding='utf-8')
        for _, service_meta in server_meta.items():
            print(service_meta, args)
            if service_meta['service'] == args[0]:
                service = getattr(client, '{}Client'.format(service_meta['service']))
                proto_type = getattr(protocol, service_meta['protocol'])
                proto = proto_type(*service_meta['args'], **service_meta['kwargs'])
                host = service_meta['host']
                port = service_meta['port']
    cli = service(proto)
    connect(cli, host, port)

    if service is client.MessageServiceClient:
        rum_messanger(cli)


if __name__ == '__main__':
    main()

