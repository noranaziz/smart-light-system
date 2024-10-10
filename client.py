import asyncio
from aiocoap import *

ip = '10.25.3.27' # ip of the Raspberry Pi

async def main(req, inp):
    protocol = await Context.create_client_context()

    if req == '1':
        request = Message(code=GET, uri='coap://' + ip + '/hello')
        print('Fetching hello resource...')
    elif req == '2':
        request = Message(code=GET, uri='coap://' + ip + '/remote')
        print('Fetching remote_get resource...')
    elif req == '3':
        request = Message(code=PUT, payload=inp.encode('utf-8'), uri='coap://' + ip + '/remote')
        print('Fetching remote_put resource...')
    elif req == '4':
        request = Message(code=GET, uri='coap://' + ip + '/power')
        print('Fetching power resource...')

    try:
        response = await protocol.request(request).response

    except Exception as e:
        print('Failed to fetch resource:')
        print(e)

    else:
        print('Response: %s\n%r\n'%(response.code, response.payload))

while True:
    print('1: GET hello world resource')
    print('2: GET remote resource')
    print('3: PUT remote resource')
    print('4: GET power resource')
    print('0: exit program')
    print('')
    choice = input("Enter your choice: ")
    if choice == '0':
        break
    elif choice in ['1', '2', '4']:
        asyncio.run(main(choice, 0))
    elif choice == '3':
        put = input("Enter your PUT: ")
        asyncio.run(main(choice, put))
    else:
        print("Invalid choice. Please enter 1, 2, 3, or 0.")