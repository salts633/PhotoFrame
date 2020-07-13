WS.addEventListener("message", function (evt) {
    var msg = JSON.parse(evt.data)
    var type = msg['type']
    if (type == 'photo') {
        document.getElementById('photo').src='/' + PHOTOS_PATH + '/' + msg['message'];
    }
});