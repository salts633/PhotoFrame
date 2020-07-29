function settingsHandler(newsettings) {
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
        REFRESH.updateGui(
            newsettings['photoUpdateInterval'],
            newsettings['photoIntervalMode'],
            'hmsrefreshnumber'
        )
    }
    if("photoAlbumList" in newsettings) {
        set_album_list(
            newsettings["photoAlbumList"],
            newsettings["photoCurrentAlbum"]
        )
    }
}

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
            COMM.sendMessage('settings', {'skip': direction})
        }
    )
}

function PlayPause (checkbox) {
    event.stopPropagation()
    new Promise (
        function () {
            if (checkbox.checked == true) {
                document.getElementById("playpauseicon").src = STATICPATH + 'icons/2000px-Breathe-media-playback-pause.svg.png';
                COMM.sendMessage('settings', {'playPause': 'play'})
            }
            else {
                document.getElementById("playpauseicon").src = STATICPATH + 'icons/2000px-Breathe-media-playback-start.svg.png';
                COMM.sendMessage('settings', {'playPause': 'pause'})
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
             COMM.sendMessage(
                'settings', {
                    'photoUpdateInterval': this.update_interval,
                    'photoIntervalMode': this.mode
                 }
             )
        }
        catch(err){
            console.log('error sending update for photoUpdateInterval:', err)
        }
    }
    updateGui(seconds, mode, number_input_name){
        this.update_interval = seconds
        this.setMode(mode, number_input_name)
        document.getElementById('hms'+mode).checked = true
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

    setModeGui(mode, number_input_name){
        this.setMode(mode, number_input_name)
        this.send_update()
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
    }
}

function set_album_list(album_list, current_album){
    var container = document.getElementById("albumselector");
    container.innerHTML = ""
    album_list.forEach(
        album => {
            container.appendChild(
                make_album_button(album, current_album)
            )
        }
    )
}
function make_album_button(album, current_album){
    var outerdiv = document.createElement("div")
    outerdiv.className = "albuttondiv buttondiv"
    var label = document.createElement("label")
    var input = document.createElement("input")
    input.className = "buttoninput"
    input.setAttribute("type", "checkbox")
    if(album.title == current_album){
        input.checked = true
    }
    else {
        input.checked = false
    }
    input.setAttribute(
        "onchange",
        "if(this.checked) enable_album('"
         +
            album.title
            .replace("'", "\\'")
            .replace('"', '\\"')
         + "')"
    )
    var span = document.createElement("span")
    span.className = "buttonspan"
    span.appendChild(document.createTextNode(album.title))
    label.appendChild(input)
    label.appendChild(span)
    outerdiv.appendChild(label)
    return outerdiv
}

function enable_album(album){
    console.log('ena', album)
    COMM.sendMessage(
        "settings", {"photoCurrentAlbum": album}
    )
}