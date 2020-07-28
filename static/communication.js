class Communicator {
    constructor(server){
        this.WS = new WebSocket("ws://"+server+"/socket");
        this.message_callbacks = new Object();
        this.WS.addEventListener("message", this.get_message_handler(this));
    }

    get_message_handler(comms){
        return function (evt){
            var msg = JSON.parse(evt.data);
            var type = msg['type'];
            if (comms.message_callbacks[type] !== undefined) {
                comms.message_callbacks[type].forEach(
                    fn => {
                        fn(msg['message'])
                    }
                );
            }
        }
    }

    addOpenListener (fn) {
        this.WS.addEventListener("open", () => {fn(this.WS)})
    }

    addMessageCallback(message_type, fn) {
        if (this.message_callbacks[message_type] === undefined) {
            this.message_callbacks[message_type] = [];
        }
        this.message_callbacks[message_type].push(fn)
    }

    sendMessage(message_type, message){
        var newmsg = {};
        newmsg[message_type] = message
        this.WS.send(JSON.stringify(newmsg))
    }
}