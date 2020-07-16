WS.addEventListener("message", function (evt) {
    var msg = JSON.parse(evt.data);
    var type = msg['type'];
    if (type == 'settings') {
        let newsettings = msg['message'];
        pp = 'playPause' in newsettings ? newsettings.playPause : null
        var ppbutton = document.getElementById('playPause');
        if (pp == 'play'){ ppbutton.checked = true;}
        if (pp == 'pause'){ ppbutton.checked = false;}
    }
});


function ToggleSettingsVisibility() {
    new Promise(
        function () {
            var setingstyle = document.getElementById('settingscontain').style;
            if (setingstyle.visibility == "hidden") {
                setingstyle.visibility = "visible"
            }
            else {
                setingstyle.visibility = "hidden"
            }
        }
    )
}

function skip(direction) {
    new Promise(
        function () {
                WS.send(JSON.stringify(
                    {'settings': {'skip': direction}}
                ))
        }
    )
}

function PlayPause (checkbox) {
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