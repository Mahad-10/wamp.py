from wampproto import dealer, broker, messages

from wamp import types


class Realm:
    def __init__(self):
        super().__init__()
        self.dealer = dealer.Dealer()
        self.broker = broker.Broker()

        self.clients: dict[int, types.IAsyncBaseSession] = {}

    def attach_client(self, base: types.IAsyncBaseSession):
        self.clients[base.id] = base
        self.dealer.add_session(base.id)
        self.broker.add_session(base.id)

    def detach_client(self, base: types.IAsyncBaseSession):
        del self.clients[base.id]
        self.broker.remove_session(base.id)
        self.dealer.remove_session(base.id)

    def stop(self):
        """stop will disconnect all clients."""
        pass

    async def receive_message(self, session_id: int, msg: messages.Message):
        match msg.TYPE:
            case messages.Call.TYPE | messages.Yield.TYPE | messages.Register.TYPE | messages.UnRegister.TYPE:
                recipient = self.dealer.receive_message(session_id, msg)
                client = self.clients[recipient.recipient]
                await client.send_message(recipient.message)

            case messages.Publish.TYPE | messages.Subscribe.TYPE | messages.UnSubscribe.TYPE:
                recipients = self.broker.receive_message(session_id, msg)
                if recipients is None:
                    return

                for recipient in recipients:
                    client = self.clients[recipient.recipient]
                    await client.send_message(recipient.message)
            case messages.Goodbye.TYPE:
                self.dealer.remove_session(session_id)
                self.broker.remove_session(session_id)
                client = self.clients[session_id]
                await client.close()
                del self.clients[session_id]