var ws = new WebSocket("ws://"+SERVER_ADDRESS+"/socket");

// ws.onopen = function() {
//     ws.send("Hello, world");
// };
ws.onmessage = function (evt) {
    var msg = JSON.parse(evt.data)
    if (msg['type'] == 'photo') {
        document.getElementById('photo').src='/' + PHOTOS_PATH + '/' + msg['message'];
    }
    // alert(evt.data);
};
