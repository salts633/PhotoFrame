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
        if ('photoUpdateInterval' in newsettings){
            let mode = newsettings['photoIntervalMode'];
            // socket always gives value in seconds so set update_interval directly
            REFRESH.update_interval = newsettings['photoUpdateInterval']
            document.getElementById('hms'+mode).checked = true
            REFRESH.setMode(mode, 'hmsrefreshnumber');
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

class RefreshManager{
    constructor(){
        this.update_interval = 5
        this.mode = 'seconds'
    }
    send_update(){
        try {
             console.log('sending photo update', this.update_interval)
             WS.send(
                JSON.stringify(
                    {'settings': {
                        'photoUpdateInterval': this.update_interval,
                        'photoIntervalMode': this.mode
                     }
                    }
                )
             )
        }
        catch(err){
            console.log('error sending update for photoUpdateInterval:', err)
        }
    }
    setVal(val) {
        if (this.mode == 'seconds'){
            var newval = val
        }
        else if (this.mode == 'minutes'){
            var newval = val * 60
        }
        else if (this.mode == 'hours'){
            var newval = val * 3600
        }
        if (newval != this.update_interval){
            this.update_interval = newval
            this.checkLims()
            this.send_update()
        }
    }

    checkLims(){
        if (this.mode == 'seconds'){
            var max = 120;
            var min = 5;
        }
        else if (this.mode == 'minutes'){
            var max = 90 * 60;
            var min = 60;
        }
        else if (this.mode == 'hours'){
            var max = 12 * 3600;
            var min = 3600;
        }
        if (this.update_interval < min){
            this.update_interval = min
        }
        if (this.update_interval > max){
            this.update_interval = max
        }
    }

    setMode(mode, number_input_name){
        var number_input = document.getElementById(number_input_name)
        this.mode = mode
        console.log('refresh setting mode', mode)
        if (this.mode == 'seconds'){
            number_input.step = 5
            number_input.min = 5
            number_input.max = 120
            this.checkLims()
            number_input.value = this.update_interval
        }
        else if (this.mode == 'minutes'){
            number_input.step = 1
            number_input.min = 1
            number_input.max = 90
            this.checkLims()
            number_input.value = this.update_interval/60.0
        }
        else if (this.mode == 'hours'){
            number_input.step = 0.5
            number_input.min = 1
            number_input.max = 12
            this.checkLims()
            number_input.value = this.update_interval/3600.0
        }
        this.send_update()
    }

}

REFRESH = new RefreshManager()