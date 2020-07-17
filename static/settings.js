WS.addEventListener("message", function (evt) {
    var msg = JSON.parse(evt.data);
    var type = msg['type'];
    if (type == 'settings') {
        let newsettings = msg['message'];
        pp = 'playPause' in newsettings ? newsettings.playPause : null
        var ppbutton = document.getElementById('playPause');
        if (pp == 'play'){ ppbutton.checked = true;}
        if (pp == 'pause'){ ppbutton.checked = false;}

        if ('canForward' in newsettings) {
            if (newsettings.canForward === false) {
                document.getElementById('forwardbox').style.display = 'none'
            }
            if (newsettings.canForward === true) {
                document.getElementById('forwardbox').style.display = 'flex'
            }
        }
        if ('canBackward' in newsettings) {
            if (newsettings.canBackward === false) {
                document.getElementById('backbox').style.display = 'none'
            }
            if (newsettings.canBackward === true) {
                document.getElementById('backbox').style.display = 'flex'
            }
        }
    }
});

function openMenu(menudiv) {
    new Promise (
        function () {
            var settingsboxes = document.getElementsByClassName('settingscontain')
            for (var i =0; i< settingsboxes.length; i++){
                if (menudiv === settingsboxes[i]) {
                    settingsboxes[i].classList.remove('nodisplay')
                }
                else {
                    settingsboxes[i].classList.add('nodisplay')
                }
            }
        }
    )
}

function ToggleSettingsVisibility() {
    new Promise(
        function () {
            var settingsboxes = document.getElementsByClassName('settingscontain')
            let hidden = true;
            for (var i =0; i< settingsboxes.length; i++){
                hidden = settingsboxes[i].classList.contains('nodisplay') ? true : false;
                if (hidden === false) break;
            }
            if (hidden === false) {
                for (var i =0; i< settingsboxes.length; i++){
                    settingsboxes[i].classList.add('nodisplay');
                }
            }
            else{
                document.getElementById("topsettings").classList.remove('nodisplay');
            }
        }
    )
}

function skip(event, direction) {
    event.stopPropagation()
    new Promise(
        function () {
                WS.send(JSON.stringify(
                    {'settings': {'skip': direction}}
                ))
        }
    )
}

function PlayPause (checkbox) {
    event.stopPropagation()
    new Promise (
        function () {
            if (checkbox.checked == true) {
                document.getElementById("playpauseicon").src = STATICPATH + 'icons/2000px-Breathe-media-playback-pause.svg.png';
                WS.send(JSON.stringify(
                    {'settings': {'playPause': 'play'}}
                ))
            }
            else {
                document.getElementById("playpauseicon").src = STATICPATH + 'icons/2000px-Breathe-media-playback-start.svg.png';
                WS.send(JSON.stringify(
                    {'settings': {'playPause': 'pause'}}
                ))
            }
        }
    )
}